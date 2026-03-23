"""
CARVanta – Multi-Factor Authentication (MFA / TOTP)
=====================================================
Enterprise-grade TOTP-based 2FA implementation following RFC 6238.
Supports authenticator apps (Google Authenticator, Authy, 1Password, etc.)
and backup recovery codes for account recovery.

Security:
  - TOTP secrets encrypted before storage
  - 30-second time windows with ±1 window tolerance
  - One-time backup codes (12 codes, each usable once)
  - Rate limiting on verification attempts
  - Constant-time comparison to prevent timing attacks
"""

import hashlib
import hmac
import os
import struct
import time
import base64
import secrets
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func
from db.models import Base, User


# ─── Configuration ──────────────────────────────────────────────────────────────

MFA_ISSUER = "CARVanta"                    # Shown in authenticator app
MFA_ALGORITHM = "SHA1"                      # Standard for TOTP
MFA_DIGITS = 6                              # 6-digit codes
MFA_PERIOD = 30                             # 30 seconds per code
MFA_TOLERANCE = 1                           # Accept ±1 time window
MFA_BACKUP_CODE_COUNT = 12                  # Number of recovery codes
MFA_MAX_ATTEMPTS = 5                        # Max failed attempts before lockout
MFA_LOCKOUT_SECONDS = 300                   # 5-minute lockout
MFA_ENCRYPTION_KEY = os.getenv(
    "MFA_ENCRYPTION_KEY",
    hashlib.sha256(b"carvanta-mfa-dev-key").hexdigest()[:32]
)


# ─── MFA State Model ───────────────────────────────────────────────────────────

class MFAConfig(Base):
    """
    Stores MFA configuration for users.
    TOTP secrets are encrypted at rest.
    """
    __tablename__ = "mfa_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    totp_secret_encrypted = Column(String(512), nullable=False)
    backup_codes_encrypted = Column(Text, nullable=True)  # JSON array, each code is hashed
    is_enabled = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)  # Setup completed?
    failed_attempts = Column(Integer, nullable=False, default=0)
    last_failed_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    enabled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<MFAConfig user_id={self.user_id} enabled={self.is_enabled}>"


# ─── TOTP Core (RFC 6238) ──────────────────────────────────────────────────────

def _generate_totp_secret(length: int = 32) -> str:
    """Generate a random base32-encoded TOTP secret."""
    random_bytes = os.urandom(length)
    return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")


def _compute_hotp(secret_b32: str, counter: int) -> str:
    """
    Compute HMAC-based One-Time Password (HOTP) — RFC 4226.
    This is the core building block for TOTP.
    """
    # Decode base32 secret
    # Add padding if needed
    padded = secret_b32 + "=" * ((8 - len(secret_b32) % 8) % 8)
    secret_bytes = base64.b32decode(padded.upper())

    # Pack counter as 8-byte big-endian
    counter_bytes = struct.pack(">Q", counter)

    # HMAC-SHA1
    h = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()

    # Dynamic truncation
    offset = h[-1] & 0x0F
    truncated = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF

    # Generate N-digit code
    otp = truncated % (10 ** MFA_DIGITS)
    return str(otp).zfill(MFA_DIGITS)


def _compute_totp(secret_b32: str, timestamp: float = None) -> str:
    """Compute Time-based OTP at the given timestamp (or now)."""
    if timestamp is None:
        timestamp = time.time()
    counter = int(timestamp) // MFA_PERIOD
    return _compute_hotp(secret_b32, counter)


def _verify_totp(secret_b32: str, code: str, tolerance: int = MFA_TOLERANCE) -> bool:
    """
    Verify a TOTP code with time window tolerance.
    Uses constant-time comparison to prevent timing attacks.
    """
    now = time.time()

    for offset in range(-tolerance, tolerance + 1):
        timestamp = now + (offset * MFA_PERIOD)
        expected = _compute_totp(secret_b32, timestamp)
        if hmac.compare_digest(expected, code):
            return True

    return False


# ─── Encryption Helpers ─────────────────────────────────────────────────────────

def _encrypt_secret(plaintext: str) -> str:
    """
    Simple XOR-based encryption with the MFA encryption key.
    In production, use AES-256-GCM via cryptography library.
    """
    key = MFA_ENCRYPTION_KEY.encode()
    plaintext_bytes = plaintext.encode()

    encrypted = bytearray()
    for i, byte in enumerate(plaintext_bytes):
        encrypted.append(byte ^ key[i % len(key)])

    return base64.b64encode(bytes(encrypted)).decode()


def _decrypt_secret(ciphertext: str) -> str:
    """Decrypt an XOR-encrypted secret."""
    key = MFA_ENCRYPTION_KEY.encode()
    encrypted = base64.b64decode(ciphertext.encode())

    decrypted = bytearray()
    for i, byte in enumerate(encrypted):
        decrypted.append(byte ^ key[i % len(key)])

    return bytes(decrypted).decode()


# ─── Backup Code Generation ────────────────────────────────────────────────────

def _generate_backup_codes(count: int = MFA_BACKUP_CODE_COUNT) -> Tuple[List[str], List[str]]:
    """
    Generate backup recovery codes.
    Returns (plaintext_codes, hashed_codes).
    Plaintext codes are shown to user once; hashed codes are stored.
    """
    plaintext_codes = []
    hashed_codes = []

    for _ in range(count):
        # Format: XXXX-XXXX (8 chars, easy to type)
        code = f"{secrets.token_hex(4)[:4].upper()}-{secrets.token_hex(4)[:4].upper()}"
        plaintext_codes.append(code)
        hashed_codes.append(hashlib.sha256(code.encode()).hexdigest())

    return plaintext_codes, hashed_codes


def _verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, int]:
    """
    Verify a backup code against the stored hashes.
    Returns (is_valid, code_index) — the code at the index should be removed.
    """
    code_hash = hashlib.sha256(code.strip().upper().encode()).hexdigest()
    for i, stored_hash in enumerate(hashed_codes):
        if hmac.compare_digest(code_hash, stored_hash):
            return True, i
    return False, -1


# ─── QR Code URI Generation ────────────────────────────────────────────────────

def _generate_totp_uri(secret: str, email: str) -> str:
    """
    Generate otpauth:// URI for QR code scanning.
    Compatible with Google Authenticator, Authy, 1Password, etc.
    """
    import urllib.parse

    params = {
        "secret": secret,
        "issuer": MFA_ISSUER,
        "algorithm": MFA_ALGORITHM,
        "digits": str(MFA_DIGITS),
        "period": str(MFA_PERIOD),
    }

    label = urllib.parse.quote(f"{MFA_ISSUER}:{email}")
    query = urllib.parse.urlencode(params)

    return f"otpauth://totp/{label}?{query}"


def _generate_qr_data_url(uri: str) -> str:
    """
    Generate a simple QR code as a data URL using a basic QR renderer.
    Falls back to returning the URI if qrcode library is not installed.
    """
    try:
        import qrcode
        import io

        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{b64}"
    except ImportError:
        # Return URI for manual entry if qrcode not installed
        return ""


# ─── MFA Setup Flow ────────────────────────────────────────────────────────────

def initiate_mfa_setup(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Start MFA setup for a user.
    Generates a new TOTP secret and QR code.
    The user must verify with a code before MFA is activated.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    # Check if MFA is already enabled
    existing = db.query(MFAConfig).filter(MFAConfig.user_id == user_id).first()
    if existing and existing.is_enabled:
        return {"error": "MFA is already enabled. Disable it first to reconfigure."}

    # Generate new secret
    secret = _generate_totp_secret()
    encrypted_secret = _encrypt_secret(secret)

    # Create or update MFA config
    if existing:
        existing.totp_secret_encrypted = encrypted_secret
        existing.is_verified = False
        existing.is_enabled = False
        existing.failed_attempts = 0
    else:
        mfa_config = MFAConfig(
            user_id=user_id,
            totp_secret_encrypted=encrypted_secret,
            is_enabled=False,
            is_verified=False,
        )
        db.add(mfa_config)

    db.commit()

    # Generate QR code
    totp_uri = _generate_totp_uri(secret, user.email)
    qr_data_url = _generate_qr_data_url(totp_uri)

    return {
        "setup_initiated": True,
        "totp_uri": totp_uri,
        "qr_code": qr_data_url,
        "secret": secret,  # Shown for manual entry
        "message": "Scan the QR code with your authenticator app, then enter a code to verify.",
    }


def verify_mfa_setup(db: Session, user_id: int, code: str) -> Dict[str, Any]:
    """
    Verify the MFA setup by checking the first TOTP code.
    On success, generates backup codes and enables MFA.
    """
    mfa_config = db.query(MFAConfig).filter(MFAConfig.user_id == user_id).first()
    if not mfa_config:
        return {"error": "MFA setup not initiated"}

    if mfa_config.is_enabled:
        return {"error": "MFA is already enabled"}

    # Decrypt and verify
    secret = _decrypt_secret(mfa_config.totp_secret_encrypted)
    if not _verify_totp(secret, code.strip()):
        return {"error": "Invalid verification code. Please try again."}

    # Generate backup codes
    plaintext_codes, hashed_codes = _generate_backup_codes()
    mfa_config.backup_codes_encrypted = _encrypt_secret(json.dumps(hashed_codes))
    mfa_config.is_verified = True
    mfa_config.is_enabled = True
    mfa_config.enabled_at = datetime.now(timezone.utc)
    mfa_config.failed_attempts = 0

    # Update user record
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.mfa_enabled = True

    db.commit()

    return {
        "mfa_enabled": True,
        "backup_codes": plaintext_codes,
        "message": "MFA is now active! Save your backup codes securely — they won't be shown again.",
        "backup_code_count": len(plaintext_codes),
    }


# ─── MFA Verification (Login) ──────────────────────────────────────────────────

def verify_mfa_code(db: Session, user_id: int, code: str) -> Dict[str, Any]:
    """
    Verify a TOTP code during login.
    Includes rate limiting and lockout protection.
    """
    mfa_config = db.query(MFAConfig).filter(
        MFAConfig.user_id == user_id,
        MFAConfig.is_enabled == True,
    ).first()

    if not mfa_config:
        return {"error": "MFA is not enabled for this account"}

    # Check lockout
    if mfa_config.failed_attempts >= MFA_MAX_ATTEMPTS:
        if mfa_config.last_failed_at:
            lockout_until = mfa_config.last_failed_at.timestamp() + MFA_LOCKOUT_SECONDS
            if time.time() < lockout_until:
                remaining = int(lockout_until - time.time())
                return {
                    "error": f"Account locked due to too many failed attempts. Try again in {remaining} seconds.",
                    "locked": True,
                    "retry_after": remaining,
                }
            else:
                # Reset after lockout period
                mfa_config.failed_attempts = 0

    # Try TOTP verification first
    secret = _decrypt_secret(mfa_config.totp_secret_encrypted)
    clean_code = code.strip().replace("-", "").replace(" ", "")

    # Check if it's a 6-digit TOTP code
    if len(clean_code) == MFA_DIGITS and clean_code.isdigit():
        if _verify_totp(secret, clean_code):
            mfa_config.failed_attempts = 0
            mfa_config.last_verified_at = datetime.now(timezone.utc)
            db.commit()
            return {"verified": True, "method": "totp"}

    # Check backup codes (format: XXXX-XXXX)
    if mfa_config.backup_codes_encrypted:
        hashed_codes = json.loads(_decrypt_secret(mfa_config.backup_codes_encrypted))
        is_valid, code_index = _verify_backup_code(clean_code, hashed_codes)

        if is_valid:
            # Remove used backup code
            hashed_codes.pop(code_index)
            mfa_config.backup_codes_encrypted = _encrypt_secret(json.dumps(hashed_codes))
            mfa_config.failed_attempts = 0
            mfa_config.last_verified_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "verified": True,
                "method": "backup_code",
                "remaining_backup_codes": len(hashed_codes),
                "warning": f"Backup code used. {len(hashed_codes)} codes remaining." if len(hashed_codes) < 4 else None,
            }

    # Failed attempt
    mfa_config.failed_attempts += 1
    mfa_config.last_failed_at = datetime.now(timezone.utc)
    db.commit()

    remaining_attempts = MFA_MAX_ATTEMPTS - mfa_config.failed_attempts
    return {
        "error": "Invalid MFA code",
        "remaining_attempts": max(remaining_attempts, 0),
    }


# ─── MFA Management ────────────────────────────────────────────────────────────

def disable_mfa(db: Session, user_id: int, code: str) -> Dict[str, Any]:
    """
    Disable MFA for a user. Requires a valid TOTP code for security.
    """
    mfa_config = db.query(MFAConfig).filter(
        MFAConfig.user_id == user_id,
        MFAConfig.is_enabled == True,
    ).first()

    if not mfa_config:
        return {"error": "MFA is not enabled"}

    # Verify code before disabling
    secret = _decrypt_secret(mfa_config.totp_secret_encrypted)
    if not _verify_totp(secret, code.strip()):
        return {"error": "Invalid verification code. Cannot disable MFA."}

    mfa_config.is_enabled = False
    mfa_config.is_verified = False
    mfa_config.backup_codes_encrypted = None

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.mfa_enabled = False

    db.commit()

    return {
        "mfa_disabled": True,
        "message": "MFA has been disabled. Your account is now protected by password only.",
    }


def regenerate_backup_codes(db: Session, user_id: int, code: str) -> Dict[str, Any]:
    """
    Regenerate backup recovery codes. Requires a valid TOTP code.
    Invalidates all previous backup codes.
    """
    mfa_config = db.query(MFAConfig).filter(
        MFAConfig.user_id == user_id,
        MFAConfig.is_enabled == True,
    ).first()

    if not mfa_config:
        return {"error": "MFA is not enabled"}

    # Verify code
    secret = _decrypt_secret(mfa_config.totp_secret_encrypted)
    if not _verify_totp(secret, code.strip()):
        return {"error": "Invalid verification code"}

    # Generate new backup codes
    plaintext_codes, hashed_codes = _generate_backup_codes()
    mfa_config.backup_codes_encrypted = _encrypt_secret(json.dumps(hashed_codes))
    db.commit()

    return {
        "regenerated": True,
        "backup_codes": plaintext_codes,
        "message": "New backup codes generated. Previous codes are now invalid.",
    }


def get_mfa_status(db: Session, user_id: int) -> Dict[str, Any]:
    """Get MFA status for a user."""
    mfa_config = db.query(MFAConfig).filter(MFAConfig.user_id == user_id).first()

    if not mfa_config:
        return {
            "mfa_enabled": False,
            "setup_started": False,
            "backup_codes_remaining": 0,
        }

    backup_count = 0
    if mfa_config.backup_codes_encrypted and mfa_config.is_enabled:
        try:
            codes = json.loads(_decrypt_secret(mfa_config.backup_codes_encrypted))
            backup_count = len(codes)
        except Exception:
            pass

    return {
        "mfa_enabled": mfa_config.is_enabled,
        "setup_started": not mfa_config.is_enabled and mfa_config.totp_secret_encrypted is not None,
        "enabled_at": str(mfa_config.enabled_at) if mfa_config.enabled_at else None,
        "last_verified_at": str(mfa_config.last_verified_at) if mfa_config.last_verified_at else None,
        "backup_codes_remaining": backup_count,
        "is_locked": mfa_config.failed_attempts >= MFA_MAX_ATTEMPTS,
    }


# ─── MFA Requirement Check ─────────────────────────────────────────────────────

def is_mfa_required(db: Session, user_id: int) -> bool:
    """Check if a user has MFA enabled and requires 2FA verification."""
    mfa_config = db.query(MFAConfig).filter(
        MFAConfig.user_id == user_id,
        MFAConfig.is_enabled == True,
    ).first()
    return mfa_config is not None
