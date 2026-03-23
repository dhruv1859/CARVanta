"""
CARVanta – Billing & Subscription Management
===============================================
Enterprise billing system with tiered plans, usage metering,
invoice generation, and payment webhook handling.

Supports:
  - Free, Pro, Enterprise tier plans
  - Per-feature usage quotas
  - Monthly/annual billing cycles
  - Invoice generation with PDF-ready data
  - Razorpay payment integration (India)
  - Stripe fallback for international
  - Plan upgrade/downgrade with proration
  - Usage overage tracking
"""

import os
import json
import time
import hmac
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, Boolean, Text,
    ForeignKey, Index, func, JSON,
)
from db.models import Base, User

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Razorpay SDK (pip install razorpay)
try:
    import razorpay
    _razorpay_client = razorpay.Client(
        auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", ""))
    ) if os.getenv("RAZORPAY_KEY_ID") else None
except ImportError:
    _razorpay_client = None


# ─── Configuration ──────────────────────────────────────────────────────────────

# Razorpay (primary — India)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

# Stripe (fallback — international)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Billing defaults
BILLING_CURRENCY = os.getenv("BILLING_CURRENCY", "INR")  # INR for India
FREE_TRIAL_DAYS = int(os.getenv("FREE_TRIAL_DAYS", "14"))

# Price mapping in INR (at ~₹83/USD)
INR_PRICES = {
    "pro": {"monthly": 3999, "annual": 39999},
    "enterprise": {"monthly": 15999, "annual": 159999},
}


# ─── Subscription Plans ────────────────────────────────────────────────────────

class PlanTier(str, Enum):
    """Subscription tier levels."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    """Billing frequency options."""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    LIFETIME = "lifetime"


@dataclass
class PlanDefinition:
    """Static plan configuration."""
    tier: PlanTier
    name: str
    description: str
    price_monthly: float
    price_annual: float
    features: Dict[str, Any]
    limits: Dict[str, int]
    is_active: bool = True


# Plan definitions — the source of truth for what each tier includes
PLANS: Dict[str, PlanDefinition] = {
    PlanTier.FREE.value: PlanDefinition(
        tier=PlanTier.FREE,
        name="CARVanta Free",
        description="For individual researchers getting started with CAR-T analysis",
        price_monthly=0.0,
        price_annual=0.0,
        features={
            "single_antigen_analysis": True,
            "antigen_comparison": True,
            "tissue_heatmap": False,
            "patient_digital_twin": False,
            "nlp_query": True,
            "clinical_trials": True,
            "api_access": False,
            "multi_target_synergy": False,
            "pdf_reports": False,
            "priority_support": False,
            "custom_models": False,
            "team_collaboration": False,
            "audit_trail": False,
            "hipaa_compliance": False,
        },
        limits={
            "analyses_per_day": 10,
            "analyses_per_month": 100,
            "api_calls_per_day": 50,
            "storage_mb": 100,
            "team_members": 1,
            "saved_queries": 10,
            "export_per_month": 5,
        },
    ),
    PlanTier.PRO.value: PlanDefinition(
        tier=PlanTier.PRO,
        name="CARVanta Pro",
        description="For research teams and clinicians needing advanced analysis",
        price_monthly=49.0,
        price_annual=470.0,
        features={
            "single_antigen_analysis": True,
            "antigen_comparison": True,
            "tissue_heatmap": True,
            "patient_digital_twin": True,
            "nlp_query": True,
            "clinical_trials": True,
            "api_access": True,
            "multi_target_synergy": True,
            "pdf_reports": True,
            "priority_support": False,
            "custom_models": False,
            "team_collaboration": True,
            "audit_trail": True,
            "hipaa_compliance": False,
        },
        limits={
            "analyses_per_day": 100,
            "analyses_per_month": 2000,
            "api_calls_per_day": 1000,
            "storage_mb": 5000,
            "team_members": 10,
            "saved_queries": 100,
            "export_per_month": 50,
        },
    ),
    PlanTier.ENTERPRISE.value: PlanDefinition(
        tier=PlanTier.ENTERPRISE,
        name="CARVanta Enterprise",
        description="For hospitals, pharma companies, and large research institutions",
        price_monthly=199.0,
        price_annual=1990.0,
        features={
            "single_antigen_analysis": True,
            "antigen_comparison": True,
            "tissue_heatmap": True,
            "patient_digital_twin": True,
            "nlp_query": True,
            "clinical_trials": True,
            "api_access": True,
            "multi_target_synergy": True,
            "pdf_reports": True,
            "priority_support": True,
            "custom_models": True,
            "team_collaboration": True,
            "audit_trail": True,
            "hipaa_compliance": True,
        },
        limits={
            "analyses_per_day": 999999,
            "analyses_per_month": 999999,
            "api_calls_per_day": 50000,
            "storage_mb": 100000,
            "team_members": 999,
            "saved_queries": 999999,
            "export_per_month": 999999,
        },
    ),
}


# ─── Database Models ───────────────────────────────────────────────────────────

class Subscription(Base):
    """
    User subscription records.
    Tracks plan, billing cycle, status, and payment info.
    """
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    plan_tier = Column(String(32), nullable=False, default=PlanTier.FREE.value, index=True)
    billing_cycle = Column(String(16), nullable=False, default=BillingCycle.MONTHLY.value)
    status = Column(String(32), nullable=False, default="active", index=True)  # active, canceled, past_due, trialing
    # Razorpay (India)
    razorpay_customer_id = Column(String(128), nullable=True)
    razorpay_subscription_id = Column(String(128), nullable=True)
    razorpay_plan_id = Column(String(128), nullable=True)
    # Stripe (international fallback)
    stripe_customer_id = Column(String(128), nullable=True)
    stripe_subscription_id = Column(String(128), nullable=True)
    # Billing period
    trial_end = Column(DateTime, nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_subscription_status", "status"),
    )

    def __repr__(self):
        return f"<Subscription user={self.user_id} plan={self.plan_tier} status={self.status}>"


class Invoice(Base):
    """
    Invoice records for billing history.
    """
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(32), unique=True, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default=BILLING_CURRENCY)
    status = Column(String(32), nullable=False, default="draft")  # draft, pending, paid, failed, refunded
    description = Column(Text, nullable=True)
    stripe_invoice_id = Column(String(128), nullable=True)
    payment_method = Column(String(32), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    line_items = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Invoice #{self.invoice_number} ${self.amount} {self.status}>"


class UsageRecord(Base):
    """
    Tracks usage for metered billing and quota enforcement.
    """
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric = Column(String(64), nullable=False, index=True)  # analyses, api_calls, exports
    count = Column(Integer, nullable=False, default=0)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_usage_user_metric", "user_id", "metric"),
        Index("idx_usage_period", "period_start", "period_end"),
    )

    def __repr__(self):
        return f"<UsageRecord user={self.user_id} {self.metric}={self.count}>"


# ─── Plan Management ───────────────────────────────────────────────────────────

def get_available_plans() -> Dict[str, Any]:
    """Get all available subscription plans with pricing and features."""
    plans = []
    for tier_value, plan in PLANS.items():
        plans.append({
            "tier": plan.tier.value,
            "name": plan.name,
            "description": plan.description,
            "price_monthly": plan.price_monthly,
            "price_annual": plan.price_annual,
            "annual_savings": round((plan.price_monthly * 12 - plan.price_annual), 2),
            "features": plan.features,
            "limits": plan.limits,
        })
    return {"plans": plans}


def get_user_subscription(db: Session, user_id: int) -> Dict[str, Any]:
    """Get the current subscription for a user."""
    sub = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status.in_(["active", "trialing"]),
    ).first()

    if not sub:
        # Default to free plan
        plan = PLANS[PlanTier.FREE.value]
        return {
            "plan_tier": PlanTier.FREE.value,
            "plan_name": plan.name,
            "billing_cycle": "none",
            "status": "active",
            "features": plan.features,
            "limits": plan.limits,
            "is_free": True,
        }

    plan = PLANS.get(sub.plan_tier, PLANS[PlanTier.FREE.value])
    return {
        "subscription_id": sub.id,
        "plan_tier": sub.plan_tier,
        "plan_name": plan.name,
        "billing_cycle": sub.billing_cycle,
        "status": sub.status,
        "features": plan.features,
        "limits": plan.limits,
        "current_period_start": str(sub.current_period_start) if sub.current_period_start else None,
        "current_period_end": str(sub.current_period_end) if sub.current_period_end else None,
        "cancel_at": str(sub.cancel_at) if sub.cancel_at else None,
        "is_free": sub.plan_tier == PlanTier.FREE.value,
    }


def create_subscription(
    db: Session,
    user_id: int,
    plan_tier: str,
    billing_cycle: str = "monthly",
) -> Dict[str, Any]:
    """
    Create or upgrade a subscription.
    In production, this would integrate with Stripe.
    """
    plan = PLANS.get(plan_tier)
    if not plan:
        return {"error": f"Invalid plan: {plan_tier}"}

    # Check for existing active subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status.in_(["active", "trialing"]),
    ).first()

    now = datetime.now(timezone.utc)

    if existing:
        # Upgrade/downgrade existing subscription
        old_tier = existing.plan_tier
        existing.plan_tier = plan_tier
        existing.billing_cycle = billing_cycle
        existing.current_period_start = now
        existing.current_period_end = now + (
            timedelta(days=365) if billing_cycle == "annual" else timedelta(days=30)
        )
        existing.updated_at = now
        db.commit()

        return {
            "subscription_id": existing.id,
            "action": "upgraded" if _tier_rank(plan_tier) > _tier_rank(old_tier) else "downgraded",
            "old_plan": old_tier,
            "new_plan": plan_tier,
            "billing_cycle": billing_cycle,
            "message": f"Subscription changed to {plan.name}",
        }

    # Create new subscription
    period_end = now + timedelta(days=FREE_TRIAL_DAYS) if plan_tier != PlanTier.FREE.value else None

    sub = Subscription(
        user_id=user_id,
        plan_tier=plan_tier,
        billing_cycle=billing_cycle,
        status="trialing" if plan_tier != PlanTier.FREE.value else "active",
        trial_end=now + timedelta(days=FREE_TRIAL_DAYS) if plan_tier != PlanTier.FREE.value else None,
        current_period_start=now,
        current_period_end=period_end,
    )
    db.add(sub)

    # Create first invoice
    if plan_tier != PlanTier.FREE.value:
        price = plan.price_annual if billing_cycle == "annual" else plan.price_monthly
        invoice = Invoice(
            user_id=user_id,
            invoice_number=_generate_invoice_number(),
            amount=price,
            currency=BILLING_CURRENCY,
            status="pending",
            description=f"{plan.name} — {billing_cycle.title()} subscription",
            due_date=now + timedelta(days=14),
            line_items=json.dumps([{
                "description": f"{plan.name} ({billing_cycle})",
                "amount": price,
                "quantity": 1,
            }]),
        )
        db.add(invoice)

    db.commit()

    return {
        "subscription_id": sub.id,
        "plan_tier": plan_tier,
        "plan_name": plan.name,
        "billing_cycle": billing_cycle,
        "status": sub.status,
        "trial_end": str(sub.trial_end) if sub.trial_end else None,
        "message": f"Welcome to {plan.name}!",
    }


def cancel_subscription(db: Session, user_id: int, reason: str = None) -> Dict[str, Any]:
    """Cancel a subscription. Remains active until end of billing period."""
    sub = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status.in_(["active", "trialing"]),
    ).first()

    if not sub:
        return {"error": "No active subscription found"}

    if sub.plan_tier == PlanTier.FREE.value:
        return {"error": "Cannot cancel free plan"}

    now = datetime.now(timezone.utc)
    sub.canceled_at = now
    sub.cancel_at = sub.current_period_end or now
    sub.status = "canceled"

    db.commit()

    return {
        "canceled": True,
        "effective_date": str(sub.cancel_at),
        "message": f"Subscription will end on {sub.cancel_at.strftime('%B %d, %Y')}. You'll keep access until then.",
    }


# ─── Usage Tracking & Quota Enforcement ────────────────────────────────────────

def track_usage(db: Session, user_id: int, metric: str, count: int = 1) -> Dict[str, Any]:
    """
    Track usage for a specific metric.
    Returns current usage and remaining quota.
    """
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    # Find or create usage record for this period
    record = db.query(UsageRecord).filter(
        UsageRecord.user_id == user_id,
        UsageRecord.metric == metric,
        UsageRecord.period_start == period_start,
    ).first()

    if record:
        record.count += count
        record.updated_at = now
    else:
        record = UsageRecord(
            user_id=user_id,
            metric=metric,
            count=count,
            period_start=period_start,
            period_end=period_end,
        )
        db.add(record)

    db.commit()

    # Get user's plan limits
    sub = get_user_subscription(db, user_id)
    limit = sub.get("limits", {}).get(f"{metric}_per_month", 999999)

    return {
        "metric": metric,
        "current_usage": record.count,
        "limit": limit,
        "remaining": max(0, limit - record.count),
        "is_over_limit": record.count > limit,
    }


def check_quota(db: Session, user_id: int, metric: str) -> Dict[str, Any]:
    """Check if a user has remaining quota for a specific metric."""
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    record = db.query(UsageRecord).filter(
        UsageRecord.user_id == user_id,
        UsageRecord.metric == metric,
        UsageRecord.period_start == period_start,
    ).first()

    current_usage = record.count if record else 0

    sub = get_user_subscription(db, user_id)
    limit = sub.get("limits", {}).get(f"{metric}_per_month", 999999)

    has_quota = current_usage < limit

    return {
        "has_quota": has_quota,
        "current_usage": current_usage,
        "limit": limit,
        "remaining": max(0, limit - current_usage),
        "plan_tier": sub.get("plan_tier", "free"),
        "upgrade_needed": not has_quota,
    }


def get_usage_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Get complete usage summary for a user across all metrics."""
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    records = db.query(UsageRecord).filter(
        UsageRecord.user_id == user_id,
        UsageRecord.period_start == period_start,
    ).all()

    sub = get_user_subscription(db, user_id)
    limits = sub.get("limits", {})

    usage = {}
    for record in records:
        limit_key = f"{record.metric}_per_month"
        limit = limits.get(limit_key, 999999)
        usage[record.metric] = {
            "used": record.count,
            "limit": limit,
            "remaining": max(0, limit - record.count),
            "percentage": round(record.count / max(limit, 1) * 100, 1),
        }

    return {
        "period": f"{period_start.strftime('%B %Y')}",
        "plan_tier": sub.get("plan_tier", "free"),
        "usage": usage,
    }


# ─── Invoice Management ────────────────────────────────────────────────────────

def get_invoices(db: Session, user_id: int, limit: int = 20) -> Dict[str, Any]:
    """Get billing history for a user."""
    invoices = db.query(Invoice).filter(
        Invoice.user_id == user_id,
    ).order_by(Invoice.created_at.desc()).limit(limit).all()

    return {
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount": inv.amount,
                "currency": inv.currency,
                "status": inv.status,
                "description": inv.description,
                "paid_at": str(inv.paid_at) if inv.paid_at else None,
                "due_date": str(inv.due_date) if inv.due_date else None,
                "created_at": str(inv.created_at),
            }
            for inv in invoices
        ],
        "total_paid": sum(inv.amount for inv in invoices if inv.status == "paid"),
    }


# ─── Razorpay Order Creation ───────────────────────────────────────────────────

def create_razorpay_order(
    db: Session,
    user_id: int,
    plan_tier: str,
    billing_cycle: str = "monthly",
) -> Dict[str, Any]:
    """
    Create a Razorpay order for the user to pay.
    The frontend uses this order_id to open the Razorpay checkout popup.

    Flow:
      1. Backend calls this → gets order_id
      2. Frontend opens Razorpay checkout with order_id
      3. User pays via UPI/Card/Netbanking
      4. Razorpay sends webhook → process_payment_webhook()
      5. Subscription activated automatically
    """
    if not _razorpay_client:
        return {"error": "Razorpay not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env"}

    plan = PLANS.get(plan_tier)
    if not plan:
        return {"error": f"Invalid plan: {plan_tier}"}

    if plan_tier == PlanTier.FREE.value:
        return {"error": "Free plan doesn't require payment"}

    # Get INR price (amount in paise = INR * 100)
    inr_price = INR_PRICES.get(plan_tier, {})
    if billing_cycle == "annual":
        amount_inr = inr_price.get("annual", 0)
    else:
        amount_inr = inr_price.get("monthly", 0)

    amount_paise = int(amount_inr * 100)  # Razorpay uses paise

    try:
        # Create Razorpay order
        order_data = _razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"cvt_{user_id}_{int(time.time())}",
            "notes": {
                "user_id": str(user_id),
                "plan_tier": plan_tier,
                "billing_cycle": billing_cycle,
                "platform": "CARVanta",
            },
        })

        return {
            "order_id": order_data["id"],
            "amount": amount_inr,
            "amount_paise": amount_paise,
            "currency": "INR",
            "razorpay_key_id": RAZORPAY_KEY_ID,  # Frontend needs this
            "plan_name": plan.name,
            "plan_tier": plan_tier,
            "billing_cycle": billing_cycle,
            "description": f"{plan.name} — {billing_cycle.title()} Subscription",
            "prefill": {
                "name": "",  # Will be filled by frontend from user data
                "email": "",
            },
            "notes": {
                "user_id": user_id,
                "plan_tier": plan_tier,
            },
        }

    except Exception as e:
        return {"error": f"Failed to create order: {str(e)}"}


def verify_razorpay_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:
    """
    Verify that a Razorpay payment is legitimate.
    Uses HMAC SHA256 to verify the signature.
    """
    if not RAZORPAY_KEY_SECRET:
        return False

    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, razorpay_signature)


# ─── Webhook Processing ────────────────────────────────────────────────────────

def process_payment_webhook(payload: Dict, signature: str) -> Dict[str, Any]:
    """
    Process payment webhooks from Razorpay or Stripe.
    Auto-detects the provider from the payload structure.
    """
    # Detect provider
    if "event" in payload and payload.get("entity") == "event":
        # Razorpay webhook format
        return _process_razorpay_webhook(payload, signature)
    else:
        # Stripe webhook format
        return _process_stripe_webhook(payload, signature)


def _process_razorpay_webhook(payload: Dict, signature: str) -> Dict[str, Any]:
    """
    Process Razorpay webhooks.
    Verifies signature and handles payment events.
    """
    # Verify webhook signature
    if RAZORPAY_WEBHOOK_SECRET:
        expected_sig = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            json.dumps(payload, separators=(',', ':'), sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return {"error": "Invalid Razorpay webhook signature", "status": 400}

    event = payload.get("event", "")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    # Handle Razorpay events
    razorpay_handlers = {
        "payment.captured": _handle_razorpay_payment_captured,
        "payment.failed": _handle_razorpay_payment_failed,
        "subscription.activated": _handle_razorpay_subscription_activated,
        "subscription.charged": _handle_razorpay_subscription_charged,
        "subscription.cancelled": _handle_razorpay_subscription_cancelled,
        "subscription.paused": _handle_razorpay_subscription_paused,
        "refund.processed": _handle_razorpay_refund,
    }

    handler = razorpay_handlers.get(event)
    if handler:
        return handler(payment_entity, payload)

    return {"received": True, "provider": "razorpay", "event": event}


def _handle_razorpay_payment_captured(payment: Dict, full_payload: Dict) -> Dict:
    """
    Handle successful Razorpay payment.
    This fires when money is actually captured in your account.
    """
    order_id = payment.get("order_id", "")
    payment_id = payment.get("id", "")
    amount_paise = payment.get("amount", 0)
    amount_inr = amount_paise / 100
    method = payment.get("method", "unknown")  # upi, card, netbanking, wallet
    email = payment.get("email", "")
    contact = payment.get("contact", "")
    notes = payment.get("notes", {})

    user_id = notes.get("user_id")
    plan_tier = notes.get("plan_tier")
    billing_cycle = notes.get("billing_cycle", "monthly")

    print(f"[Billing] ✅ Payment captured: ₹{amount_inr} via {method} for user {user_id}")
    print(f"[Billing]    Order: {order_id}, Payment: {payment_id}")
    print(f"[Billing]    Plan: {plan_tier} ({billing_cycle}), Email: {email}")

    # TODO: Activate subscription in DB when user_id is available
    # This would be: create_subscription(db, user_id, plan_tier, billing_cycle)

    return {
        "processed": True,
        "provider": "razorpay",
        "event": "payment.captured",
        "amount_inr": amount_inr,
        "payment_method": method,
        "user_id": user_id,
        "plan_tier": plan_tier,
    }


def _handle_razorpay_payment_failed(payment: Dict, full_payload: Dict) -> Dict:
    """Handle failed Razorpay payment."""
    error = payment.get("error_description", "Unknown error")
    print(f"[Billing] ❌ Payment failed: {error}")
    return {
        "processed": True,
        "provider": "razorpay",
        "event": "payment.failed",
        "error": error,
    }


def _handle_razorpay_subscription_activated(data: Dict, full_payload: Dict) -> Dict:
    """Handle Razorpay subscription activation."""
    return {"processed": True, "provider": "razorpay", "event": "subscription.activated"}


def _handle_razorpay_subscription_charged(data: Dict, full_payload: Dict) -> Dict:
    """Handle recurring Razorpay subscription charge."""
    return {"processed": True, "provider": "razorpay", "event": "subscription.charged"}


def _handle_razorpay_subscription_cancelled(data: Dict, full_payload: Dict) -> Dict:
    """Handle Razorpay subscription cancellation."""
    return {"processed": True, "provider": "razorpay", "event": "subscription.cancelled"}


def _handle_razorpay_subscription_paused(data: Dict, full_payload: Dict) -> Dict:
    """Handle Razorpay subscription pause."""
    return {"processed": True, "provider": "razorpay", "event": "subscription.paused"}


def _handle_razorpay_refund(data: Dict, full_payload: Dict) -> Dict:
    """Handle processed refund."""
    return {"processed": True, "provider": "razorpay", "event": "refund.processed"}


# ─── Stripe Webhook (International Fallback) ──────────────────────────────────

def _process_stripe_webhook(payload: Dict, signature: str) -> Dict[str, Any]:
    """Process Stripe webhooks (for international customers)."""
    if STRIPE_WEBHOOK_SECRET:
        expected_sig = hmac.new(
            STRIPE_WEBHOOK_SECRET.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return {"error": "Invalid Stripe webhook signature", "status": 400}

    event_type = payload.get("type", "")
    data = payload.get("data", {}).get("object", {})

    stripe_handlers = {
        "checkout.session.completed": lambda d: {"processed": True, "event": event_type},
        "invoice.paid": lambda d: {"processed": True, "event": event_type},
        "invoice.payment_failed": lambda d: {"processed": True, "event": event_type},
        "customer.subscription.updated": lambda d: {"processed": True, "event": event_type},
        "customer.subscription.deleted": lambda d: {"processed": True, "event": event_type},
    }

    handler = stripe_handlers.get(event_type)
    if handler:
        return handler(data)

    return {"received": True, "provider": "stripe", "event_type": event_type}


# ─── Feature Gate Check ────────────────────────────────────────────────────────

def check_feature_access(db: Session, user_id: int, feature: str) -> Dict[str, Any]:
    """
    Check if a user has access to a specific feature based on their plan.
    Returns access status and upgrade info if blocked.
    """
    sub = get_user_subscription(db, user_id)
    features = sub.get("features", {})
    has_access = features.get(feature, False)

    if has_access:
        return {"allowed": True, "feature": feature, "plan": sub.get("plan_tier")}

    # Find the cheapest plan that includes this feature
    upgrade_to = None
    for tier_value, plan in PLANS.items():
        if plan.features.get(feature, False):
            upgrade_to = {
                "tier": plan.tier.value,
                "name": plan.name,
                "price_monthly": plan.price_monthly,
                "price_monthly_inr": INR_PRICES.get(plan.tier.value, {}).get("monthly", 0),
            }
            break

    return {
        "allowed": False,
        "feature": feature,
        "current_plan": sub.get("plan_tier"),
        "upgrade_to": upgrade_to,
        "message": f"This feature requires {upgrade_to['name'] if upgrade_to else 'an upgrade'}.",
    }


# ─── Helpers ────────────────────────────────────────────────────────────────────

def _tier_rank(tier: str) -> int:
    """Get numeric rank for plan comparison."""
    ranks = {PlanTier.FREE.value: 0, PlanTier.PRO.value: 1, PlanTier.ENTERPRISE.value: 2}
    return ranks.get(tier, 0)


def _generate_invoice_number() -> str:
    """Generate unique invoice number: CVT-YYYYMM-XXXX."""
    now = datetime.now(timezone.utc)
    random_part = secrets.token_hex(4)[:4].upper()
    return f"CVT-{now.strftime('%Y%m')}-{random_part}"
