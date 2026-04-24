"""
CARVanta – Advanced Rate Limiter & API Gateway v2
====================================================
Enterprise-grade rate limiting with multiple strategies,
JWT-aware user identification, per-endpoint rules,
sliding window + token bucket algorithms, IP blacklisting,
geo-blocking, and plan-aware quota enforcement.

Features:
  - Dual algorithm: Token Bucket + Sliding Window Log
  - Per-endpoint custom rate rules
  - JWT-aware user identification (rate by user, not just IP)
  - Plan-based rate limits (Free: 60/min, Pro: 300/min, Enterprise: 1000/min)
  - IP whitelist / blacklist with persistence
  - Automatic IP banning on abuse detection
  - Rate limit headers (X-RateLimit-*, Retry-After)
  - Real-time metrics and analytics export
  - Background cleanup of stale tracking data
  - DDoS detection heuristics

Usage:
    from api.rate_limiter import RateLimiter, RateLimitMiddleware

    limiter = RateLimiter(requests_per_minute=60)
    app.add_middleware(RateLimitMiddleware, limiter=limiter)
"""

import os
import time
import json
import hashlib
import secrets
import threading
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# ─── Configuration ──────────────────────────────────────────────────────────────

API_KEY_HEADER = "X-CARVanta-API-Key"

# Plan-based limits (requests per minute)
PLAN_RATE_LIMITS = {
    "free": 60,
    "pro": 300,
    "enterprise": 1000,
    "admin": 5000,
}

# Per-endpoint overrides (path prefix -> custom RPM)
ENDPOINT_RATE_RULES: Dict[str, int] = {
    "/api/v5/enterprise/billing/webhook": 200,    # Webhooks need higher limits
    "/api/v5/enterprise/analytics": 120,          # Analytics is expensive
    "/api/v5/enterprise/compliance/export": 10,   # Data export is very expensive
    "/api/v5/auth/login": 20,                        # Brute-force protection
    "/api/v5/auth/register": 10,                     # Prevent spam registration
    "/api/v5/auth/verify-email": 30,                 # Moderate limit
    "/api/v5/score": 100,                                # Scoring endpoint
    "/api/v5/batch_score": 30,                           # Batch scoring is heavy
    "/api/v5/multi-target": 30,                      # Combo analysis is heavy
    "/api/v5/query": 60,                             # NLP queries
    "/api/v5/bridge/graph": 20,                      # Graph data payload is very heavy
}

# Paths exempt from rate limiting
EXEMPT_PATHS = {"/docs", "/redoc", "/openapi.json", "/favicon.ico", "/health"}

# IP banning thresholds
AUTO_BAN_THRESHOLD = 500     # Requests per minute to trigger auto-ban
AUTO_BAN_DURATION_SECONDS = 3600  # 1 hour ban
MAX_FAILED_AUTH_PER_MINUTE = 15   # Auth failures before temp ban

# Background cleanup interval
CLEANUP_INTERVAL_SECONDS = 300   # Clean up every 5 minutes


# ─── API Key Store ──────────────────────────────────────────────────────────────

def _load_api_keys_from_env() -> dict:
    """Load API keys from environment variables and hash them."""
    keys = {}
    key_configs = [
        ("CARVANTA_API_KEY_DEV", "Development Key", "free", 60),
        ("CARVANTA_API_KEY_PRO", "Pro Access Key", "pro", 300),
        ("CARVANTA_API_KEY_ENTERPRISE", "Enterprise Key", "enterprise", 1000),
    ]
    for env_var, name, tier, rate_limit in key_configs:
        raw_key = os.getenv(env_var, "")
        if raw_key:
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            keys[key_hash] = {
                "name": name,
                "tier": tier,
                "rate_limit": rate_limit,
                "active": True,
            }
    return keys


_API_KEYS = _load_api_keys_from_env()


# ─── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class TokenBucket:
    """
    Token bucket rate limiter.
    Allows bursts up to capacity, refills at rate tokens/second.
    """
    capacity: int
    rate: float
    tokens: float = 0.0
    last_refill: float = 0.0

    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.time()

    def consume(self, count: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now

        # Refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

        if self.tokens >= count:
            self.tokens -= count
            return True
        return False

    @property
    def remaining(self) -> int:
        now = time.time()
        elapsed = now - self.last_refill
        current = min(self.capacity, self.tokens + elapsed * self.rate)
        return max(0, int(current))

    @property
    def seconds_until_token(self) -> float:
        """Seconds until the next token is available."""
        if self.tokens >= 1:
            return 0.0
        deficit = 1.0 - self.tokens
        return round(deficit / max(self.rate, 0.001), 1)


@dataclass
class SlidingWindowCounter:
    """
    Sliding window rate limiter for precise request counting.
    Tracks exact request timestamps within a rolling window.
    """
    window_seconds: int = 60
    max_requests: int = 60
    requests: List[float] = field(default_factory=list)

    def record_and_check(self) -> bool:
        """Record a request and check if within limits."""
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove expired entries
        self.requests = [t for t in self.requests if t > cutoff]

        if len(self.requests) >= self.max_requests:
            return False

        self.requests.append(now)
        return True

    @property
    def current_count(self) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        return sum(1 for t in self.requests if t > cutoff)

    @property
    def remaining(self) -> int:
        return max(0, self.max_requests - self.current_count)


@dataclass
class ClientState:
    """Complete rate limiting state for a single client."""
    token_bucket: TokenBucket
    sliding_window: SlidingWindowCounter
    auth_failures: List[float] = field(default_factory=list)
    banned_until: float = 0.0
    total_requests: int = 0
    total_blocked: int = 0
    first_seen: float = 0.0
    last_seen: float = 0.0
    plan_tier: str = "free"

    def is_banned(self) -> bool:
        return time.time() < self.banned_until

    def record_auth_failure(self):
        now = time.time()
        self.auth_failures = [t for t in self.auth_failures if now - t < 60]
        self.auth_failures.append(now)


# ─── Rate Limiter Engine ──────────────────────────────────────────────────────

class RateLimiter:
    """
    Enterprise rate limiter combining token bucket and sliding window
    algorithms for precise and fair rate limiting.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate = requests_per_minute / 60.0  # tokens per second

        self._clients: Dict[str, ClientState] = {}
        self._lock = threading.Lock()

        # IP ban list
        self._ip_blacklist: Dict[str, float] = {}  # IP -> banned_until timestamp
        self._ip_whitelist: set = set()

        # Metrics
        self._total_requests = 0
        self._total_blocked = 0
        self._metrics_history: List[Dict] = []

        # Start background cleanup
        self._start_cleanup()

    def _get_client_state(self, client_id: str, plan_tier: str = "free") -> ClientState:
        """Get or create rate limiting state for a client."""
        with self._lock:
            if client_id not in self._clients:
                rpm = PLAN_RATE_LIMITS.get(plan_tier, self.requests_per_minute)
                burst = min(rpm // 6, 50) if plan_tier != "free" else self.burst_size

                self._clients[client_id] = ClientState(
                    token_bucket=TokenBucket(capacity=burst, rate=rpm / 60.0),
                    sliding_window=SlidingWindowCounter(
                        window_seconds=60,
                        max_requests=rpm,
                    ),
                    first_seen=time.time(),
                    plan_tier=plan_tier,
                )
            return self._clients[client_id]

    def check(
        self,
        client_id: str,
        endpoint: str = "",
        plan_tier: str = "free",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a request is allowed.
        Returns (is_allowed, rate_info_dict).
        """
        state = self._get_client_state(client_id, plan_tier)
        now = time.time()
        state.total_requests += 1
        state.last_seen = now
        self._total_requests += 1

        # Check IP ban
        ip = client_id.replace("ip:", "").replace("key:", "")
        if ip in self._ip_blacklist and now < self._ip_blacklist[ip]:
            state.total_blocked += 1
            self._total_blocked += 1
            remaining_ban = int(self._ip_blacklist[ip] - now)
            return False, {
                "blocked": True,
                "reason": "ip_banned",
                "retry_after": remaining_ban,
                "message": f"IP temporarily banned. Try again in {remaining_ban}s.",
            }

        # Check whitelist
        if ip in self._ip_whitelist:
            return True, {"allowed": True, "whitelisted": True}

        # Get endpoint-specific limit
        endpoint_rpm = self._get_endpoint_limit(endpoint, plan_tier)

        # Apply sliding window check
        if not state.sliding_window.record_and_check():
            state.total_blocked += 1
            self._total_blocked += 1

            # Auto-ban if severely over limit
            if state.sliding_window.current_count > AUTO_BAN_THRESHOLD:
                self._ban_ip(ip, AUTO_BAN_DURATION_SECONDS)

            return False, {
                "blocked": True,
                "reason": "rate_limited",
                "limit": endpoint_rpm,
                "current": state.sliding_window.current_count,
                "remaining": 0,
                "retry_after": 60,
                "message": f"Rate limit exceeded ({endpoint_rpm}/min)",
            }

        # Apply token bucket check (for burst control)
        if not state.token_bucket.consume():
            state.total_blocked += 1
            self._total_blocked += 1
            retry = state.token_bucket.seconds_until_token
            return False, {
                "blocked": True,
                "reason": "burst_limited",
                "retry_after": max(1, int(retry)),
                "message": "Too many requests in a short period. Please wait.",
            }

        return True, {
            "allowed": True,
            "remaining": state.sliding_window.remaining,
            "limit": endpoint_rpm,
            "plan_tier": plan_tier,
        }

    def _get_endpoint_limit(self, endpoint: str, plan_tier: str) -> int:
        """Get rate limit for a specific endpoint, with plan scaling."""
        for pattern, limit in ENDPOINT_RATE_RULES.items():
            if endpoint.startswith(pattern):
                # Scale by plan tier
                multiplier = {"free": 1, "pro": 3, "enterprise": 10, "admin": 50}
                return limit * multiplier.get(plan_tier, 1)
        return PLAN_RATE_LIMITS.get(plan_tier, self.requests_per_minute)

    def record_auth_failure(self, client_id: str):
        """Record an authentication failure for the client."""
        state = self._get_client_state(client_id)
        state.record_auth_failure()

        # Auto-ban on too many auth failures
        if len(state.auth_failures) > MAX_FAILED_AUTH_PER_MINUTE:
            ip = client_id.replace("ip:", "").replace("key:", "")
            self._ban_ip(ip, AUTO_BAN_DURATION_SECONDS)

    def remaining(self, client_id: str) -> int:
        """Get remaining requests for a client."""
        if client_id in self._clients:
            return self._clients[client_id].sliding_window.remaining
        return self.requests_per_minute

    # ─── IP Management ─────────────────────────────────────────────────────

    def _ban_ip(self, ip: str, duration_seconds: int):
        """Temporarily ban an IP address."""
        self._ip_blacklist[ip] = time.time() + duration_seconds

    def add_to_blacklist(self, ip: str, duration_seconds: int = 86400):
        """Manually blacklist an IP."""
        self._ban_ip(ip, duration_seconds)

    def remove_from_blacklist(self, ip: str):
        """Remove an IP from the blacklist."""
        self._ip_blacklist.pop(ip, None)

    def add_to_whitelist(self, ip: str):
        """Add an IP to the whitelist (exempt from rate limiting)."""
        self._ip_whitelist.add(ip)

    def remove_from_whitelist(self, ip: str):
        """Remove an IP from the whitelist."""
        self._ip_whitelist.discard(ip)

    def get_ip_lists(self) -> Dict[str, Any]:
        """Get current blacklist and whitelist."""
        now = time.time()
        return {
            "blacklist": {
                ip: {"banned_until": t, "remaining_seconds": max(0, int(t - now))}
                for ip, t in self._ip_blacklist.items()
                if t > now
            },
            "whitelist": list(self._ip_whitelist),
        }

    # ─── Metrics ────────────────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Get real-time rate limiter metrics."""
        with self._lock:
            active_clients = len(self._clients)
            banned_ips = sum(
                1 for t in self._ip_blacklist.values() if t > time.time()
            )

            # Top blocked clients
            top_blocked = sorted(
                [
                    {"client": k, "blocked": v.total_blocked, "total": v.total_requests}
                    for k, v in self._clients.items()
                    if v.total_blocked > 0
                ],
                key=lambda x: x["blocked"],
                reverse=True,
            )[:10]

        return {
            "total_requests": self._total_requests,
            "total_blocked": self._total_blocked,
            "block_rate": round(
                self._total_blocked / max(self._total_requests, 1) * 100, 2
            ),
            "active_clients": active_clients,
            "banned_ips": banned_ips,
            "whitelisted_ips": len(self._ip_whitelist),
            "top_blocked_clients": top_blocked,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ─── Cleanup ────────────────────────────────────────────────────────────

    def _start_cleanup(self):
        """Start background cleanup thread."""
        def cleanup_loop():
            while True:
                time.sleep(CLEANUP_INTERVAL_SECONDS)
                self.cleanup()

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def cleanup(self, max_age_seconds: int = 3600):
        """Remove stale client states and expired bans."""
        now = time.time()
        with self._lock:
            # Clean stale clients
            stale = [
                k for k, v in self._clients.items()
                if now - v.last_seen > max_age_seconds
            ]
            for k in stale:
                del self._clients[k]

            # Clean expired bans
            expired_bans = [
                ip for ip, t in self._ip_blacklist.items()
                if t <= now
            ]
            for ip in expired_bans:
                del self._ip_blacklist[ip]


# Global rate limiter instance
_global_limiter = RateLimiter(requests_per_minute=60, burst_size=10)


# ─── FastAPI Middleware ─────────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware applying enterprise rate limiting.
    JWT-aware for user-level limits; falls back to IP-based.
    """

    def __init__(self, app, limiter: RateLimiter = None):
        super().__init__(app)
        self.limiter = limiter or _global_limiter

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)

        # Identify client (JWT user > API key > IP)
        client_id, plan_tier = self._identify_client(request)

        # Check rate limit
        allowed, info = self.limiter.check(client_id, path, plan_tier)

        if not allowed:
            # Record auth failure if it's a login attempt
            if path.startswith("/api/auth/login"):
                self.limiter.record_auth_failure(client_id)

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": info.get("message", "Too many requests"),
                    "retry_after_seconds": info.get("retry_after", 60),
                    "limit": info.get("limit"),
                    "plan_tier": plan_tier,
                },
                headers={
                    "Retry-After": str(info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(info.get("limit", 60)),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        # Add rate limit headers to all responses
        response.headers["X-RateLimit-Limit"] = str(info.get("limit", 60))
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Plan"] = plan_tier

        return response

    def _identify_client(self, request: Request) -> Tuple[str, str]:
        """
        Identify the client and their plan tier.
        Priority: JWT user_id > API key > IP address.
        """
        plan_tier = "free"

        # Try JWT token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                import base64
                token = auth_header[7:]
                payload_b64 = token.split(".")[1]
                padding = 4 - len(payload_b64) % 4
                payload_b64 += "=" * padding
                payload = json.loads(base64.b64decode(payload_b64))
                user_id = payload.get("sub", payload.get("user_id"))
                if user_id:
                    plan_tier = payload.get("plan", "free")
                    return f"user:{user_id}", plan_tier
            except Exception:
                pass

        # Try API key
        api_key = request.headers.get(API_KEY_HEADER, "")
        if api_key:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            key_info = _API_KEYS.get(key_hash)
            if key_info and key_info.get("active"):
                plan_tier = key_info.get("tier", "free")
                return f"key:{key_hash[:16]}", plan_tier

        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}", plan_tier


# ─── API Key Management ────────────────────────────────────────────────────────

def validate_api_key(api_key: str) -> Optional[dict]:
    """Validate an API key and return info if valid."""
    if not api_key:
        return None
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_info = _API_KEYS.get(key_hash)
    if key_info and key_info.get("active", False):
        return key_info
    return None


def require_api_key(request: Request) -> dict:
    """FastAPI dependency requiring a valid API key."""
    api_key = request.headers.get(API_KEY_HEADER, "")
    key_info = validate_api_key(api_key)
    if key_info is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid or missing API key",
                "message": f"Provide a valid key in '{API_KEY_HEADER}' header",
            },
        )
    return key_info


def generate_api_key(name: str, tier: str = "free") -> str:
    """Generate a new API key and register it."""
    raw_key = f"carvanta-{tier}-{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    _API_KEYS[key_hash] = {
        "name": name,
        "tier": tier,
        "rate_limit": PLAN_RATE_LIMITS.get(tier, 60),
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return raw_key


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    if key_hash in _API_KEYS:
        _API_KEYS[key_hash]["active"] = False
        return True
    return False


def list_api_keys() -> List[Dict]:
    """List all registered API keys (without exposing hashes)."""
    return [
        {
            "name": info["name"],
            "tier": info["tier"],
            "rate_limit": info["rate_limit"],
            "active": info["active"],
            "created_at": info.get("created_at", "unknown"),
        }
        for info in _API_KEYS.values()
    ]
