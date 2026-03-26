"""
CARVanta – MFA / TOTP Module
===============================
Implements Time-based One-Time Password (TOTP) multi-factor authentication.
Uses HMAC-based OTP (RFC 6238) with backup recovery codes.

Exports used by enterprise_router.py.
"""

import os
import time
import hmac
import struct
import hashlib
import secrets
import base64
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from db.models import User


# ─── Config ──────────────────────────────────────────────────────────────────────

MFA_ISSUER = os.getenv("MFA_ISSUER", "CARVanta")
TOTP_DIGITS = 6
TOTP_PERIOD = 30  # seconds
TOTP_WINDOW = 1   # allow ±1 period for clock drift
BACKUP_CODE_COUNT = 12

# In-memory backup codes store (keyed by user_id)
# In production, store encrypted in database
_backup_codes: dict[int, list[str]] = {}
_mfa_setup_secrets: dict[int, str] = {}  # temporary secrets during setup
_mfa_metadata: dict[int, dict] = {}  # enabled_at, last_verified_at etc.


# ─── TOTP Core Implementation ───────────────────────────────────────────────────

def _generate_secret(length: int = 20) -> str:
    """Generate a random base32-encoded secret key."""
    random_bytes = secrets.token_bytes(length)
    return base64.b32encode(random_bytes).decode("ascii").rstrip("=")


def _compute_totp(secret: str, time_step: Optional[int] = None) -> str:
    """Compute TOTP code for a given secret and time step."""
    if time_step is None:
        time_step = int(time.time()) // TOTP_PERIOD

    # Decode the base32 secret
    secret_padded = secret + "=" * (8 - len(secret) % 8) if len(secret) % 8 else secret
    try:
        key = base64.b32decode(secret_padded.upper())
    except Exception:
        key = secret.encode()

    # HMAC-SHA1
    msg = struct.pack(">Q", time_step)
    h = hmac.new(key, msg, hashlib.sha1).digest()

    # Dynamic truncation
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
    code = code % (10 ** TOTP_DIGITS)

    return str(code).zfill(TOTP_DIGITS)


def _verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code with a time window tolerance."""
    current_step = int(time.time()) // TOTP_PERIOD
    for offset in range(-TOTP_WINDOW, TOTP_WINDOW + 1):
        expected = _compute_totp(secret, current_step + offset)
        if hmac.compare_digest(expected, code):
            return True
    return False


def _generate_backup_codes(count: int = BACKUP_CODE_COUNT) -> List[str]:
    """Generate a set of one-time backup recovery codes."""
    codes = []
    for _ in range(count):
        part1 = secrets.token_hex(3).upper()
        part2 = secrets.token_hex(3).upper()
        codes.append(f"{part1}-{part2}")
    return codes


def _build_totp_uri(secret: str, email: str) -> str:
    """Build otpauth URI for QR code generation."""
    from urllib.parse import quote
    label = quote(f"{MFA_ISSUER}:{email}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(MFA_ISSUER)}&digits={TOTP_DIGITS}&period={TOTP_PERIOD}"


def _generate_qr_data_url(uri: str) -> str:
    """Generate a simple QR code placeholder data URL.
    In production, use qrcode library to generate actual QR images."""
    # Return a placeholder — the frontend can use the TOTP URI directly
    # with a JS QR library. For full QR support, install 'qrcode' package.
    try:
        import qrcode
        import io
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{b64}"
    except ImportError:
        # qrcode not installed — return URI for frontend QR generation
        return ""


# ─── Public API ──────────────────────────────────────────────────────────────────

def initiate_mfa_setup(db: Session, user_id: int) -> dict:
    """
    Start MFA setup: generate a TOTP secret and return QR code data.
    The user must verify with a code before MFA is activated.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    if user.mfa_enabled:
        return {"error": "MFA is already enabled on this account"}

    # Generate and temporarily store secret
    secret = _generate_secret()
    _mfa_setup_secrets[user_id] = secret

    # Build TOTP URI
    totp_uri = _build_totp_uri(secret, user.email)

    # Generate QR code
    qr_code = _generate_qr_data_url(totp_uri)

    return {
        "setup_initiated": True,
        "totp_uri": totp_uri,
        "qr_code": qr_code,
        "secret": secret,
        "message": "Scan the QR code with your authenticator app, then enter the 6-digit code to verify.",
    }


def verify_mfa_setup(db: Session, user_id: int, code: str) -> dict:
    """
    Verify the first TOTP code to activate MFA.
    Called after initiate_mfa_setup to confirm the user has set up their authenticator.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    # Get the temporary secret from setup
    secret = _mfa_setup_secrets.get(user_id)
    if not secret:
        return {"error": "No pending MFA setup found. Please initiate setup first."}

    # Verify the code
    if not _verify_totp(secret, code.strip()):
        return {"error": "Invalid code. Make sure your authenticator app is synced and try again."}

    # Activate MFA
    user.mfa_enabled = True
    user.mfa_secret = secret
    db.commit()

    # Clean up temporary secret
    del _mfa_setup_secrets[user_id]

    # Generate backup codes
    backup_codes = _generate_backup_codes()
    _backup_codes[user_id] = backup_codes.copy()

    # Store metadata
    _mfa_metadata[user_id] = {
        "enabled_at": datetime.utcnow().isoformat(),
        "last_verified_at": datetime.utcnow().isoformat(),
    }

    return {
        "mfa_enabled": True,
        "backup_codes": backup_codes,
        "message": "MFA has been successfully enabled! Save your backup codes securely.",
    }


def verify_mfa_code(db: Session, user_id: int, code: str) -> dict:
    """
    Verify a TOTP code during login or sensitive operations.
    Also accepts backup recovery codes.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    if not user.mfa_enabled or not user.mfa_secret:
        return {"error": "MFA is not enabled on this account"}

    code = code.strip()

    # Try TOTP verification
    if len(code) == TOTP_DIGITS and code.isdigit():
        if _verify_totp(user.mfa_secret, code):
            # Update last verified
            if user_id in _mfa_metadata:
                _mfa_metadata[user_id]["last_verified_at"] = datetime.utcnow().isoformat()
            return {"verified": True, "method": "totp"}

    # Try backup code
    user_codes = _backup_codes.get(user_id, [])
    if code.upper() in [c.upper() for c in user_codes]:
        user_codes = [c for c in user_codes if c.upper() != code.upper()]
        _backup_codes[user_id] = user_codes
        if user_id in _mfa_metadata:
            _mfa_metadata[user_id]["last_verified_at"] = datetime.utcnow().isoformat()
        return {
            "verified": True,
            "method": "backup_code",
            "backup_codes_remaining": len(user_codes),
        }

    return {"error": "Invalid MFA code"}


def disable_mfa(db: Session, user_id: int, code: str) -> dict:
    """Disable MFA (requires valid TOTP code for security)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    if not user.mfa_enabled or not user.mfa_secret:
        return {"error": "MFA is not currently enabled"}

    # Verify current code before disabling
    if not _verify_totp(user.mfa_secret, code.strip()):
        return {"error": "Invalid TOTP code. Enter your current authenticator code to disable MFA."}

    user.mfa_enabled = False
    user.mfa_secret = None
    db.commit()

    # Clean up
    _backup_codes.pop(user_id, None)
    _mfa_metadata.pop(user_id, None)

    return {"mfa_disabled": True, "message": "MFA has been disabled on your account."}


def regenerate_backup_codes(db: Session, user_id: int, code: str) -> dict:
    """Regenerate backup recovery codes (requires valid TOTP code)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    if not user.mfa_enabled or not user.mfa_secret:
        return {"error": "MFA is not enabled"}

    # Verify TOTP before regenerating
    if not _verify_totp(user.mfa_secret, code.strip()):
        return {"error": "Invalid TOTP code"}

    new_codes = _generate_backup_codes()
    _backup_codes[user_id] = new_codes.copy()

    return {
        "backup_codes": new_codes,
        "message": "New backup codes generated. Previous codes are now invalid.",
    }


def get_mfa_status(db: Session, user_id: int) -> dict:
    """Get MFA status for the current user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    metadata = _mfa_metadata.get(user_id, {})
    remaining = len(_backup_codes.get(user_id, []))

    return {
        "mfa_enabled": user.mfa_enabled,
        "setup_started": user_id in _mfa_setup_secrets,
        "enabled_at": metadata.get("enabled_at"),
        "last_verified_at": metadata.get("last_verified_at"),
        "backup_codes_remaining": remaining if user.mfa_enabled else 0,
        "is_locked": False,
    }


def is_mfa_required(db: Session, user_id: int) -> bool:
    """Check if MFA verification is required for this user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    return user.mfa_enabled
