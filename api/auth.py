"""
CARVanta – JWT Authentication Handler
=======================================
Handles password hashing, JWT token creation/validation,
session management, and user CRUD operations.
"""

import hashlib
import hmac
import os
import json
import base64
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
import threading

from sqlalchemy.orm import Session

from db.models import User, UserSession, UserRole


# ─── Configuration ──────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET", "carvanta-stable-jwt-secret-2026-national-demo")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30
BCRYPT_ROUNDS = 12


# ─── Password Hashing (PBKDF2 — no extra deps needed) ──────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 with random salt."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return base64.b64encode(salt + key).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    decoded = base64.b64decode(stored_hash.encode())
    salt = decoded[:32]
    stored_key = decoded[32:]
    test_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(stored_key, test_key)


# ─── JWT Token Management ──────────────────────────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    s += "=" * padding
    return base64.urlsafe_b64decode(s.encode())


def create_jwt(payload: dict, secret: str = JWT_SECRET, expire_hours: int = ACCESS_TOKEN_EXPIRE_HOURS) -> str:
    """Create a JWT token with HMAC-SHA256 signing."""
    header = {"alg": "HS256", "typ": "JWT"}
    
    now = time.time()
    payload.update({
        "iat": int(now),
        "exp": int(now + expire_hours * 3600),
    })
    
    header_b64 = _b64url_encode(json.dumps(header).encode())
    payload_b64 = _b64url_encode(json.dumps(payload).encode())
    
    message = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_jwt(token: str, secret: str = JWT_SECRET) -> Optional[dict]:
    """Decode and verify a JWT token. Returns None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(secret.encode(), message, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64))
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
        
        return payload
    except Exception:
        return None


def hash_token(token: str) -> str:
    """Create a SHA-256 hash of a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ─── User CRUD Operations ──────────────────────────────────────────────────────

def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    full_name: str,
    role: str = UserRole.RESEARCHER.value,
    institution: str = None,
    country: str = None,
) -> dict:
    """Register a new user. Returns user dict or error."""
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return {"error": "Email already registered"}
    
    # Check if username already exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return {"error": "Username already taken"}
    
    # Validate role
    valid_roles = [r.value for r in UserRole]
    if role not in valid_roles:
        return {"error": f"Invalid role. Must be one of: {valid_roles}"}
    
    # Create user
    user = User(
        email=email.lower().strip(),
        username=username.strip(),
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        role=role,
        institution=institution,
        country=country,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": str(user.created_at),
    }


def authenticate_user(
    db: Session,
    email_or_username: str,
    password: str,
    device_info: str = None,
    ip_address: str = None,
) -> dict:
    """Authenticate a user and create a session. Returns tokens or error."""
    
    # Find user by email or username
    user = db.query(User).filter(
        (User.email == email_or_username.lower()) |
        (User.username == email_or_username)
    ).first()
    
    if not user:
        return {"error": "Invalid credentials"}
    
    if not user.is_active:
        return {"error": "Account is deactivated"}
    
    if not verify_password(password, user.password_hash):
        return {"error": "Invalid credentials"}
    
    # ── MANDATORY: Block unverified users ─────────────────────────────────
    if not user.is_verified:
        return {
            "error": "Email not verified",
            "requires_verification": True,
            "email": user.email,
            "message": "Please verify your email before logging in. Check your inbox for the verification code.",
        }
    
    # Create access token
    access_token = create_jwt({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "type": "access",
    })
    
    # Create refresh token
    refresh_token = create_jwt({
        "user_id": user.id,
        "type": "refresh",
    }, expire_hours=REFRESH_TOKEN_EXPIRE_DAYS * 24)
    
    # Record session
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(access_token),
        device_info=device_info,
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    )
    db.add(session)
    
    # Update login stats
    user.last_login = datetime.now(timezone.utc)
    user.login_count += 1
    
    db.commit()
    
    result = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "institution": user.institution,
            "total_analyses": user.total_analyses,
            "login_count": user.login_count,
        }
    }
    
    # ── Send login notification email (fire-and-forget in background) ────
    try:
        from api.email_verification import send_login_notification
        threading.Thread(
            target=send_login_notification,
            args=(user.email, user.full_name, user.login_count, ip_address or "unknown"),
            daemon=True,
        ).start()
    except Exception:
        pass  # Never let email failure block login
    
    return result


def get_current_user(db: Session, token: str) -> Optional[dict]:
    """Validate a JWT token and return the user. Returns None if invalid."""
    
    payload = decode_jwt(token)
    if not payload:
        return None
    
    if payload.get("type") != "access":
        return None
    
    user_id = payload.get("user_id")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        return None
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "avatar_url": user.avatar_url,
        "institution": user.institution,
        "country": user.country,
        "bio": user.bio,
        "orcid_id": user.orcid_id,
        "is_verified": user.is_verified,
        "total_analyses": user.total_analyses,
        "api_calls_today": user.api_calls_today,
        "created_at": str(user.created_at),
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """Exchange a refresh token for a new access token."""
    
    payload = decode_jwt(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return {"error": "Invalid refresh token"}
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        return {"error": "User not found"}
    
    # Create new access token
    access_token = create_jwt({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "type": "access",
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    }


def logout_user(db: Session, token: str) -> dict:
    """Invalidate a user's session."""
    
    token_h = hash_token(token)
    session = db.query(UserSession).filter(UserSession.token_hash == token_h).first()
    if session:
        session.is_active = False
        db.commit()
    
    return {"message": "Logged out successfully"}


def update_profile(
    db: Session,
    user_id: int,
    full_name: str = None,
    bio: str = None,
    institution: str = None,
    country: str = None,
    orcid_id: str = None,
) -> dict:
    """Update a user's profile."""
    
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
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "bio": user.bio,
        "institution": user.institution,
        "country": user.country,
        "orcid_id": user.orcid_id,
        "avatar_url": user.avatar_url,
    }


def get_all_users(db: Session, skip: int = 0, limit: int = 50) -> list:
    """Admin: Get all users with pagination."""
    
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "institution": u.institution,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "total_analyses": u.total_analyses,
            "login_count": u.login_count,
            "last_login": str(u.last_login) if u.last_login else None,
            "created_at": str(u.created_at),
        }
        for u in users
    ]


def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> dict:
    """Change a user's password."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}
    
    if not verify_password(old_password, user.password_hash):
        return {"error": "Current password is incorrect"}
    
    if len(new_password) < 8:
        return {"error": "Password must be at least 8 characters"}
    
    user.password_hash = hash_password(new_password)
    
    # Invalidate all existing sessions
    db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    
    return {"message": "Password changed successfully. Please log in again."}


def get_user_stats(db: Session) -> dict:
    """Get platform-wide user statistics."""
    
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active == True).count()
    
    role_counts = {}
    for role in UserRole:
        role_counts[role.value] = db.query(User).filter(User.role == role.value).count()
    
    return {
        "total_users": total,
        "active_users": active,
        "role_distribution": role_counts,
    }
