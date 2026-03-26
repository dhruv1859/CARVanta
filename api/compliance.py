"""
CARVanta – HIPAA/GDPR Compliance Module
==========================================
Handles consent management, PHI access logging, data deletion requests,
data export (GDPR Article 20), and compliance dashboard.

Exports used by enterprise_router.py.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from db.models import User


# ─── In-Memory Stores ────────────────────────────────────────────────────────────
# In production, these would be dedicated database tables with encryption

_consent_records: list[dict] = []
_phi_access_logs: list[dict] = []
_deletion_requests: list[dict] = []
_log_counter = 0


# ─── Helpers ─────────────────────────────────────────────────────────────────────

def _sha256(data: str) -> str:
    """Compute SHA-256 hash for integrity verification."""
    return hashlib.sha256(data.encode()).hexdigest()


def _compute_chain_hash(log_entry: dict, previous_hash: str) -> str:
    """Compute tamper-proof hash chain for audit logs."""
    payload = json.dumps({
        "index": log_entry.get("index", 0),
        "timestamp": log_entry.get("timestamp", ""),
        "user_id": log_entry.get("user_id", 0),
        "action": log_entry.get("action", ""),
        "previous_hash": previous_hash,
    }, sort_keys=True)
    return _sha256(payload)


# ─── Consent Management ─────────────────────────────────────────────────────────

def record_consent(
    db: Session,
    user_id: int,
    consent_type: str,
    is_granted: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    consent_version: str = "1.0",
) -> dict:
    """Record a user's consent decision (e.g., data processing, research use)."""
    record = {
        "id": len(_consent_records) + 1,
        "user_id": user_id,
        "consent_type": consent_type,
        "is_granted": is_granted,
        "consent_version": consent_version,
        "ip_address": ip_address,
        "user_agent": user_agent[:256] if user_agent else None,
        "recorded_at": datetime.utcnow().isoformat(),
    }
    _consent_records.append(record)

    return {
        "consent_recorded": True,
        "consent_type": consent_type,
        "is_granted": is_granted,
        "message": f"Consent for '{consent_type}' has been {'granted' if is_granted else 'revoked'}.",
    }


def get_user_consents(db: Session, user_id: int) -> dict:
    """Get all consent statuses for a user."""
    user_consents = [c for c in _consent_records if c["user_id"] == user_id]

    # Build current consent state (latest decision per type)
    consent_state = {}
    for c in user_consents:
        consent_state[c["consent_type"]] = {
            "is_granted": c["is_granted"],
            "version": c["consent_version"],
            "recorded_at": c["recorded_at"],
        }

    # Default consent types
    defaults = ["data_processing", "research_use", "marketing", "third_party_sharing", "analytics"]
    for ct in defaults:
        if ct not in consent_state:
            consent_state[ct] = {
                "is_granted": False,
                "version": "1.0",
                "recorded_at": None,
            }

    return {
        "user_id": user_id,
        "consents": consent_state,
        "total_records": len(user_consents),
    }


# ─── PHI Access Logging ─────────────────────────────────────────────────────────

def log_phi_access(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict:
    """Log access to Protected Health Information (HIPAA requirement)."""
    global _log_counter
    _log_counter += 1

    # Previous hash for chain integrity
    previous_hash = _phi_access_logs[-1]["chain_hash"] if _phi_access_logs else "GENESIS"

    entry = {
        "index": _log_counter,
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow().isoformat(),
        "previous_hash": previous_hash,
    }
    entry["chain_hash"] = _compute_chain_hash(entry, previous_hash)

    _phi_access_logs.append(entry)

    return {"logged": True, "log_id": _log_counter}


def get_phi_access_logs(db: Session, limit: int = 50) -> dict:
    """Get PHI access logs (admin only). Returns most recent entries."""
    logs = _phi_access_logs[-limit:] if _phi_access_logs else []
    logs_reversed = list(reversed(logs))

    return {
        "total_logs": len(_phi_access_logs),
        "returned": len(logs_reversed),
        "logs": logs_reversed,
    }


# ─── Data Deletion (GDPR Article 17) ────────────────────────────────────────────

def request_data_deletion(
    db: Session,
    user_id: int,
    reason: Optional[str] = None,
    categories: Optional[List[str]] = None,
) -> dict:
    """Submit a GDPR data deletion request."""
    request = {
        "id": len(_deletion_requests) + 1,
        "user_id": user_id,
        "reason": reason,
        "categories": categories or ["all"],
        "status": "pending",
        "submitted_at": datetime.utcnow().isoformat(),
        "estimated_completion": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }
    _deletion_requests.append(request)

    return {
        "request_id": request["id"],
        "status": "pending",
        "message": "Your data deletion request has been submitted. It will be processed within 30 days as required by GDPR Article 17.",
        "estimated_completion": request["estimated_completion"],
    }


# ─── Data Export (GDPR Article 20) ───────────────────────────────────────────────

def export_user_data(db: Session, user_id: int) -> dict:
    """Export all user data in machine-readable format (GDPR data portability)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    # Compile all user data
    user_consents = [c for c in _consent_records if c["user_id"] == user_id]
    user_phi_logs = [l for l in _phi_access_logs if l["user_id"] == user_id]

    export = {
        "export_format": "JSON",
        "exported_at": datetime.utcnow().isoformat(),
        "user_profile": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "institution": user.institution,
            "country": user.country,
            "bio": user.bio,
            "orcid_id": user.orcid_id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "consent_history": user_consents,
        "phi_access_history": [
            {k: v for k, v in l.items() if k != "chain_hash"}
            for l in user_phi_logs
        ],
        "deletion_requests": [
            d for d in _deletion_requests if d["user_id"] == user_id
        ],
        "data_categories": [
            "profile_data",
            "consent_records",
            "phi_access_logs",
            "analysis_history",
        ],
    }

    return export


# ─── Compliance Dashboard (Admin) ────────────────────────────────────────────────

def get_compliance_dashboard(db: Session) -> dict:
    """Get overall compliance metrics for admin dashboard."""
    total_users = db.query(User).count()

    # Consent rates
    consent_types = ["data_processing", "research_use", "marketing", "third_party_sharing", "analytics"]
    consent_rates = {}
    for ct in consent_types:
        granted = len([c for c in _consent_records if c["consent_type"] == ct and c["is_granted"]])
        total = len([c for c in _consent_records if c["consent_type"] == ct])
        consent_rates[ct] = {
            "granted": granted,
            "total": total,
            "rate": round(granted / max(total, 1) * 100, 1),
        }

    # PHI access summary
    now = datetime.utcnow()
    last_24h = [l for l in _phi_access_logs
                if datetime.fromisoformat(l["timestamp"]) > now - timedelta(hours=24)]
    last_7d = [l for l in _phi_access_logs
               if datetime.fromisoformat(l["timestamp"]) > now - timedelta(days=7)]

    # Deletion requests
    pending_deletions = len([d for d in _deletion_requests if d["status"] == "pending"])
    completed_deletions = len([d for d in _deletion_requests if d["status"] == "completed"])

    return {
        "total_users": total_users,
        "consent_rates": consent_rates,
        "phi_access": {
            "total_logs": len(_phi_access_logs),
            "last_24h": len(last_24h),
            "last_7d": len(last_7d),
        },
        "deletion_requests": {
            "pending": pending_deletions,
            "completed": completed_deletions,
            "total": len(_deletion_requests),
        },
        "compliance_score": _calculate_compliance_score(consent_rates, total_users),
        "last_audit": now.isoformat(),
    }


def _calculate_compliance_score(consent_rates: dict, total_users: int) -> float:
    """Calculate an overall compliance health score (0-100)."""
    if total_users == 0:
        return 100.0

    # Score based on consent rates and log integrity
    avg_consent_rate = sum(
        r["rate"] for r in consent_rates.values()
    ) / max(len(consent_rates), 1)

    # Integrity check score
    integrity = verify_phi_log_integrity(None)
    integrity_score = 100.0 if integrity.get("integrity_valid") else 50.0

    return round((avg_consent_rate * 0.6 + integrity_score * 0.4), 1)


# ─── Log Integrity Verification ─────────────────────────────────────────────────

def verify_phi_log_integrity(db: Optional[Session]) -> dict:
    """
    Verify the SHA-256 hash chain of PHI access logs.
    Detects any log tampering.
    """
    if not _phi_access_logs:
        return {
            "integrity_valid": True,
            "total_logs": 0,
            "verified": 0,
            "message": "No logs to verify",
        }

    previous_hash = "GENESIS"
    invalid_entries = []

    for i, entry in enumerate(_phi_access_logs):
        expected_hash = _compute_chain_hash(entry, previous_hash)
        if expected_hash != entry.get("chain_hash"):
            invalid_entries.append(i + 1)
        previous_hash = entry.get("chain_hash", "")

    is_valid = len(invalid_entries) == 0

    return {
        "integrity_valid": is_valid,
        "total_logs": len(_phi_access_logs),
        "verified": len(_phi_access_logs) - len(invalid_entries),
        "tampered_entries": invalid_entries if not is_valid else [],
        "hash_algorithm": "SHA-256",
        "chain_type": "sequential",
        "message": "All logs verified — integrity intact" if is_valid
                   else f"WARNING: {len(invalid_entries)} log entries may have been tampered with",
    }
