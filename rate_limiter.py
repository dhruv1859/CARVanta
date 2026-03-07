"""
CARVanta – Rate Limiter & API Key Middleware v1
=================================================
CARVanta-Original: Token bucket rate limiter with API key validation
for FastAPI.

Features:
  - Token bucket algorithm for smooth rate limiting
  - Configurable per-endpoint limits
  - Simple API key validation system
  - In-memory storage (suitable for single-instance deployment)

Usage:
    from api.rate_limiter import RateLimiter, require_api_key

    limiter = RateLimiter(requests_per_minute=60)
    app.add_middleware(limiter.middleware)
"""

import time
import hashlib
from collections import defaultdict
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


import os


# ─── API Key Store ──────────────────────────────────────────────────────────────
# Keys loaded from environment variables — NEVER hardcoded.
# In production, this should be backed by a database.
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

# Header name for API key
API_KEY_HEADER = "X-CARVanta-API-Key"


class TokenBucket:
    """
    Token bucket rate limiter.

    Allows bursts up to `capacity` tokens, refills at `rate` tokens per second.
    """

    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity
        self.rate = rate
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed, False if rate limited."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now

        # Refill tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def remaining(self) -> int:
        """Number of tokens remaining."""
        now = time.time()
        elapsed = now - self.last_refill
        current = min(self.capacity, self.tokens + elapsed * self.rate)
        return int(current)


class RateLimiter:
    """
    CARVanta-Original: Per-client rate limiter using token bucket algorithm.

    Tracks rate limits per IP address and per API key.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate = requests_per_minute / 60.0  # tokens per second
        self._buckets: dict[str, TokenBucket] = {}

    def _get_bucket(self, client_id: str) -> TokenBucket:
        """Get or create a token bucket for a client."""
        if client_id not in self._buckets:
            self._buckets[client_id] = TokenBucket(
                capacity=self.burst_size,
                rate=self.rate,
            )
        return self._buckets[client_id]

    def check(self, client_id: str) -> bool:
        """Check if a request from this client is allowed."""
        bucket = self._get_bucket(client_id)
        return bucket.consume()

    def remaining(self, client_id: str) -> int:
        """Get remaining requests for a client."""
        bucket = self._get_bucket(client_id)
        return bucket.remaining

    def cleanup(self, max_age_seconds: int = 3600):
        """Remove stale buckets to prevent memory leaks."""
        now = time.time()
        stale = [
            k for k, v in self._buckets.items()
            if now - v.last_refill > max_age_seconds
        ]
        for k in stale:
            del self._buckets[k]


# Global rate limiter instance
_global_limiter = RateLimiter(requests_per_minute=60, burst_size=10)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that applies rate limiting.

    Extracts client identity from API key header or IP address.
    Returns 429 Too Many Requests when limit is exceeded.
    """

    def __init__(self, app, limiter: RateLimiter = None):
        super().__init__(app)
        self.limiter = limiter or _global_limiter

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for docs and health endpoints
        path = request.url.path
        if path in ("/docs", "/redoc", "/openapi.json", "/api/health"):
            return await call_next(request)

        # Identify client
        api_key = request.headers.get(API_KEY_HEADER, "")
        if api_key:
            client_id = f"key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
            # Check if API key has custom rate limit
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            key_info = _API_KEYS.get(key_hash)
            if key_info and key_info.get("rate_limit"):
                # Use key-specific limiter
                custom_limiter = RateLimiter(
                    requests_per_minute=key_info["rate_limit"],
                    burst_size=min(key_info["rate_limit"] // 6, 50),
                )
                if not custom_limiter.check(client_id):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "message": f"Your API key allows {key_info['rate_limit']} requests/minute",
                            "retry_after_seconds": 60,
                        },
                    )
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(key_info["rate_limit"])
                response.headers["X-RateLimit-Remaining"] = str(
                    custom_limiter.remaining(client_id)
                )
                return response
        else:
            # Use IP-based limiting
            client_ip = request.client.host if request.client else "unknown"
            client_id = f"ip:{client_ip}"

        # Check rate limit
        if not self.limiter.check(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.limiter.requests_per_minute} requests/minute",
                    "retry_after_seconds": 60,
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(
            self.limiter.requests_per_minute
        )
        response.headers["X-RateLimit-Remaining"] = str(
            self.limiter.remaining(client_id)
        )

        return response


def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Validate an API key and return key info if valid.

    Returns None if key is invalid or inactive.
    """
    if not api_key:
        return None

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_info = _API_KEYS.get(key_hash)

    if key_info and key_info.get("active", False):
        return key_info
    return None


def require_api_key(request: Request) -> dict:
    """
    FastAPI dependency that requires a valid API key.

    Usage:
        @app.get("/api/premium")
        async def premium(key_info: dict = Depends(require_api_key)):
            ...
    """
    api_key = request.headers.get(API_KEY_HEADER, "")
    key_info = validate_api_key(api_key)

    if key_info is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid or missing API key",
                "message": f"Provide a valid API key in the '{API_KEY_HEADER}' header",
            },
        )

    return key_info


def generate_api_key(name: str, tier: str = "free") -> str:
    """
    Generate a new API key and register it.

    Returns the raw key string (must be stored by the user).
    """
    import secrets
    raw_key = f"carvanta-{tier}-{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    rate_limits = {
        "free": 60,
        "pro": 300,
        "enterprise": 1000,
    }

    _API_KEYS[key_hash] = {
        "name": name,
        "tier": tier,
        "rate_limit": rate_limits.get(tier, 60),
        "active": True,
    }

    return raw_key
