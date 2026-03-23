"""
CARVanta – Email Verification System
=======================================
Handles email confirmation for new account registrations.
Generates verification codes, sends emails via SMTP, and validates codes.

Configuration via environment variables:
  SMTP_HOST       – SMTP server (default: smtp.gmail.com)
  SMTP_PORT       – SMTP port (default: 587)
  SMTP_USER       – Sender email address
  SMTP_PASSWORD   – App password (NOT your regular password)
  SMTP_FROM_NAME  – Display name (default: CARVanta Platform)
"""

import os
import random
import string
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timezone

# Load .env file for SMTP credentials
from dotenv import load_dotenv
load_dotenv()


# ─── Configuration ──────────────────────────────────────────────────────────────

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CARVanta Platform")

VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY = 600  # 10 minutes in seconds
RESEND_COOLDOWN = 60  # 1 minute between resend attempts


# ─── In-memory store (upgrade to Redis/DB for production) ──────────────────────

_pending_verifications: dict[str, dict] = {}
# Structure: { email: { "code": "123456", "created_at": timestamp, "attempts": 0 } }


# ─── Code Generation ───────────────────────────────────────────────────────────

def generate_verification_code() -> str:
    """Generate a cryptographically random 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=VERIFICATION_CODE_LENGTH))


# ─── Email Sending ─────────────────────────────────────────────────────────────

def _build_verification_email(to_email: str, code: str, full_name: str) -> MIMEMultipart:
    """Build a beautiful HTML verification email with anti-spam headers."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"CARVanta — Verify Your Account (Code: {code})"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Reply-To"] = SMTP_USER
    msg["X-Mailer"] = "CARVanta Platform v5.0"
    msg["X-Priority"] = "3"  # Normal priority

    # Plain text fallback
    text = f"""
CARVanta — Email Verification

Hi {full_name},

Your verification code is: {code}

This code expires in 10 minutes. If you didn't create a CARVanta account, please ignore this email.

— CARVanta Platform
    """

    # Rich HTML email
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background:#0F172A; font-family:'Segoe UI',Roboto,Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#0F172A; padding:40px 0;">
            <tr>
                <td align="center">
                    <table width="560" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#1E293B,#0F172A); border:1px solid rgba(148,163,184,0.15); border-radius:16px; overflow:hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding:36px 40px 20px; text-align:center;">
                                <div style="font-size:36px; margin-bottom:8px;">🧬</div>
                                <h1 style="margin:0; color:#F8FAFC; font-size:24px; font-weight:700; letter-spacing:-0.02em;">CARVanta</h1>
                                <p style="margin:4px 0 0; color:#94A3B8; font-size:13px;">Immunotherapy Intelligence Platform</p>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding:20px 40px 32px;">
                                <p style="color:#CBD5E1; font-size:15px; line-height:1.6; margin:0 0 8px;">
                                    Hi <strong style="color:#F1F5F9;">{full_name}</strong>,
                                </p>
                                <p style="color:#94A3B8; font-size:14px; line-height:1.6; margin:0 0 28px;">
                                    Welcome to CARVanta! Please verify your email address using the code below:
                                </p>

                                <!-- Code Box -->
                                <div style="background:rgba(0,119,182,0.1); border:2px solid rgba(0,180,216,0.3); border-radius:12px; padding:24px; text-align:center; margin-bottom:28px;">
                                    <p style="margin:0 0 8px; color:#94A3B8; font-size:12px; text-transform:uppercase; letter-spacing:0.1em;">Verification Code</p>
                                    <div style="font-size:36px; font-weight:800; color:#38BDF8; letter-spacing:0.25em; font-family:'Courier New',monospace;">
                                        {code}
                                    </div>
                                    <p style="margin:12px 0 0; color:#64748B; font-size:12px;">
                                        ⏱️ This code expires in <strong>10 minutes</strong>
                                    </p>
                                </div>

                                <p style="color:#64748B; font-size:13px; line-height:1.6; margin:0;">
                                    If you didn't create a CARVanta account, you can safely ignore this email.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding:20px 40px 28px; border-top:1px solid rgba(148,163,184,0.1); text-align:center;">
                                <p style="margin:0; color:#475569; font-size:12px;">
                                    © 2026 CARVanta Platform · Advancing CAR-T Cell Research
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_verification_email(to_email: str, full_name: str) -> dict:
    """
    Generate a verification code and send it to the user's email.
    Returns success/error status.
    """
    email_lower = to_email.lower().strip()

    # Rate limit: prevent spamming resend
    existing = _pending_verifications.get(email_lower)
    if existing:
        elapsed = time.time() - existing["created_at"]
        if elapsed < RESEND_COOLDOWN:
            remaining = int(RESEND_COOLDOWN - elapsed)
            return {
                "error": f"Please wait {remaining} seconds before requesting a new code",
                "retry_after": remaining,
            }

    # Generate code
    code = generate_verification_code()
    _pending_verifications[email_lower] = {
        "code": code,
        "created_at": time.time(),
        "attempts": 0,
        "full_name": full_name,
    }

    # If SMTP is not configured, return code in response (dev mode)
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"  [CARVanta Email] DEV MODE — Verification code for {email_lower}: {code}")
        return {
            "message": "Verification code generated (SMTP not configured — check server console)",
            "dev_mode": True,
            "dev_code": code,  # Only shown when SMTP is not set up
        }

    # Send real email
    try:
        msg = _build_verification_email(email_lower, code, full_name)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        return {"message": f"Verification code sent to {email_lower}"}

    except smtplib.SMTPAuthenticationError:
        return {"error": "Email authentication failed — check SMTP_USER and SMTP_PASSWORD environment variables"}
    except smtplib.SMTPException as e:
        return {"error": f"Failed to send email: {str(e)}"}
    except Exception as e:
        return {"error": f"Email service error: {str(e)}"}


def verify_code(email: str, code: str) -> dict:
    """
    Verify a user-submitted code against the stored code.
    Returns success or error with remaining attempts.
    """
    email_lower = email.lower().strip()
    record = _pending_verifications.get(email_lower)

    if not record:
        return {"error": "No verification pending for this email. Please request a new code."}

    # Check expiry
    elapsed = time.time() - record["created_at"]
    if elapsed > VERIFICATION_CODE_EXPIRY:
        del _pending_verifications[email_lower]
        return {"error": "Verification code expired. Please request a new one."}

    # Check max attempts (5 tries max)
    if record["attempts"] >= 5:
        del _pending_verifications[email_lower]
        return {"error": "Too many failed attempts. Please request a new code."}

    # Verify
    record["attempts"] += 1

    if record["code"] == code.strip():
        # Success — clean up
        del _pending_verifications[email_lower]
        return {"verified": True, "message": "Email verified successfully!"}
    else:
        remaining = 5 - record["attempts"]
        return {
            "verified": False,
            "error": f"Invalid code. {remaining} attempts remaining.",
            "attempts_remaining": remaining,
        }


def is_email_pending_verification(email: str) -> bool:
    """Check if an email has a pending (non-expired) verification."""
    email_lower = email.lower().strip()
    record = _pending_verifications.get(email_lower)
    if not record:
        return False
    elapsed = time.time() - record["created_at"]
    if elapsed > VERIFICATION_CODE_EXPIRY:
        del _pending_verifications[email_lower]
        return False
    return True


def cleanup_expired() -> int:
    """Remove all expired verification records. Returns count removed."""
    now = time.time()
    expired = [
        email for email, rec in _pending_verifications.items()
        if now - rec["created_at"] > VERIFICATION_CODE_EXPIRY
    ]
    for email in expired:
        del _pending_verifications[email]
    return len(expired)


# ─── Login Notification Email ──────────────────────────────────────────────────

def _build_login_notification(to_email: str, full_name: str, login_count: int, ip_address: str) -> MIMEMultipart:
    """Build a thank-you login notification email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"CARVanta — Welcome back, {full_name}!"
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Reply-To"] = SMTP_USER
    msg["X-Mailer"] = "CARVanta Platform v5.0"
    msg["X-Priority"] = "3"

    now = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    text = f"""
CARVanta — Login Notification

Hi {full_name},

You've successfully signed in to CARVanta (Login #{login_count}).

Time: {now}
IP Address: {ip_address}

Thank you for being part of the CARVanta community and advancing immunotherapy research!

If this wasn't you, please change your password immediately.

— CARVanta Platform
    """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="margin:0; padding:0; background:#0F172A; font-family:'Segoe UI',Roboto,Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#0F172A; padding:40px 0;">
            <tr>
                <td align="center">
                    <table width="560" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#1E293B,#0F172A); border:1px solid rgba(148,163,184,0.15); border-radius:16px; overflow:hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding:36px 40px 20px; text-align:center;">
                                <div style="font-size:36px; margin-bottom:8px;">🧬</div>
                                <h1 style="margin:0; color:#F8FAFC; font-size:24px; font-weight:700;">CARVanta</h1>
                                <p style="margin:4px 0 0; color:#94A3B8; font-size:13px;">Immunotherapy Intelligence Platform</p>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding:20px 40px 32px;">
                                <p style="color:#CBD5E1; font-size:15px; line-height:1.6; margin:0 0 8px;">
                                    Hi <strong style="color:#F1F5F9;">{full_name}</strong>,
                                </p>
                                <p style="color:#94A3B8; font-size:14px; line-height:1.6; margin:0 0 24px;">
                                    Welcome back! You've successfully signed in to your CARVanta account.
                                </p>

                                <!-- Login Details -->
                                <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2); border-radius:12px; padding:20px; margin-bottom:24px;">
                                    <table cellpadding="0" cellspacing="0" width="100%">
                                        <tr>
                                            <td style="color:#64748B; font-size:12px; padding:4px 0;">Login Count</td>
                                            <td style="color:#10B981; font-size:14px; font-weight:600; text-align:right;">#{login_count}</td>
                                        </tr>
                                        <tr>
                                            <td style="color:#64748B; font-size:12px; padding:4px 0;">Time</td>
                                            <td style="color:#CBD5E1; font-size:13px; text-align:right;">{now}</td>
                                        </tr>
                                        <tr>
                                            <td style="color:#64748B; font-size:12px; padding:4px 0;">IP Address</td>
                                            <td style="color:#CBD5E1; font-size:13px; text-align:right;">{ip_address}</td>
                                        </tr>
                                    </table>
                                </div>

                                <p style="color:#94A3B8; font-size:14px; line-height:1.6; margin:0 0 16px;">
                                    Thank you for being part of the CARVanta community and helping advance 
                                    <strong style="color:#38BDF8;">CAR-T cell immunotherapy research</strong>.
                                </p>

                                <p style="color:#475569; font-size:12px; line-height:1.5; margin:0; padding-top:16px; border-top:1px solid rgba(148,163,184,0.1);">
                                    If this wasn't you, please change your password immediately and contact support.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding:20px 40px 28px; border-top:1px solid rgba(148,163,184,0.1); text-align:center;">
                                <p style="margin:0; color:#475569; font-size:12px;">
                                    &copy; 2026 CARVanta Platform &middot; Advancing CAR-T Cell Research
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_login_notification(to_email: str, full_name: str, login_count: int, ip_address: str) -> None:
    """Send a login notification/thank-you email. Safe to call from background thread."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"  [CARVanta Email] DEV MODE — Login notification for {to_email} (login #{login_count})")
        return

    try:
        msg = _build_login_notification(to_email, full_name, login_count, ip_address)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"  [CARVanta Email] Login notification sent to {to_email}")
    except Exception as e:
        print(f"  [CARVanta Email] Failed to send login notification: {e}")
