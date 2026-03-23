"""
CARVanta – Auth API Router
============================
FastAPI router for authentication endpoints.
Handles register, login, logout, profile, token refresh, and email verification.
"""

from fastapi import APIRouter, Depends, Request, Header
from pydantic import BaseModel
from typing import Optional

from sqlalchemy.orm import Session
from db.connection import get_db
from db.models import User
from api.auth import (
    create_user, authenticate_user, get_current_user,
    refresh_access_token, logout_user, update_profile,
    get_all_users, change_password, get_user_stats,
)
from api.email_verification import (
    send_verification_email, verify_code, is_email_pending_verification,
)


router = APIRouter(prefix="/api/v5/auth", tags=["Authentication"])


# ─── Pydantic Models ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str
    role: str = "researcher"
    institution: Optional[str] = None
    country: Optional[str] = None


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    institution: Optional[str] = None
    country: Optional[str] = None
    orcid_id: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


class ResendVerificationRequest(BaseModel):
    email: str
    full_name: Optional[str] = "User"


# ─── Helper: Extract token from Authorization header ────────────────────────────

def _extract_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return authorization


# ─── Auth Endpoints ─────────────────────────────────────────────────────────────

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new CARVanta account and send verification email."""
    if len(req.password) < 8:
        return {"error": "Password must be at least 8 characters"}
    if len(req.username) < 3:
        return {"error": "Username must be at least 3 characters"}

    result = create_user(
        db=db,
        email=req.email,
        username=req.username,
        password=req.password,
        full_name=req.full_name,
        role=req.role,
        institution=req.institution,
        country=req.country,
    )

    if "error" in result:
        return result

    # Send verification email after successful registration
    email_result = send_verification_email(req.email, req.full_name)

    return {
        **result,
        "verification": email_result,
        "message": "Account created! Please check your email for a verification code.",
    }


@router.post("/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Log in with email/username and password."""
    device_info = request.headers.get("user-agent", "unknown")
    ip_address = request.client.host if request.client else "unknown"

    result = authenticate_user(
        db=db,
        email_or_username=req.email_or_username,
        password=req.password,
        device_info=device_info,
        ip_address=ip_address,
    )
    return result


@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Log out and invalidate the current session."""
    token = _extract_token(authorization)
    if not token:
        return {"error": "No token provided"}
    return logout_user(db, token)


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Get the current authenticated user's profile."""
    token = _extract_token(authorization)
    if not token:
        return {"error": "Not authenticated", "status": 401}

    user = get_current_user(db, token)
    if not user:
        return {"error": "Invalid or expired token", "status": 401}

    return user


@router.put("/profile")
def edit_profile(
    req: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Update the current user's profile."""
    token = _extract_token(authorization)
    if not token:
        return {"error": "Not authenticated"}

    user = get_current_user(db, token)
    if not user:
        return {"error": "Invalid or expired token"}

    return update_profile(
        db=db,
        user_id=user["id"],
        full_name=req.full_name,
        bio=req.bio,
        institution=req.institution,
        country=req.country,
        orcid_id=req.orcid_id,
    )


@router.post("/change-password")
def password_change(
    req: PasswordChangeRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Change the current user's password."""
    token = _extract_token(authorization)
    if not token:
        return {"error": "Not authenticated"}

    user = get_current_user(db, token)
    if not user:
        return {"error": "Invalid or expired token"}

    return change_password(db, user["id"], req.old_password, req.new_password)


@router.post("/refresh")
def token_refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    return refresh_access_token(db, req.refresh_token)






# ─── Admin Endpoints ───────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Admin: List all users."""
    token = _extract_token(authorization)
    if not token:
        return {"error": "Not authenticated"}

    user = get_current_user(db, token)
    if not user:
        return {"error": "Invalid or expired token"}

    if user["role"] != "admin":
        return {"error": "Admin access required"}

    return get_all_users(db, skip, limit)


@router.get("/stats")
def platform_stats(db: Session = Depends(get_db)):
    """Get platform-wide user statistics."""
    return get_user_stats(db)


# ── Email Verification Endpoints (MANDATORY — server-enforced) ─────────────────

@router.post("/verify-email")
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email with 6-digit code. Marks user as verified in the database."""
    result = verify_code(req.email, req.code)

    if result.get("verified"):
        # Mark user as verified in the DATABASE (server-side enforcement)
        user = db.query(User).filter(User.email == req.email.lower().strip()).first()
        if user:
            user.is_verified = True
            db.commit()
            return {
                "verified": True,
                "message": "Email verified successfully! You can now log in.",
            }
        return {"error": "User not found"}

    return result


@router.post("/resend-verification")
def resend_verification(req: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification code (rate-limited: 1 per minute)."""
    # Check if user exists
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user:
        return {"error": "No account found with this email"}

    if user.is_verified:
        return {"message": "Email is already verified. You can log in."}

    full_name = req.full_name or user.full_name or "User"
    return send_verification_email(req.email, full_name)
