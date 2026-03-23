"""
CARVanta – Multi-Tenant Architecture
=======================================
Organization-level data isolation, workspace management, and
team collaboration for enterprise customers.

Supports:
  - Organization (tenant) creation and management
  - Workspace/project isolation
  - Invite/join flow with email verification
  - Organization-level roles (owner, admin, member, viewer)
  - Tenant-scoped data queries
  - Organization settings and branding
  - Member activity tracking
  - Cross-org data sharing policies
"""

import os
import secrets
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey, Index, func, UniqueConstraint,
)
from db.models import Base, User


# ─── Configuration ──────────────────────────────────────────────────────────────

MAX_FREE_ORGS = 1                  # Free users can create 1 org
MAX_PRO_ORGS = 3                   # Pro users can create 3 orgs
MAX_ORG_NAME_LENGTH = 128
INVITE_EXPIRY_DAYS = 7


# ─── Enums ──────────────────────────────────────────────────────────────────────

class OrgRole(str, Enum):
    """Organization-level roles with hierarchical permissions."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InviteStatus(str, Enum):
    """Status of an organization invite."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ─── Database Models ───────────────────────────────────────────────────────────

class Organization(Base):
    """
    Top-level tenant entity. All data within an org is isolated
    from other organizations (tenant-scoped queries).
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(512), nullable=True)
    website = Column(String(256), nullable=True)

    # Owner
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Settings
    settings_json = Column(Text, nullable=True)  # JSON: branding, defaults, etc.
    is_active = Column(Boolean, nullable=False, default=True)
    plan_tier = Column(String(32), nullable=False, default="free")
    max_members = Column(Integer, nullable=False, default=5)

    # Contact
    billing_email = Column(String(256), nullable=True)
    admin_email = Column(String(256), nullable=True)
    country = Column(String(64), nullable=True)
    industry = Column(String(64), nullable=True)

    # Stats
    member_count = Column(Integer, nullable=False, default=1)
    total_analyses = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Organization {self.name} [{self.slug}]>"


class OrgMembership(Base):
    """
    Maps users to organizations with role-based permissions.
    A user can belong to multiple organizations.
    """
    __tablename__ = "org_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False, default=OrgRole.MEMBER.value)
    is_active = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, server_default=func.now())
    last_active_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_org"),
        Index("idx_membership_org", "organization_id"),
    )

    def __repr__(self):
        return f"<OrgMembership user={self.user_id} org={self.organization_id} role={self.role}>"


class OrgInvite(Base):
    """
    Email-based invitation to join an organization.
    """
    __tablename__ = "org_invites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_email = Column(String(256), nullable=False, index=True)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    role = Column(String(16), nullable=False, default=OrgRole.MEMBER.value)
    status = Column(String(16), nullable=False, default=InviteStatus.PENDING.value)
    invite_token = Column(String(128), unique=True, nullable=False)
    message = Column(Text, nullable=True)
    accepted_by = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<OrgInvite {self.invited_email} -> org={self.organization_id}>"


class OrgAuditLog(Base):
    """
    Organization-level audit trail for all administrative actions.
    """
    __tablename__ = "org_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(128), nullable=True)
    details = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_org_audit_action", "organization_id", "action"),
    )

    def __repr__(self):
        return f"<OrgAuditLog org={self.organization_id} action={self.action}>"


# ─── Organization CRUD ─────────────────────────────────────────────────────────

def create_organization(
    db: Session,
    owner_id: int,
    name: str,
    description: str = None,
    industry: str = None,
    country: str = None,
) -> Dict[str, Any]:
    """Create a new organization and set the creator as owner."""
    user = db.query(User).filter(User.id == owner_id).first()
    if not user:
        return {"error": "User not found"}

    # Check org limit
    owned_count = db.query(Organization).filter(
        Organization.owner_id == owner_id,
        Organization.is_active == True,
    ).count()

    if owned_count >= MAX_PRO_ORGS:
        return {"error": f"You've reached the maximum of {MAX_PRO_ORGS} organizations"}

    # Generate unique slug
    slug = _generate_slug(db, name)

    org = Organization(
        name=name.strip()[:MAX_ORG_NAME_LENGTH],
        slug=slug,
        description=description,
        owner_id=owner_id,
        billing_email=user.email,
        admin_email=user.email,
        industry=industry,
        country=country,
        settings_json=json.dumps({
            "branding": {"primary_color": "#6366f1", "logo": None},
            "defaults": {"default_role": OrgRole.MEMBER.value},
            "features": {"allow_external_sharing": False},
        }),
    )
    db.add(org)
    db.flush()

    # Add owner as member
    membership = OrgMembership(
        user_id=owner_id,
        organization_id=org.id,
        role=OrgRole.OWNER.value,
    )
    db.add(membership)

    # Audit log
    _log_org_action(db, org.id, owner_id, "org_created", details={"name": name})

    db.commit()

    return {
        "organization_id": org.id,
        "name": org.name,
        "slug": org.slug,
        "role": OrgRole.OWNER.value,
        "message": f"Organization '{name}' created successfully!",
    }


def get_organization(db: Session, org_id: int) -> Dict[str, Any]:
    """Get organization details."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "description": org.description,
        "logo_url": org.logo_url,
        "website": org.website,
        "owner_id": org.owner_id,
        "plan_tier": org.plan_tier,
        "member_count": org.member_count,
        "max_members": org.max_members,
        "total_analyses": org.total_analyses,
        "industry": org.industry,
        "country": org.country,
        "is_active": org.is_active,
        "created_at": str(org.created_at),
    }


def get_user_organizations(db: Session, user_id: int) -> Dict[str, Any]:
    """Get all organizations a user belongs to."""
    memberships = db.query(OrgMembership).filter(
        OrgMembership.user_id == user_id,
        OrgMembership.is_active == True,
    ).all()

    orgs = []
    for m in memberships:
        org = db.query(Organization).filter(Organization.id == m.organization_id).first()
        if org and org.is_active:
            orgs.append({
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "role": m.role,
                "member_count": org.member_count,
                "plan_tier": org.plan_tier,
                "joined_at": str(m.joined_at),
            })

    return {"organizations": orgs, "total": len(orgs)}


def update_organization(
    db: Session,
    org_id: int,
    user_id: int,
    name: str = None,
    description: str = None,
    logo_url: str = None,
    website: str = None,
    settings: Dict = None,
) -> Dict[str, Any]:
    """Update organization details. Requires admin+ role."""
    if not _has_permission(db, user_id, org_id, OrgRole.ADMIN):
        return {"error": "Admin access required"}

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    if name:
        org.name = name.strip()[:MAX_ORG_NAME_LENGTH]
    if description is not None:
        org.description = description
    if logo_url is not None:
        org.logo_url = logo_url
    if website is not None:
        org.website = website
    if settings:
        existing = json.loads(org.settings_json or "{}")
        existing.update(settings)
        org.settings_json = json.dumps(existing)

    _log_org_action(db, org_id, user_id, "org_updated")
    db.commit()

    return {"updated": True, "message": "Organization updated successfully"}


# ─── Invite Flow ────────────────────────────────────────────────────────────────

def invite_member(
    db: Session,
    org_id: int,
    invited_by_id: int,
    email: str,
    role: str = OrgRole.MEMBER.value,
    message: str = None,
) -> Dict[str, Any]:
    """Send an invitation to join the organization."""
    if not _has_permission(db, invited_by_id, org_id, OrgRole.ADMIN):
        return {"error": "Admin access required to invite members"}

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    # Check member limit
    if org.member_count >= org.max_members:
        return {"error": f"Organization has reached its member limit ({org.max_members})"}

    # Check for existing membership
    existing_user = db.query(User).filter(User.email == email.lower().strip()).first()
    if existing_user:
        existing_membership = db.query(OrgMembership).filter(
            OrgMembership.user_id == existing_user.id,
            OrgMembership.organization_id == org_id,
        ).first()
        if existing_membership and existing_membership.is_active:
            return {"error": "User is already a member of this organization"}

    # Check for existing pending invite
    existing_invite = db.query(OrgInvite).filter(
        OrgInvite.organization_id == org_id,
        OrgInvite.invited_email == email.lower().strip(),
        OrgInvite.status == InviteStatus.PENDING.value,
    ).first()

    if existing_invite:
        return {"error": "An invite has already been sent to this email"}

    # Validate role
    if role not in [r.value for r in OrgRole if r != OrgRole.OWNER]:
        return {"error": f"Invalid role: {role}"}

    invite = OrgInvite(
        organization_id=org_id,
        invited_email=email.lower().strip(),
        invited_by=invited_by_id,
        role=role,
        message=message,
        invite_token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(invite)

    _log_org_action(db, org_id, invited_by_id, "member_invited", details={
        "email": email, "role": role,
    })

    db.commit()

    return {
        "invite_id": invite.id,
        "invite_token": invite.invite_token,
        "email": email,
        "role": role,
        "expires_at": str(invite.expires_at),
        "message": f"Invitation sent to {email}",
    }


def accept_invite(db: Session, user_id: int, invite_token: str) -> Dict[str, Any]:
    """Accept an organization invitation."""
    invite = db.query(OrgInvite).filter(
        OrgInvite.invite_token == invite_token,
        OrgInvite.status == InviteStatus.PENDING.value,
    ).first()

    if not invite:
        return {"error": "Invalid or expired invitation"}

    if invite.expires_at < datetime.now(timezone.utc):
        invite.status = InviteStatus.EXPIRED.value
        db.commit()
        return {"error": "Invitation has expired"}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    # Verify email matches
    if user.email.lower() != invite.invited_email.lower():
        return {"error": "Invitation was sent to a different email address"}

    # Create membership
    membership = OrgMembership(
        user_id=user_id,
        organization_id=invite.organization_id,
        role=invite.role,
    )
    db.add(membership)

    # Update invite
    invite.status = InviteStatus.ACCEPTED.value
    invite.accepted_by = user_id

    # Update org member count
    org = db.query(Organization).filter(Organization.id == invite.organization_id).first()
    if org:
        org.member_count += 1

    _log_org_action(db, invite.organization_id, user_id, "member_joined", details={
        "role": invite.role,
    })

    db.commit()

    return {
        "accepted": True,
        "organization_id": invite.organization_id,
        "organization_name": org.name if org else "",
        "role": invite.role,
        "message": f"Welcome to {org.name if org else 'the organization'}!",
    }


# ─── Member Management ─────────────────────────────────────────────────────────

def get_org_members(db: Session, org_id: int, user_id: int) -> Dict[str, Any]:
    """Get all members of an organization."""
    if not _has_permission(db, user_id, org_id, OrgRole.VIEWER):
        return {"error": "You don't have access to this organization"}

    memberships = db.query(OrgMembership).filter(
        OrgMembership.organization_id == org_id,
        OrgMembership.is_active == True,
    ).all()

    members = []
    for m in memberships:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            members.append({
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": m.role,
                "avatar_url": user.avatar_url,
                "joined_at": str(m.joined_at),
                "last_active_at": str(m.last_active_at) if m.last_active_at else None,
            })

    # Get pending invites
    pending = db.query(OrgInvite).filter(
        OrgInvite.organization_id == org_id,
        OrgInvite.status == InviteStatus.PENDING.value,
    ).all()

    return {
        "members": members,
        "total_members": len(members),
        "pending_invites": [
            {
                "email": inv.invited_email,
                "role": inv.role,
                "expires_at": str(inv.expires_at),
            }
            for inv in pending
        ],
    }


def update_member_role(
    db: Session,
    org_id: int,
    admin_id: int,
    target_user_id: int,
    new_role: str,
) -> Dict[str, Any]:
    """Change a member's role. Requires admin+ access."""
    if not _has_permission(db, admin_id, org_id, OrgRole.ADMIN):
        return {"error": "Admin access required"}

    if target_user_id == admin_id:
        return {"error": "You cannot change your own role"}

    membership = db.query(OrgMembership).filter(
        OrgMembership.user_id == target_user_id,
        OrgMembership.organization_id == org_id,
    ).first()

    if not membership:
        return {"error": "Member not found"}

    if membership.role == OrgRole.OWNER.value:
        return {"error": "Cannot change owner's role"}

    old_role = membership.role
    membership.role = new_role

    _log_org_action(db, org_id, admin_id, "role_changed", details={
        "user_id": target_user_id, "old_role": old_role, "new_role": new_role,
    })

    db.commit()

    return {"updated": True, "old_role": old_role, "new_role": new_role}


def remove_member(
    db: Session,
    org_id: int,
    admin_id: int,
    target_user_id: int,
) -> Dict[str, Any]:
    """Remove a member from an organization."""
    if not _has_permission(db, admin_id, org_id, OrgRole.ADMIN):
        return {"error": "Admin access required"}

    membership = db.query(OrgMembership).filter(
        OrgMembership.user_id == target_user_id,
        OrgMembership.organization_id == org_id,
    ).first()

    if not membership:
        return {"error": "Member not found"}

    if membership.role == OrgRole.OWNER.value:
        return {"error": "Cannot remove the organization owner"}

    membership.is_active = False

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org:
        org.member_count = max(0, org.member_count - 1)

    _log_org_action(db, org_id, admin_id, "member_removed", details={
        "user_id": target_user_id,
    })

    db.commit()

    return {"removed": True, "message": "Member removed from organization"}


# ─── Permission Checks ─────────────────────────────────────────────────────────

ROLE_HIERARCHY = {
    OrgRole.VIEWER.value: 0,
    OrgRole.MEMBER.value: 1,
    OrgRole.ADMIN.value: 2,
    OrgRole.OWNER.value: 3,
}


def _has_permission(db: Session, user_id: int, org_id: int, required_role: OrgRole) -> bool:
    """Check if user has at least the required role in the organization."""
    membership = db.query(OrgMembership).filter(
        OrgMembership.user_id == user_id,
        OrgMembership.organization_id == org_id,
        OrgMembership.is_active == True,
    ).first()

    if not membership:
        return False

    user_level = ROLE_HIERARCHY.get(membership.role, 0)
    required_level = ROLE_HIERARCHY.get(required_role.value, 0)

    return user_level >= required_level


def get_user_org_role(db: Session, user_id: int, org_id: int) -> Optional[str]:
    """Get a user's role in an organization."""
    membership = db.query(OrgMembership).filter(
        OrgMembership.user_id == user_id,
        OrgMembership.organization_id == org_id,
        OrgMembership.is_active == True,
    ).first()
    return membership.role if membership else None


# ─── Tenant-Scoped Data ────────────────────────────────────────────────────────

def get_tenant_context(db: Session, user_id: int, org_slug: str = None) -> Dict[str, Any]:
    """
    Get tenant context for scoping data queries.
    Returns org info and user permissions for the active workspace.
    """
    if org_slug:
        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if not org:
            return {"error": "Organization not found"}

        role = get_user_org_role(db, user_id, org.id)
        if not role:
            return {"error": "You don't have access to this organization"}

        return {
            "organization_id": org.id,
            "organization_name": org.name,
            "slug": org.slug,
            "role": role,
            "permissions": _get_role_permissions(role),
            "plan_tier": org.plan_tier,
        }

    # Default: personal workspace
    return {
        "organization_id": None,
        "organization_name": "Personal Workspace",
        "slug": "personal",
        "role": OrgRole.OWNER.value,
        "permissions": _get_role_permissions(OrgRole.OWNER.value),
        "plan_tier": "free",
    }


def _get_role_permissions(role: str) -> Dict[str, bool]:
    """Get permissions for a role."""
    base_permissions = {
        "can_view": True,
        "can_create": role in [OrgRole.MEMBER.value, OrgRole.ADMIN.value, OrgRole.OWNER.value],
        "can_edit": role in [OrgRole.MEMBER.value, OrgRole.ADMIN.value, OrgRole.OWNER.value],
        "can_delete": role in [OrgRole.ADMIN.value, OrgRole.OWNER.value],
        "can_invite": role in [OrgRole.ADMIN.value, OrgRole.OWNER.value],
        "can_manage_members": role in [OrgRole.ADMIN.value, OrgRole.OWNER.value],
        "can_manage_settings": role in [OrgRole.ADMIN.value, OrgRole.OWNER.value],
        "can_manage_billing": role == OrgRole.OWNER.value,
        "can_delete_org": role == OrgRole.OWNER.value,
    }
    return base_permissions


# ─── Helpers ────────────────────────────────────────────────────────────────────

def _generate_slug(db: Session, name: str) -> str:
    """Generate a URL-safe slug from an org name."""
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    slug = slug.strip("-")[:48]

    candidate = slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == candidate).first():
        candidate = f"{slug}-{counter}"
        counter += 1

    return candidate


def _log_org_action(
    db: Session,
    org_id: int,
    user_id: int,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: Dict = None,
    ip_address: str = None,
) -> None:
    """Log an organizational action to the audit trail."""
    log = OrgAuditLog(
        organization_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(log)
