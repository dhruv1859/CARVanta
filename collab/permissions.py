"""
CARVanta Collab — Permissions & Access Control Engine
=======================================================
Fine-grained access control for collaborative research
projects, datasets, notebooks, and experiments.

Features:
- Role-based access control (RBAC) with 8 predefined roles
- Resource-level permission grants
- Team hierarchy with inheritance
- Invitation management and approval workflows
- Data sharing agreements (DSA) for cross-institutional collaboration
- Anonymization policies for sensitive research data
- API key management for programmatic access
- Access request and approval queue
"""

import logging
import hashlib
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.permissions")

# In-memory stores
_PERMISSIONS: Dict[str, Dict] = {}
_INVITATIONS: Dict[str, Dict] = {}
_API_KEYS: Dict[str, Dict] = {}
_DATA_SHARING_AGREEMENTS: Dict[str, Dict] = {}

# Role definitions
_ROLES = {
    "owner": {
        "description": "Full control — can manage all aspects including deletion and transfer",
        "level": 100,
        "permissions": ["create", "read", "update", "delete", "share", "manage_members",
                       "manage_settings", "manage_billing", "transfer_ownership", "export_data"],
    },
    "admin": {
        "description": "Administrative access — can manage members and settings",
        "level": 80,
        "permissions": ["create", "read", "update", "delete", "share", "manage_members",
                       "manage_settings", "export_data"],
    },
    "principal_investigator": {
        "description": "PI role — full research access, can approve experiments and publications",
        "level": 70,
        "permissions": ["create", "read", "update", "share", "approve_experiments",
                       "approve_publications", "manage_members", "export_data"],
    },
    "senior_researcher": {
        "description": "Senior researcher — can create and manage experiments, review submissions",
        "level": 60,
        "permissions": ["create", "read", "update", "share", "review_submissions", "export_data"],
    },
    "researcher": {
        "description": "Standard researcher — can create content and contribute to experiments",
        "level": 50,
        "permissions": ["create", "read", "update", "share"],
    },
    "collaborator": {
        "description": "External collaborator — read access with limited write to shared content",
        "level": 30,
        "permissions": ["read", "create_comments", "share_limited"],
    },
    "reviewer": {
        "description": "Peer reviewer — read access to submissions, can submit reviews",
        "level": 20,
        "permissions": ["read", "review_submissions"],
    },
    "viewer": {
        "description": "Read-only access — can view but not modify any content",
        "level": 10,
        "permissions": ["read"],
    },
}

# Resource types
_RESOURCE_TYPES = {
    "project": {"description": "Research project", "shareable": True},
    "experiment": {"description": "Experiment within a project", "shareable": True},
    "dataset": {"description": "Shared dataset", "shareable": True},
    "notebook": {"description": "Analysis notebook", "shareable": True},
    "protocol": {"description": "Research protocol", "shareable": True},
    "submission": {"description": "Peer review submission", "shareable": False},
}


async def list_roles() -> Dict[str, Any]:
    """List all available roles with permissions."""
    return {
        "total_roles": len(_ROLES),
        "roles": {
            name: {
                "description": role["description"],
                "level": role["level"],
                "permissions": role["permissions"],
                "n_permissions": len(role["permissions"]),
            }
            for name, role in _ROLES.items()
        },
    }


async def grant_permission(
    resource_type: str,
    resource_id: str,
    user_id: str,
    role: str = "researcher",
    granted_by: str = "owner",
    expires_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Grant a role-based permission on a resource."""
    if role not in _ROLES:
        return {"error": f"Unknown role: {role}", "available_roles": list(_ROLES.keys())}
    if resource_type not in _RESOURCE_TYPES:
        return {"error": f"Unknown resource type: {resource_type}", "available": list(_RESOURCE_TYPES.keys())}

    perm_id = f"PERM-{uuid.uuid4().hex[:8]}"
    permission = {
        "permission_id": perm_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "user_id": user_id,
        "role": role,
        "role_level": _ROLES[role]["level"],
        "permissions": _ROLES[role]["permissions"],
        "granted_by": granted_by,
        "granted_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at,
        "active": True,
    }

    _PERMISSIONS[perm_id] = permission
    return {"permission_id": perm_id, "status": "granted", "permission": permission}


async def check_access(
    resource_type: str,
    resource_id: str,
    user_id: str,
    action: str = "read",
) -> Dict[str, Any]:
    """Check if a user has permission to perform an action on a resource."""
    user_perms = [
        p for p in _PERMISSIONS.values()
        if p["resource_id"] == resource_id and p["user_id"] == user_id and p["active"]
    ]

    if not user_perms:
        return {
            "allowed": False,
            "reason": "No permissions found for this user on this resource",
            "resource": resource_id,
            "user": user_id,
            "action": action,
        }

    # Check highest role
    best_perm = max(user_perms, key=lambda p: p["role_level"])
    allowed = action in best_perm["permissions"]

    return {
        "allowed": allowed,
        "resource": resource_id,
        "user": user_id,
        "action": action,
        "role": best_perm["role"],
        "reason": f"Action '{action}' {'permitted' if allowed else 'denied'} for role '{best_perm['role']}'",
    }


async def create_invitation(
    project_id: str,
    email: str,
    role: str = "researcher",
    invited_by: str = "owner",
    message: str = "",
) -> Dict[str, Any]:
    """Create a project invitation."""
    invite_id = f"INV-{uuid.uuid4().hex[:8]}"
    token = hashlib.sha256(f"{invite_id}:{email}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:32]

    invitation = {
        "invitation_id": invite_id,
        "project_id": project_id,
        "email": email,
        "role": role,
        "invited_by": invited_by,
        "message": message,
        "token": token,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    }

    _INVITATIONS[invite_id] = invitation
    return {"invitation_id": invite_id, "token": token, "status": "sent", "invitation": invitation}


async def create_data_sharing_agreement(
    project_id: str,
    partner_institution: str,
    data_types: Optional[List[str]] = None,
    purpose: str = "",
    duration_months: int = 12,
    created_by: str = "pi_1",
    de_identified: bool = True,
) -> Dict[str, Any]:
    """Create a data sharing agreement for cross-institutional collaboration."""
    dsa_id = f"DSA-{uuid.uuid4().hex[:8]}"

    agreement = {
        "dsa_id": dsa_id,
        "project_id": project_id,
        "partner_institution": partner_institution,
        "data_types": data_types or ["clinical", "genomic"],
        "purpose": purpose or "Collaborative immunotherapy research",
        "duration_months": duration_months,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=duration_months * 30)).isoformat(),
        "created_by": created_by,
        "status": "draft",
        "de_identified": de_identified,
        "terms": {
            "data_use": "Research purposes only as defined in agreement",
            "publication_rights": "Both parties retain right to publish with acknowledgment",
            "data_retention": f"Data to be destroyed {duration_months} months after agreement end",
            "security_requirements": "AES-256 encryption at rest, TLS 1.3 in transit",
            "breach_notification": "72-hour notification requirement",
            "irb_approval": "Both institutions must maintain active IRB approval",
        },
        "signatures": [],
    }

    _DATA_SHARING_AGREEMENTS[dsa_id] = agreement
    return {"dsa_id": dsa_id, "status": "created", "agreement": agreement}


async def generate_api_key(
    user_id: str,
    project_id: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    expires_days: int = 90,
) -> Dict[str, Any]:
    """Generate an API key for programmatic access."""
    key_id = f"KEY-{uuid.uuid4().hex[:8]}"
    api_key = f"cvt_{hashlib.sha256(f'{key_id}:{user_id}:{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:40]}"

    key_record = {
        "key_id": key_id,
        "user_id": user_id,
        "project_id": project_id,
        "scopes": scopes or ["read"],
        "api_key_prefix": api_key[:8] + "...",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
        "active": True,
        "last_used": None,
        "usage_count": 0,
    }

    _API_KEYS[key_id] = key_record
    return {"key_id": key_id, "api_key": api_key, "expires_in_days": expires_days, "scopes": key_record["scopes"]}
