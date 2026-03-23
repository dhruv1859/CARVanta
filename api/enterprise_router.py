"""
CARVanta – Enterprise API Router
===================================
FastAPI router for all enterprise features:
OAuth2/SSO, MFA, billing, compliance, multi-tenant, and analytics.

Endpoints:
  /api/v5/enterprise/oauth/*        - OAuth2/SSO login flows
  /api/v5/enterprise/mfa/*          - MFA setup, verify, manage
  /api/v5/enterprise/billing/*      - Plans, subscriptions, invoices
  /api/v5/enterprise/compliance/*   - Consent, PHI logs, GDPR
  /api/v5/enterprise/org/*          - Organization/tenant management
  /api/v5/enterprise/analytics/*    - Usage analytics, health
"""

from fastapi import APIRouter, Depends, Request, Header, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from db.connection import get_db
from api.auth import get_current_user

# Enterprise modules
from api.oauth2_sso import (
    get_authorization_url, validate_oauth_state, exchange_code_for_tokens,
    fetch_user_info, process_oauth_callback, unlink_provider, get_user_connections,
)
from api.mfa_totp import (
    initiate_mfa_setup, verify_mfa_setup, verify_mfa_code,
    disable_mfa, regenerate_backup_codes, get_mfa_status, is_mfa_required,
)
from api.billing import (
    get_available_plans, get_user_subscription, create_subscription,
    cancel_subscription, track_usage, check_quota, get_usage_summary,
    get_invoices, check_feature_access, process_payment_webhook,
)
from api.compliance import (
    record_consent, get_user_consents, log_phi_access,
    get_phi_access_logs, request_data_deletion, export_user_data,
    get_compliance_dashboard, verify_phi_log_integrity,
)
from api.tenant import (
    create_organization, get_organization, get_user_organizations,
    update_organization, invite_member, accept_invite,
    get_org_members, update_member_role, remove_member, get_tenant_context,
)
from api.analytics import (
    get_api_analytics, get_feature_analytics, get_platform_health,
    get_user_engagement, export_analytics_report,
)


router = APIRouter(prefix="/api/v5/enterprise", tags=["Enterprise"])


# ─── Helper ─────────────────────────────────────────────────────────────────────

def _extract_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return authorization


def _get_authenticated_user(db: Session, authorization: Optional[str]):
    """Get authenticated user or return error dict."""
    token = _extract_token(authorization)
    if not token:
        return None
    return get_current_user(db, token)


# ─── Pydantic Models ────────────────────────────────────────────────────────────

class MFASetupVerifyRequest(BaseModel):
    code: str

class MFADisableRequest(BaseModel):
    code: str

class SubscriptionRequest(BaseModel):
    plan_tier: str
    billing_cycle: str = "monthly"

class ConsentRequest(BaseModel):
    consent_type: str
    is_granted: bool
    consent_version: str = "1.0"

class OrgCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None

class OrgUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None

class InviteRequest(BaseModel):
    email: str
    role: str = "member"
    message: Optional[str] = None

class RoleUpdateRequest(BaseModel):
    user_id: int
    role: str

class DeletionRequest(BaseModel):
    reason: Optional[str] = None
    categories: Optional[List[str]] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  OAUTH2 / SSO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/oauth/{provider}/authorize")
def oauth_authorize(provider: str, redirect_to: str = "/"):
    """Get OAuth2 authorization URL for a provider (google, github, orcid)."""
    result = get_authorization_url(provider, redirect_to)
    if not result:
        return {"error": f"Provider '{provider}' is not configured"}
    return result


@router.get("/oauth/{provider}/callback")
def oauth_callback(
    provider: str,
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    db: Session = Depends(get_db),
):
    """Handle OAuth2 callback after provider authorization."""
    if error:
        return {"error": f"OAuth error: {error}"}
    if not code or not state:
        return {"error": "Missing authorization code or state"}

    # Validate state token
    state_data = validate_oauth_state(state)
    if not state_data:
        return {"error": "Invalid or expired OAuth state"}

    # Exchange code for tokens
    tokens = exchange_code_for_tokens(provider, code, state_data)
    if not tokens:
        return {"error": "Failed to exchange authorization code"}

    # Fetch user info
    access_token = tokens.get("access_token", "")
    user_info = fetch_user_info(provider, access_token)
    if not user_info:
        return {"error": "Failed to fetch user info from provider"}

    # Process: link or create account
    return process_oauth_callback(db, provider, user_info, tokens)


@router.get("/oauth/connections")
def get_connections(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get user's linked OAuth connections."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_user_connections(db, user["id"])


@router.delete("/oauth/{provider}/unlink")
def unlink_oauth(
    provider: str,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Unlink an OAuth provider from user's account."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return unlink_provider(db, user["id"], provider)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MFA / TOTP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/mfa/setup")
def mfa_setup(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Initiate MFA setup — returns QR code and secret."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return initiate_mfa_setup(db, user["id"])


@router.post("/mfa/verify-setup")
def mfa_verify_setup(
    req: MFASetupVerifyRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Verify MFA setup with first TOTP code — activates MFA."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return verify_mfa_setup(db, user["id"], req.code)


@router.post("/mfa/verify")
def mfa_verify(
    req: MFASetupVerifyRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Verify MFA code during login or sensitive operations."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return verify_mfa_code(db, user["id"], req.code)


@router.post("/mfa/disable")
def mfa_disable(
    req: MFADisableRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Disable MFA (requires valid TOTP code for security)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return disable_mfa(db, user["id"], req.code)


@router.post("/mfa/regenerate-backup-codes")
def mfa_regenerate_codes(
    req: MFASetupVerifyRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Regenerate backup recovery codes (requires TOTP code)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return regenerate_backup_codes(db, user["id"], req.code)


@router.get("/mfa/status")
def mfa_get_status(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get MFA status for the current user."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_mfa_status(db, user["id"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BILLING & SUBSCRIPTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/billing/plans")
def billing_plans():
    """Get all available subscription plans."""
    return get_available_plans()


@router.get("/billing/subscription")
def billing_subscription(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get current user's subscription."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_user_subscription(db, user["id"])


@router.post("/billing/subscribe")
def billing_subscribe(
    req: SubscriptionRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Create or upgrade subscription."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return create_subscription(db, user["id"], req.plan_tier, req.billing_cycle)


@router.post("/billing/cancel")
def billing_cancel(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Cancel current subscription."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return cancel_subscription(db, user["id"])


@router.get("/billing/usage")
def billing_usage(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get usage summary for current billing period."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_usage_summary(db, user["id"])


@router.get("/billing/invoices")
def billing_invoices(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get billing history with all invoices."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_invoices(db, user["id"])


@router.get("/billing/feature-access/{feature}")
def billing_feature_check(
    feature: str,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Check if user has access to a specific feature."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return check_feature_access(db, user["id"], feature)


@router.post("/billing/webhook")
async def billing_webhook(request: Request):
    """Handle payment provider webhooks."""
    body = await request.json()
    signature = request.headers.get("stripe-signature", "")
    return process_payment_webhook(body, signature)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COMPLIANCE (HIPAA/GDPR)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/compliance/consent")
def compliance_record_consent(
    req: ConsentRequest,
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Record a user consent decision."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")
    return record_consent(db, user["id"], req.consent_type, req.is_granted, ip, ua, req.consent_version)


@router.get("/compliance/consents")
def compliance_get_consents(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get all consent statuses for the current user."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_user_consents(db, user["id"])


@router.get("/compliance/phi-logs")
def compliance_phi_logs(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    limit: int = Query(50),
):
    """Get PHI access logs (admin only)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    if user.get("role") != "admin":
        return {"error": "Admin access required"}
    return get_phi_access_logs(db, limit=limit)


@router.get("/compliance/integrity")
def compliance_integrity(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Verify PHI log integrity (admin only)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    if user.get("role") != "admin":
        return {"error": "Admin access required"}
    return verify_phi_log_integrity(db)


@router.post("/compliance/deletion-request")
def compliance_delete_data(
    req: DeletionRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Submit a GDPR data deletion request."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return request_data_deletion(db, user["id"], req.reason, req.categories)


@router.get("/compliance/export")
def compliance_export_data(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Export all user data (GDPR Article 20)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return export_user_data(db, user["id"])


@router.get("/compliance/dashboard")
def compliance_dashboard(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get compliance overview dashboard (admin only)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    if user.get("role") != "admin":
        return {"error": "Admin access required"}
    return get_compliance_dashboard(db)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MULTI-TENANT / ORGANIZATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/org/create")
def org_create(
    req: OrgCreateRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Create a new organization."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return create_organization(db, user["id"], req.name, req.description, req.industry, req.country)


@router.get("/org/{org_id}")
def org_get(
    org_id: int,
    db: Session = Depends(get_db),
):
    """Get organization details."""
    return get_organization(db, org_id)


@router.get("/org/mine")
def org_mine(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get all organizations the current user belongs to."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_user_organizations(db, user["id"])


@router.put("/org/{org_id}")
def org_update(
    org_id: int,
    req: OrgUpdateRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Update organization details (admin+)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return update_organization(db, org_id, user["id"], req.name, req.description, req.logo_url, req.website)


@router.post("/org/{org_id}/invite")
def org_invite(
    org_id: int,
    req: InviteRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Invite a member to the organization."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return invite_member(db, org_id, user["id"], req.email, req.role, req.message)


@router.post("/org/accept-invite/{token}")
def org_accept_invite(
    token: str,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Accept an organization invitation."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return accept_invite(db, user["id"], token)


@router.get("/org/{org_id}/members")
def org_members(
    org_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get organization members."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_org_members(db, org_id, user["id"])


@router.put("/org/{org_id}/role")
def org_update_role(
    org_id: int,
    req: RoleUpdateRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Change a member's role."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return update_member_role(db, org_id, user["id"], req.user_id, req.role)


@router.delete("/org/{org_id}/member/{user_id}")
def org_remove_member(
    org_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Remove a member from the organization."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return remove_member(db, org_id, user["id"], user_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANALYTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/analytics/api")
def analytics_api(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    days: int = Query(30),
):
    """Get API usage analytics."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    from datetime import timedelta
    start = datetime.utcnow() - timedelta(days=days)
    return get_api_analytics(db, user_id=user["id"], start_date=start)


@router.get("/analytics/features")
def analytics_features(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    days: int = Query(30),
):
    """Get feature usage analytics."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    from datetime import timedelta
    start = datetime.utcnow() - timedelta(days=days)
    return get_feature_analytics(db, start_date=start)


@router.get("/analytics/health")
def analytics_health(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get platform health metrics (admin only)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    if user.get("role") != "admin":
        return {"error": "Admin access required"}
    return get_platform_health(db)


@router.get("/analytics/engagement")
def analytics_engagement(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    days: int = Query(30),
):
    """Get user engagement metrics."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    return get_user_engagement(db, user_id=user["id"], days=days)


@router.get("/analytics/report")
def analytics_report(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Generate comprehensive analytics report (admin only)."""
    user = _get_authenticated_user(db, authorization)
    if not user:
        return {"error": "Not authenticated"}
    if user.get("role") != "admin":
        return {"error": "Admin access required"}
    return export_analytics_report(db)
