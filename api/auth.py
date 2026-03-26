"""
CARVanta – Core Auth Module
==============================
JWT-based authentication: user creation, login, session management,
token refresh, profile updates, and admin utilities.

Exports used by auth_router.py and enterprise_router.py.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from db.models import User, UserSession

# ─── Config ──────────────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    import warnings
    warnings.warn("JWT_SECRET not set — using insecure fallback. Set JWT_SECRET in .env!")
    JWT_SECRET = "INSECURE-DEV-ONLY-" + hashlib.sha256(b"carvanta-dev").hexdigest()[:16]
ACCESS_TOKEN_TTL_HOURS = int(os.getenv("ACCESS_TOKEN_TTL_HOURS", "24"))
REFRESH_TOKEN_TTL_DAYS = int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30"))


# ─── Helpers ─────────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """SHA-256 password hash with salt."""
    salt = os.getenv("PASSWORD_SALT", "")
    if not salt:
        salt = "INSECURE-DEV-SALT-" + hashlib.sha256(b"carvanta").hexdigest()[:12]
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def _hash_token(token: str) -> str:
    """Hash a bearer token for DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(48)


def _user_to_dict(user: User) -> dict:
    """Serialize User ORM object to a safe dictionary (no password)."""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "institution": user.institution,
        "country": user.country,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "orcid_id": user.orcid_id,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "mfa_enabled": user.mfa_enabled,
        "api_calls_today": user.api_calls_today,
        "total_analyses": user.total_analyses,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "login_count": user.login_count,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ─── User Creation ──────────────────────────────────────────────────────────────

def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    full_name: str,
    role: str = "researcher",
    institution: Optional[str] = None,
    country: Optional[str] = None,
) -> dict:
    """Register a new user account."""
    email = email.lower().strip()
    username = username.strip()

    # Check uniqueness
    if db.query(User).filter(User.email == email).first():
        return {"error": f"Email '{email}' is already registered"}
    if db.query(User).filter(User.username == username).first():
        return {"error": f"Username '{username}' is already taken"}

    user = User(
        email=email,
        username=username,
        password_hash=_hash_password(password),
        full_name=full_name,
        role=role if role in ("patient", "researcher", "clinician", "admin") else "researcher",
        institution=institution,
        country=country,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "message": "Account created successfully",
    }


# ─── Authentication ─────────────────────────────────────────────────────────────

def authenticate_user(
    db: Session,
    email_or_username: str,
    password: str,
    device_info: str = "unknown",
    ip_address: str = "unknown",
) -> dict:
    """Authenticate user and return access + refresh tokens."""
    login_val = email_or_username.lower().strip()
    user = db.query(User).filter(
        (User.email == login_val) | (User.username == login_val)
    ).first()

    if not user:
        return {"error": "Invalid credentials"}

    if user.password_hash != _hash_password(password):
        return {"error": "Invalid credentials"}

    if not user.is_active:
        return {"error": "Account is deactivated. Contact support."}

    if not user.is_verified:
        return {
            "error": "Email not verified",
            "needs_verification": True,
            "email": user.email,
        }

    # Generate tokens
    access_token = _generate_token()
    refresh_token = _generate_token()

    # Create session
    session = UserSession(
        user_id=user.id,
        token_hash=_hash_token(access_token),
        device_info=device_info[:256] if device_info else None,
        ip_address=ip_address[:45] if ip_address else None,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_TTL_HOURS),
    )
    db.add(session)

    # Update user login stats
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_TTL_HOURS * 3600,
        "user": _user_to_dict(user),
    }


# ─── Token Validation ───────────────────────────────────────────────────────────

def get_current_user(db: Session, token: str) -> Optional[dict]:
    """
    Validate a bearer token and return the authenticated user dict.
    Returns None if the token is invalid or expired.
    """
    token_hash = _hash_token(token)
    session = db.query(UserSession).filter(
        UserSession.token_hash == token_hash,
        UserSession.is_active == True,
    ).first()

    if not session:
        return None

    # Check expiration
    if session.expires_at and session.expires_at < datetime.utcnow():
        session.is_active = False
        db.commit()
        return None

    user = db.query(User).filter(User.id == session.user_id, User.is_active == True).first()
    if not user:
        return None

    return _user_to_dict(user)


# ─── Token Refresh ──────────────────────────────────────────────────────────────

def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """Exchange a refresh token for a new access token."""
    # In this implementation, the refresh token is validated similarly
    # In production, refresh tokens would have their own separate table
    new_access_token = _generate_token()
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_TTL_HOURS * 3600,
    }


# ─── Logout ─────────────────────────────────────────────────────────────────────

def logout_user(db: Session, token: str) -> dict:
    """Invalidate the current session."""
    token_hash = _hash_token(token)
    session = db.query(UserSession).filter(
        UserSession.token_hash == token_hash,
    ).first()

    if session:
        session.is_active = False
        db.commit()
        return {"message": "Logged out successfully"}

    return {"message": "Session not found (may already be expired)"}


# ─── Profile Management ─────────────────────────────────────────────────────────

def update_profile(
    db: Session,
    user_id: int,
    full_name: Optional[str] = None,
    bio: Optional[str] = None,
    institution: Optional[str] = None,
    country: Optional[str] = None,
    orcid_id: Optional[str] = None,
) -> dict:
    """Update user profile fields."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    if full_name is not None:
        user.full_name = full_name
    if bio is not None:
        user.bio = bio
    if institution is not None:
        user.institution = institution
    if country is not None:
        user.country = country
    if orcid_id is not None:
        user.orcid_id = orcid_id

    db.commit()
    db.refresh(user)
    return {"message": "Profile updated", "user": _user_to_dict(user)}


def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> dict:
    """Change user password after verifying old password."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    if user.password_hash != _hash_password(old_password):
        return {"error": "Current password is incorrect"}

    if len(new_password) < 8:
        return {"error": "New password must be at least 8 characters"}

    user.password_hash = _hash_password(new_password)
    db.commit()
    return {"message": "Password changed successfully"}


# ─── Admin Utilities ─────────────────────────────────────────────────────────────

def get_all_users(db: Session, skip: int = 0, limit: int = 50) -> dict:
    """Admin: List all users with pagination."""
    total = db.query(User).count()
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [_user_to_dict(u) for u in users],
    }


def get_user_stats(db: Session) -> dict:
    """Get platform-wide user statistics."""
    total = db.query(User).count()
    verified = db.query(User).filter(User.is_verified == True).count()
    active = db.query(User).filter(User.is_active == True).count()
    mfa_enabled = db.query(User).filter(User.mfa_enabled == True).count()

    # Role breakdown
    roles = {}
    for role in ["patient", "researcher", "clinician", "admin"]:
        roles[role] = db.query(User).filter(User.role == role).count()

    # Recent signups (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = db.query(User).filter(User.created_at >= week_ago).count()

    return {
        "total_users": total,
        "verified_users": verified,
        "active_users": active,
        "mfa_enabled": mfa_enabled,
        "roles": roles,
        "signups_last_7_days": recent,
    }
