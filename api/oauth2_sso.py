"""
CARVanta – OAuth2 / SSO Provider Integration
===============================================
Enterprise-grade social login with Google, GitHub, and ORCID.
Handles token exchange, callback flows, and account linking.

Architecture:
  - Provider-agnostic base class for easy extensibility
  - Secure state parameter + PKCE challenge for CSRF protection
  - Auto-create or link accounts on first/subsequent logins
  - Each provider stores its token in user_oauth_connections table
"""

import hashlib
import hmac
import os
import json
import base64
import time
import secrets
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func
from db.models import Base, User
from db.connection import get_db

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─── Configuration ──────────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/api/v5/auth/oauth/google/callback")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8001/api/v5/auth/oauth/github/callback")

ORCID_CLIENT_ID = os.getenv("ORCID_CLIENT_ID", "")
ORCID_CLIENT_SECRET = os.getenv("ORCID_CLIENT_SECRET", "")
ORCID_REDIRECT_URI = os.getenv("ORCID_REDIRECT_URI", "http://localhost:8001/api/v5/auth/oauth/orcid/callback")

# Frontend URL for redirect after auth
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# State token signing key
STATE_SECRET = os.getenv("OAUTH_STATE_SECRET", os.urandom(32).hex())


# ─── OAuth Connection Model ────────────────────────────────────────────────────

class OAuthConnection(Base):
    """
    Stores OAuth2 provider connections for linked accounts.
    One user can have multiple providers linked.
    """
    __tablename__ = "oauth_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(32), nullable=False, index=True)  # google, github, orcid
    provider_user_id = Column(String(255), nullable=False)
    provider_email = Column(String(255), nullable=True)
    provider_name = Column(String(255), nullable=True)
    provider_avatar = Column(String(512), nullable=True)
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    scopes = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False)
    linked_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<OAuthConnection {self.provider}:{self.provider_user_id}>"


# ─── PKCE (Proof Key for Code Exchange) ────────────────────────────────────────

def generate_pkce_pair() -> tuple:
    """
    Generate a PKCE code_verifier and code_challenge pair.
    Used to prevent authorization code interception attacks.
    """
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


# ─── State Token Management ────────────────────────────────────────────────────

# In-memory store for pending OAuth states (use Redis in production)
_pending_oauth_states: Dict[str, Dict[str, Any]] = {}


def generate_oauth_state(provider: str, redirect_to: str = "/", pkce_verifier: str = "") -> str:
    """
    Generate a signed state token for OAuth2 CSRF protection.
    Encodes provider, timestamp, nonce, and optional redirect URL.
    """
    nonce = secrets.token_urlsafe(24)
    state_data = {
        "provider": provider,
        "nonce": nonce,
        "redirect_to": redirect_to,
        "pkce_verifier": pkce_verifier,
        "created_at": time.time(),
    }

    # Create HMAC signature
    payload = json.dumps(state_data, sort_keys=True)
    signature = hmac.new(
        STATE_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()[:16]

    state_token = f"{nonce}_{signature}"
    _pending_oauth_states[state_token] = state_data

    return state_token


def validate_oauth_state(state_token: str) -> Optional[Dict[str, Any]]:
    """
    Validate and consume an OAuth state token.
    Returns the state data if valid, None otherwise.
    Tokens expire after 10 minutes and are single-use.
    """
    state_data = _pending_oauth_states.pop(state_token, None)
    if not state_data:
        return None

    # Check expiration (10 min)
    if time.time() - state_data["created_at"] > 600:
        return None

    return state_data


# ─── Provider Configurations ───────────────────────────────────────────────────

@dataclass
class OAuthProviderConfig:
    """Configuration for an OAuth2 provider."""
    name: str
    client_id: str
    client_secret: str
    redirect_uri: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: List[str] = field(default_factory=list)
    extra_params: Dict[str, str] = field(default_factory=dict)


PROVIDERS: Dict[str, OAuthProviderConfig] = {}


def _init_providers():
    """Initialize provider configurations from environment variables."""
    global PROVIDERS

    if GOOGLE_CLIENT_ID:
        PROVIDERS["google"] = OAuthProviderConfig(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            redirect_uri=GOOGLE_REDIRECT_URI,
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
            scopes=["openid", "email", "profile"],
            extra_params={"access_type": "offline", "prompt": "consent"},
        )

    if GITHUB_CLIENT_ID:
        PROVIDERS["github"] = OAuthProviderConfig(
            name="github",
            client_id=GITHUB_CLIENT_ID,
            client_secret=GITHUB_CLIENT_SECRET,
            redirect_uri=GITHUB_REDIRECT_URI,
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scopes=["user:email", "read:user"],
        )

    if ORCID_CLIENT_ID:
        PROVIDERS["orcid"] = OAuthProviderConfig(
            name="orcid",
            client_id=ORCID_CLIENT_ID,
            client_secret=ORCID_CLIENT_SECRET,
            redirect_uri=ORCID_REDIRECT_URI,
            authorize_url="https://orcid.org/oauth/authorize",
            token_url="https://orcid.org/oauth/token",
            userinfo_url="https://pub.orcid.org/v3.0/{orcid}/person",
            scopes=["/authenticate", "/read-limited"],
        )


_init_providers()


# ─── Authorization URL Generation ──────────────────────────────────────────────

def get_authorization_url(provider_name: str, redirect_to: str = "/") -> Optional[Dict[str, str]]:
    """
    Generate the OAuth2 authorization URL for a given provider.
    Returns dict with 'url' and 'state' keys, or None if provider not configured.
    """
    provider = PROVIDERS.get(provider_name)
    if not provider:
        return None

    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()

    # Generate state token
    state = generate_oauth_state(provider_name, redirect_to, code_verifier)

    # Build authorization URL
    params = {
        "client_id": provider.client_id,
        "redirect_uri": provider.redirect_uri,
        "response_type": "code",
        "scope": " ".join(provider.scopes),
        "state": state,
    }

    # PKCE for Google (GitHub doesn't support it)
    if provider_name == "google":
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"

    # Add provider-specific params
    params.update(provider.extra_params)

    url = f"{provider.authorize_url}?{urllib.parse.urlencode(params)}"

    return {
        "url": url,
        "state": state,
        "provider": provider_name,
    }


# ─── Token Exchange ────────────────────────────────────────────────────────────

def exchange_code_for_tokens(provider_name: str, code: str, state_data: Dict) -> Optional[Dict[str, Any]]:
    """
    Exchange an authorization code for access/refresh tokens.
    Uses urllib to avoid external HTTP dependencies.
    """
    import urllib.request

    provider = PROVIDERS.get(provider_name)
    if not provider:
        return None

    data = {
        "client_id": provider.client_id,
        "client_secret": provider.client_secret,
        "code": code,
        "redirect_uri": provider.redirect_uri,
        "grant_type": "authorization_code",
    }

    # Add PKCE verifier if available
    if state_data.get("pkce_verifier"):
        data["code_verifier"] = state_data["pkce_verifier"]

    encoded_data = urllib.parse.urlencode(data).encode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    try:
        req = urllib.request.Request(provider.token_url, data=encoded_data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result
    except Exception as e:
        print(f"  [OAuth2] Token exchange failed for {provider_name}: {e}")
        return None


# ─── User Info Fetching ─────────────────────────────────────────────────────────

def fetch_user_info(provider_name: str, access_token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user profile information from the OAuth2 provider.
    Returns normalized user data dict.
    """
    import urllib.request

    provider = PROVIDERS.get(provider_name)
    if not provider:
        return None

    userinfo_url = provider.userinfo_url
    headers = {"Authorization": f"Bearer {access_token}"}

    # GitHub needs separate email endpoint
    if provider_name == "github":
        headers["Accept"] = "application/vnd.github.v3+json"

    try:
        req = urllib.request.Request(userinfo_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_data = json.loads(response.read().decode())

        # Normalize response based on provider
        return _normalize_user_info(provider_name, raw_data, access_token)

    except Exception as e:
        print(f"  [OAuth2] Failed to fetch user info from {provider_name}: {e}")
        return None


def _normalize_user_info(provider_name: str, data: Dict, access_token: str) -> Dict[str, Any]:
    """Normalize provider-specific user data into a common format."""

    if provider_name == "google":
        return {
            "provider_user_id": data.get("sub", ""),
            "email": data.get("email", ""),
            "name": data.get("name", ""),
            "avatar": data.get("picture", ""),
            "email_verified": data.get("email_verified", False),
        }

    elif provider_name == "github":
        email = data.get("email", "")

        # GitHub may not return email in main response — fetch from emails endpoint
        if not email:
            email = _fetch_github_primary_email(access_token)

        return {
            "provider_user_id": str(data.get("id", "")),
            "email": email,
            "name": data.get("name", "") or data.get("login", ""),
            "avatar": data.get("avatar_url", ""),
            "email_verified": True,  # GitHub verifies emails
            "username": data.get("login", ""),
        }

    elif provider_name == "orcid":
        return {
            "provider_user_id": data.get("orcid-identifier", {}).get("path", ""),
            "email": "",  # ORCID doesn't always return email
            "name": _extract_orcid_name(data),
            "avatar": "",
            "email_verified": False,
        }

    return {
        "provider_user_id": str(data.get("id", data.get("sub", ""))),
        "email": data.get("email", ""),
        "name": data.get("name", ""),
        "avatar": data.get("picture", data.get("avatar_url", "")),
        "email_verified": False,
    }


def _fetch_github_primary_email(access_token: str) -> str:
    """Fetch primary email from GitHub emails endpoint."""
    import urllib.request

    try:
        req = urllib.request.Request(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            emails = json.loads(response.read().decode())
            for email_obj in emails:
                if email_obj.get("primary") and email_obj.get("verified"):
                    return email_obj["email"]
            if emails:
                return emails[0].get("email", "")
    except Exception:
        pass
    return ""


def _extract_orcid_name(data: Dict) -> str:
    """Extract display name from ORCID person data."""
    try:
        person = data.get("person", data)
        name_obj = person.get("name", {})
        given = name_obj.get("given-names", {}).get("value", "")
        family = name_obj.get("family-name", {}).get("value", "")
        return f"{given} {family}".strip()
    except Exception:
        return ""


# ─── Account Linking / Creation ─────────────────────────────────────────────────

def process_oauth_callback(
    db: Session,
    provider_name: str,
    user_info: Dict[str, Any],
    tokens: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process OAuth2 callback: find existing connection, link, or create new account.
    Returns dict with user data and CARVanta JWT tokens.
    """
    from api.auth import create_jwt, hash_token, ACCESS_TOKEN_EXPIRE_HOURS

    provider_user_id = user_info.get("provider_user_id", "")
    email = user_info.get("email", "").lower().strip()

    # 1. Check if OAuth connection already exists
    existing_conn = db.query(OAuthConnection).filter(
        OAuthConnection.provider == provider_name,
        OAuthConnection.provider_user_id == provider_user_id,
    ).first()

    if existing_conn:
        # Returning user — update tokens and last used
        existing_conn.access_token_encrypted = tokens.get("access_token", "")
        existing_conn.refresh_token_encrypted = tokens.get("refresh_token", "")
        existing_conn.last_used_at = datetime.now(timezone.utc)
        if tokens.get("expires_in"):
            existing_conn.token_expires_at = datetime.now(timezone.utc)

        user = db.query(User).filter(User.id == existing_conn.user_id).first()
        if not user:
            return {"error": "Linked user account not found"}

        # Update login stats
        user.last_login = datetime.now(timezone.utc)
        user.login_count += 1
        db.commit()

        return _generate_auth_response(user, provider_name)

    # 2. Check if email matches an existing user (link accounts)
    if email:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            # Link provider to existing account
            _create_oauth_connection(db, existing_user.id, provider_name, user_info, tokens)
            existing_user.is_verified = True  # OAuth email is pre-verified
            existing_user.last_login = datetime.now(timezone.utc)
            existing_user.login_count += 1
            db.commit()

            return _generate_auth_response(existing_user, provider_name)

    # 3. Create new account + link provider
    if not email:
        return {"error": "Email not provided by OAuth provider. Please register manually."}

    # Generate unique username from provider data
    base_username = user_info.get("username", "") or email.split("@")[0]
    username = _generate_unique_username(db, base_username)

    new_user = User(
        email=email,
        username=username,
        password_hash="OAUTH_NO_PASSWORD_" + secrets.token_hex(16),  # No password for OAuth users
        full_name=user_info.get("name", username),
        role="researcher",
        is_verified=True,  # OAuth emails are pre-verified
        avatar_url=user_info.get("avatar", ""),
    )
    db.add(new_user)
    db.flush()  # Get the ID before creating connection

    _create_oauth_connection(db, new_user.id, provider_name, user_info, tokens)

    new_user.last_login = datetime.now(timezone.utc)
    new_user.login_count = 1
    db.commit()

    return _generate_auth_response(new_user, provider_name)


def _create_oauth_connection(
    db: Session,
    user_id: int,
    provider_name: str,
    user_info: Dict,
    tokens: Dict,
) -> OAuthConnection:
    """Create an OAuth connection record."""
    conn = OAuthConnection(
        user_id=user_id,
        provider=provider_name,
        provider_user_id=user_info.get("provider_user_id", ""),
        provider_email=user_info.get("email", ""),
        provider_name=user_info.get("name", ""),
        provider_avatar=user_info.get("avatar", ""),
        access_token_encrypted=tokens.get("access_token", ""),
        refresh_token_encrypted=tokens.get("refresh_token", ""),
        scopes=",".join(tokens.get("scope", "").split()) if tokens.get("scope") else "",
        is_primary=True,
    )
    db.add(conn)
    return conn


def _generate_unique_username(db: Session, base: str) -> str:
    """Generate a unique username, appending numbers if needed."""
    username = base.lower().replace(" ", "_")[:32]
    candidate = username
    counter = 1
    while db.query(User).filter(User.username == candidate).first():
        candidate = f"{username}{counter}"
        counter += 1
    return candidate


def _generate_auth_response(user: User, provider: str) -> Dict[str, Any]:
    """Generate CARVanta JWT auth response for an OAuth user."""
    from api.auth import create_jwt, ACCESS_TOKEN_EXPIRE_HOURS, REFRESH_TOKEN_EXPIRE_DAYS

    access_token = create_jwt({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "type": "access",
        "auth_method": f"oauth_{provider}",
    })

    refresh_token = create_jwt({
        "user_id": user.id,
        "type": "refresh",
    }, expire_hours=REFRESH_TOKEN_EXPIRE_DAYS * 24)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        "auth_method": f"oauth_{provider}",
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
        },
    }


# ─── Account Unlinking ─────────────────────────────────────────────────────────

def unlink_provider(db: Session, user_id: int, provider_name: str) -> Dict[str, Any]:
    """
    Unlink an OAuth provider from a user account.
    Prevents unlinking if it's the only auth method.
    """
    connections = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id
    ).all()

    # Check if user has a password set (non-OAuth password)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}

    has_password = not user.password_hash.startswith("OAUTH_NO_PASSWORD_")
    conn_count = len(connections)

    # Must have at least one auth method remaining
    if not has_password and conn_count <= 1:
        return {"error": "Cannot unlink the only authentication method. Set a password first."}

    # Find and remove the connection
    target_conn = next(
        (c for c in connections if c.provider == provider_name), None
    )
    if not target_conn:
        return {"error": f"No {provider_name} connection found"}

    db.delete(target_conn)
    db.commit()

    return {
        "success": True,
        "message": f"{provider_name.title()} account unlinked successfully",
        "remaining_connections": conn_count - 1,
    }


# ─── List Connected Providers ───────────────────────────────────────────────────

def get_user_connections(db: Session, user_id: int) -> Dict[str, Any]:
    """Get all OAuth connections for a user."""
    connections = db.query(OAuthConnection).filter(
        OAuthConnection.user_id == user_id
    ).all()

    user = db.query(User).filter(User.id == user_id).first()
    has_password = user and not user.password_hash.startswith("OAUTH_NO_PASSWORD_")

    return {
        "has_password": has_password,
        "connections": [
            {
                "provider": conn.provider,
                "provider_email": conn.provider_email,
                "provider_name": conn.provider_name,
                "provider_avatar": conn.provider_avatar,
                "linked_at": str(conn.linked_at) if conn.linked_at else None,
                "last_used_at": str(conn.last_used_at) if conn.last_used_at else None,
                "is_primary": conn.is_primary,
            }
            for conn in connections
        ],
        "available_providers": list(PROVIDERS.keys()),
    }


# ─── Cleanup ────────────────────────────────────────────────────────────────────

def cleanup_expired_states() -> int:
    """Remove expired OAuth state tokens (older than 10 min)."""
    now = time.time()
    expired = [
        key for key, data in _pending_oauth_states.items()
        if now - data["created_at"] > 600
    ]
    for key in expired:
        del _pending_oauth_states[key]
    return len(expired)
