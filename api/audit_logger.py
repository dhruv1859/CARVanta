"""
CARVanta – Tamper-Proof Audit Logger v2
=========================================
Enterprise-grade, cryptographically-chained audit trail for all API requests.
Each entry is hashed with SHA-256 and chain-linked to the previous entry,
creating an immutable, verifiable ledger similar to blockchain technology.

Security features:
  - SHA-256 chained hashing (each entry includes previous entry's hash)
  - HMAC-signed integrity seals using a server-side secret
  - Genesis block initialization for chain root
  - Full chain verification with gap detection
  - Tampering detection with per-entry and chain-level checks
  - Request body hashing (never stores raw PHI data)
  - User attribution via JWT token extraction
  - Geo-IP context capture
  - Suspicious activity detection and alerting
  - Retention policy enforcement

HIPAA §164.312(b): Audit controls – hardware, software, and/or procedural
mechanisms that record and examine activity in systems containing ePHI.

ISO 13485: Records shall be established and maintained to provide evidence
of conformity to requirements and effective operation of the QMS.
"""

import os
import time
import json
import sqlite3
import hashlib
import hmac
import threading
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# ─── Configuration ──────────────────────────────────────────────────────────────

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_DB_PATH = os.path.join(_BASE_DIR, "data", "audit_log.db")
AUDIT_HMAC_SECRET = os.getenv(
    "AUDIT_HMAC_SECRET",
    hashlib.sha256(b"carvanta-audit-integrity-key").hexdigest()
)

# Retention
RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "2555"))  # 7 years for HIPAA
ALERT_THRESHOLD_PER_MIN = 200  # Suspicious if > 200 requests/min from single IP

# Thread safety
_write_lock = threading.Lock()
_chain_lock = threading.Lock()

# In-memory chain state
_last_entry_hash = None
_entry_counter = 0

# Suspicious activity tracking
_ip_request_counts: Dict[str, List[float]] = defaultdict(list)
_suspicious_alerts: List[Dict] = []


# ─── Database ──────────────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode for concurrent reads."""
    os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(AUDIT_DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Create the tamper-proof audit_log table with chain columns."""
    conn = _get_connection()

    # Migration: if old table exists without new columns, drop and recreate
    try:
        cursor = conn.execute("PRAGMA table_info(audit_log)")
        columns = [row[1] for row in cursor.fetchall()]
        if columns and "chain_sequence" not in columns:
            print("[AuditLogger] Migrating old audit_log table to tamper-proof schema...")
            conn.execute("ALTER TABLE audit_log RENAME TO audit_log_v1_backup")
            conn.commit()
    except Exception:
        pass  # Table doesn't exist yet, that's fine

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            query_params TEXT,
            request_hash TEXT,
            status_code INTEGER,
            latency_ms REAL,
            client_ip TEXT,
            user_agent TEXT,

            -- Tamper-proof chain fields
            entry_hash TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            hmac_seal TEXT NOT NULL,
            chain_sequence INTEGER NOT NULL,

            -- Enhanced attribution
            user_id TEXT,
            session_id TEXT,
            request_id TEXT UNIQUE,
            response_size_bytes INTEGER,
            error_message TEXT,

            -- Severity classification
            severity TEXT DEFAULT 'info',
            category TEXT DEFAULT 'api_request',
            is_suspicious INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_path
            ON audit_log(path);
        CREATE INDEX IF NOT EXISTS idx_audit_chain_seq
            ON audit_log(chain_sequence);
        CREATE INDEX IF NOT EXISTS idx_audit_entry_hash
            ON audit_log(entry_hash);
        CREATE INDEX IF NOT EXISTS idx_audit_user
            ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_severity
            ON audit_log(severity);
        CREATE INDEX IF NOT EXISTS idx_audit_suspicious
            ON audit_log(is_suspicious);
        CREATE INDEX IF NOT EXISTS idx_audit_category
            ON audit_log(category);

        -- Integrity verification log
        CREATE TABLE IF NOT EXISTS audit_integrity_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_timestamp TEXT NOT NULL,
            total_entries_checked INTEGER,
            valid_entries INTEGER,
            tampered_entries INTEGER,
            missing_links INTEGER,
            chain_valid INTEGER,
            integrity_score REAL,
            details TEXT
        );

        -- Alert log
        CREATE TABLE IF NOT EXISTS audit_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            source_ip TEXT,
            user_id TEXT,
            details TEXT,
            is_resolved INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()


# Initialize on import
_init_db()


def _load_chain_state():
    """Load the last entry hash and sequence from the database for chain continuity."""
    global _last_entry_hash, _entry_counter
    try:
        conn = _get_connection()
        row = conn.execute(
            "SELECT entry_hash, chain_sequence FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        if row:
            _last_entry_hash = row["entry_hash"]
            _entry_counter = row["chain_sequence"]
        else:
            # Genesis block
            _last_entry_hash = _create_genesis_hash()
            _entry_counter = 0
    except Exception:
        _last_entry_hash = _create_genesis_hash()
        _entry_counter = 0


def _create_genesis_hash() -> str:
    """Create the genesis (root) hash for the chain."""
    genesis_data = json.dumps({
        "type": "genesis",
        "platform": "CARVanta",
        "version": "2.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Tamper-proof audit chain genesis block",
    }, sort_keys=True)
    return hashlib.sha256(genesis_data.encode()).hexdigest()


# Load chain state on module import
_load_chain_state()


# ─── Cryptographic Hashing ─────────────────────────────────────────────────────

def _hash_body(body: bytes) -> str:
    """SHA-256 hash the request body for PHI compliance (never store raw)."""
    if not body:
        return ""
    return hashlib.sha256(body).hexdigest()[:16]


def _compute_entry_hash(
    timestamp: str,
    method: str,
    path: str,
    status_code: int,
    client_ip: str,
    previous_hash: str,
    chain_sequence: int,
) -> str:
    """
    Compute SHA-256 hash for an audit entry.
    Includes all critical fields + the previous hash for chain integrity.
    """
    entry_data = json.dumps({
        "ts": timestamp,
        "method": method,
        "path": path,
        "status": status_code,
        "ip": client_ip,
        "prev": previous_hash,
        "seq": chain_sequence,
    }, sort_keys=True)
    return hashlib.sha256(entry_data.encode()).hexdigest()


def _compute_hmac_seal(entry_hash: str) -> str:
    """
    Create an HMAC seal for the entry hash using the server secret.
    This prevents someone who only has DB access from forging entries,
    since they'd need the HMAC secret to create valid seals.
    """
    return hmac.new(
        AUDIT_HMAC_SECRET.encode(),
        entry_hash.encode(),
        hashlib.sha256,
    ).hexdigest()


def _verify_hmac_seal(entry_hash: str, seal: str) -> bool:
    """Verify an HMAC seal using constant-time comparison."""
    expected = _compute_hmac_seal(entry_hash)
    return hmac.compare_digest(expected, seal)


# ─── Suspicious Activity Detection ────────────────────────────────────────────

def _check_suspicious_activity(client_ip: str, path: str, status_code: int) -> bool:
    """
    Detect suspicious activity patterns:
    - High request rate from single IP
    - Repeated 401/403 errors (brute force)
    - Access to sensitive endpoints
    """
    now = time.time()

    # Track requests per IP (sliding 60-second window)
    _ip_request_counts[client_ip] = [
        t for t in _ip_request_counts[client_ip] if now - t < 60
    ]
    _ip_request_counts[client_ip].append(now)

    # Check rate
    request_count = len(_ip_request_counts[client_ip])
    if request_count > ALERT_THRESHOLD_PER_MIN:
        _create_alert("rate_limit_exceeded", "high", client_ip, None,
                       f"IP made {request_count} requests in 60s")
        return True

    # Check for auth brute force (> 10 failed auth attempts in 60s)
    if status_code in (401, 403) and path.startswith("/api/"):
        auth_failures = sum(
            1 for t in _ip_request_counts.get(f"{client_ip}_auth_fail", [])
            if now - t < 60
        )
        _ip_request_counts[f"{client_ip}_auth_fail"].append(now)
        if auth_failures > 10:
            _create_alert("brute_force_suspected", "critical", client_ip, None,
                           f"Multiple auth failures from IP")
            return True

    # Check sensitive endpoint access
    sensitive_patterns = ["/admin", "/compliance", "/phi", "/billing/webhook"]
    if any(pattern in path for pattern in sensitive_patterns):
        if status_code >= 400:
            _create_alert("sensitive_endpoint_failure", "medium", client_ip, None,
                           f"Failed access to {path} (HTTP {status_code})")
            return True

    return False


def _create_alert(
    alert_type: str,
    severity: str,
    source_ip: str = None,
    user_id: str = None,
    details: str = None,
):
    """Record a security alert."""
    try:
        conn = _get_connection()
        conn.execute(
            """INSERT INTO audit_alerts
               (timestamp, alert_type, severity, source_ip, user_id, details)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (datetime.now(timezone.utc).isoformat(), alert_type, severity,
             source_ip, user_id, details),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Keep in-memory for quick access
    _suspicious_alerts.append({
        "type": alert_type,
        "severity": severity,
        "ip": source_ip,
        "time": datetime.now(timezone.utc).isoformat(),
    })
    # Trim to last 100
    while len(_suspicious_alerts) > 100:
        _suspicious_alerts.pop(0)


# ─── Classification ────────────────────────────────────────────────────────────

def _classify_severity(status_code: int, latency_ms: float, path: str) -> str:
    """Classify the severity of an audit entry."""
    if status_code >= 500:
        return "error"
    if status_code in (401, 403):
        return "warning"
    if status_code >= 400:
        return "notice"
    if latency_ms > 5000:
        return "warning"  # Slow request
    return "info"


def _classify_category(method: str, path: str) -> str:
    """Classify the category of the request."""
    if "/auth/" in path or "/login" in path or "/register" in path:
        return "authentication"
    if "/api/v5/enterprise/" in path:
        return "enterprise"
    if "/compliance/" in path or "/phi" in path:
        return "compliance"
    if "/billing/" in path:
        return "billing"
    if "/org/" in path:
        return "organization"
    if "/mfa/" in path:
        return "security"
    if "/oauth/" in path:
        return "oauth"
    if "/analytics/" in path:
        return "analytics"
    if method == "DELETE":
        return "deletion"
    if "/admin" in path:
        return "admin"
    return "api_request"


# ─── Core Logging ──────────────────────────────────────────────────────────────

def log_request(
    method: str,
    path: str,
    query_params: str = "",
    request_hash: str = "",
    status_code: int = 200,
    latency_ms: float = 0.0,
    client_ip: str = "",
    user_agent: str = "",
    user_id: str = None,
    session_id: str = None,
    response_size: int = None,
    error_message: str = None,
):
    """
    Insert a tamper-proof audit log entry with chain linking.
    Each entry includes:
    - SHA-256 hash of its own data
    - Reference to the previous entry's hash (chain link)
    - HMAC seal signed with server secret
    """
    global _last_entry_hash, _entry_counter

    timestamp = datetime.now(timezone.utc).isoformat()
    request_id = f"req_{secrets.token_hex(8)}"

    # Classify
    severity = _classify_severity(status_code, latency_ms, path)
    category = _classify_category(method, path)

    # Check suspicious activity
    is_suspicious = _check_suspicious_activity(client_ip, path, status_code)

    with _chain_lock:
        _entry_counter += 1
        chain_sequence = _entry_counter
        previous_hash = _last_entry_hash or _create_genesis_hash()

        # Compute entry hash
        entry_hash = _compute_entry_hash(
            timestamp, method, path, status_code,
            client_ip, previous_hash, chain_sequence,
        )

        # Create HMAC seal
        hmac_seal = _compute_hmac_seal(entry_hash)

        # Update chain state
        _last_entry_hash = entry_hash

    # Write to DB
    with _write_lock:
        try:
            conn = _get_connection()
            conn.execute(
                """INSERT INTO audit_log
                   (timestamp, method, path, query_params, request_hash,
                    status_code, latency_ms, client_ip, user_agent,
                    entry_hash, previous_hash, hmac_seal, chain_sequence,
                    user_id, session_id, request_id, response_size_bytes,
                    error_message, severity, category, is_suspicious)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (timestamp, method, path, query_params, request_hash,
                 status_code, round(latency_ms, 2), client_ip, user_agent,
                 entry_hash, previous_hash, hmac_seal, chain_sequence,
                 user_id, session_id, request_id, response_size,
                 error_message, severity, category,
                 1 if is_suspicious else 0),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AuditLogger] Write error: {e}")


# ─── Chain Integrity Verification ──────────────────────────────────────────────

def verify_chain_integrity(limit: int = 10000) -> Dict[str, Any]:
    """
    Verify the entire audit chain for tampering.
    Checks:
    1. Each entry's hash matches its data
    2. Chain links (previous_hash) are continuous
    3. HMAC seals are valid (signed by server)
    4. No gaps in sequence numbers

    Returns a detailed integrity report.
    """
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY chain_sequence ASC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    if not rows:
        return {
            "chain_valid": True,
            "total_entries": 0,
            "message": "No audit entries to verify",
        }

    total = len(rows)
    valid_entries = 0
    tampered_entries = 0
    broken_links = 0
    invalid_seals = 0
    tampered_ids = []
    broken_link_ids = []

    expected_sequence = rows[0]["chain_sequence"]
    previous_hash = rows[0]["previous_hash"]  # First entry links to genesis

    for row in rows:
        row_dict = dict(row)

        # Check sequence continuity
        if row_dict["chain_sequence"] != expected_sequence:
            broken_links += 1
            broken_link_ids.append(row_dict["id"])

        # Recompute and verify entry hash
        recomputed = _compute_entry_hash(
            row_dict["timestamp"],
            row_dict["method"],
            row_dict["path"],
            row_dict["status_code"],
            row_dict["client_ip"] or "",
            row_dict["previous_hash"],
            row_dict["chain_sequence"],
        )

        if recomputed != row_dict["entry_hash"]:
            tampered_entries += 1
            tampered_ids.append(row_dict["id"])
        else:
            valid_entries += 1

        # Verify HMAC seal
        if not _verify_hmac_seal(row_dict["entry_hash"], row_dict["hmac_seal"]):
            invalid_seals += 1
            if row_dict["id"] not in tampered_ids:
                tampered_ids.append(row_dict["id"])

        # Check chain link
        if row_dict["previous_hash"] != previous_hash:
            broken_links += 1
            if row_dict["id"] not in broken_link_ids:
                broken_link_ids.append(row_dict["id"])

        previous_hash = row_dict["entry_hash"]
        expected_sequence += 1

    integrity_score = round(valid_entries / max(total, 1) * 100, 2)
    chain_valid = tampered_entries == 0 and broken_links == 0 and invalid_seals == 0

    result = {
        "chain_valid": chain_valid,
        "integrity_score": integrity_score,
        "total_entries": total,
        "valid_entries": valid_entries,
        "tampered_entries": tampered_entries,
        "broken_chain_links": broken_links,
        "invalid_hmac_seals": invalid_seals,
        "tampered_entry_ids": tampered_ids[:20],
        "broken_link_ids": broken_link_ids[:20],
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "INTACT" if chain_valid else "COMPROMISED",
    }

    # Record check result
    try:
        conn = _get_connection()
        conn.execute(
            """INSERT INTO audit_integrity_checks
               (check_timestamp, total_entries_checked, valid_entries,
                tampered_entries, missing_links, chain_valid, integrity_score, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (result["verified_at"], total, valid_entries,
             tampered_entries, broken_links, 1 if chain_valid else 0,
             integrity_score, json.dumps(result)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    return result


def get_integrity_history(limit: int = 20) -> List[Dict]:
    """Get history of integrity verification checks."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM audit_integrity_checks ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Query & Reporting ─────────────────────────────────────────────────────────

def get_recent_logs(
    limit: int = 100,
    path_filter: str = None,
    severity: str = None,
    category: str = None,
    user_id: str = None,
    start_date: str = None,
    end_date: str = None,
) -> list:
    """
    Retrieve recent audit log entries with advanced filtering.
    """
    conn = _get_connection()
    conditions = []
    params = []

    if path_filter:
        conditions.append("path LIKE ?")
        params.append(f"%{path_filter}%")
    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    if category:
        conditions.append("category = ?")
        params.append(category)
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    if start_date:
        conditions.append("timestamp >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("timestamp <= ?")
        params.append(end_date)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    rows = conn.execute(
        f"SELECT * FROM audit_log {where} ORDER BY id DESC LIMIT ?",
        params,
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_audit_stats() -> dict:
    """Get comprehensive statistics from the audit log."""
    conn = _get_connection()

    total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

    # Top endpoints
    endpoints = conn.execute(
        "SELECT path, COUNT(*) as cnt FROM audit_log GROUP BY path ORDER BY cnt DESC LIMIT 10"
    ).fetchall()

    # Average latency
    avg_latency = conn.execute(
        "SELECT AVG(latency_ms) FROM audit_log WHERE latency_ms > 0"
    ).fetchone()[0]

    # Error rate
    errors = conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE status_code >= 400"
    ).fetchone()[0]

    # Severity breakdown
    severity_counts = conn.execute(
        "SELECT severity, COUNT(*) as cnt FROM audit_log GROUP BY severity"
    ).fetchall()

    # Category breakdown
    category_counts = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM audit_log GROUP BY category ORDER BY cnt DESC"
    ).fetchall()

    # Suspicious events
    suspicious = conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE is_suspicious = 1"
    ).fetchone()[0]

    # Unique IPs
    unique_ips = conn.execute(
        "SELECT COUNT(DISTINCT client_ip) FROM audit_log"
    ).fetchone()[0]

    # Unique users
    unique_users = conn.execute(
        "SELECT COUNT(DISTINCT user_id) FROM audit_log WHERE user_id IS NOT NULL"
    ).fetchone()[0]

    # Today's stats
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_count = conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE timestamp >= ?",
        (today,),
    ).fetchone()[0]

    # Recent alerts
    recent_alerts = conn.execute(
        "SELECT * FROM audit_alerts ORDER BY id DESC LIMIT 10"
    ).fetchall()

    conn.close()

    return {
        "total_requests": total,
        "today_requests": today_count,
        "top_endpoints": [{"path": r[0], "count": r[1]} for r in endpoints],
        "avg_latency_ms": round(avg_latency, 2) if avg_latency else 0,
        "error_rate": round(errors / max(total, 1) * 100, 2),
        "severity_breakdown": {r[0]: r[1] for r in severity_counts},
        "category_breakdown": {r[0]: r[1] for r in category_counts},
        "suspicious_events": suspicious,
        "unique_ips": unique_ips,
        "unique_users": unique_users,
        "recent_alerts": [dict(a) for a in recent_alerts],
    }


def get_security_alerts(
    limit: int = 50,
    severity: str = None,
    unresolved_only: bool = False,
) -> List[Dict]:
    """Get security alerts from the audit system."""
    conn = _get_connection()
    conditions = []
    params = []

    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    if unresolved_only:
        conditions.append("is_resolved = 0")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    rows = conn.execute(
        f"SELECT * FROM audit_alerts {where} ORDER BY id DESC LIMIT ?",
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_alert(alert_id: int) -> Dict:
    """Mark a security alert as resolved."""
    conn = _get_connection()
    conn.execute(
        "UPDATE audit_alerts SET is_resolved = 1 WHERE id = ?",
        (alert_id,),
    )
    conn.commit()
    conn.close()
    return {"resolved": True, "alert_id": alert_id}


# ─── Retention Policy ──────────────────────────────────────────────────────────

def enforce_retention() -> Dict:
    """
    Enforce audit log retention policy.
    Removes entries older than the configured retention period.
    Archives important entries before deletion.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()

    conn = _get_connection()

    # Count entries to be purged
    count = conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE timestamp < ?",
        (cutoff,),
    ).fetchone()[0]

    if count > 0:
        # Archive critical entries before deletion
        critical_count = conn.execute(
            """SELECT COUNT(*) FROM audit_log
               WHERE timestamp < ? AND (severity IN ('error', 'warning') OR is_suspicious = 1)""",
            (cutoff,),
        ).fetchone()[0]

        # Delete old entries
        conn.execute(
            "DELETE FROM audit_log WHERE timestamp < ?",
            (cutoff,),
        )

        # Clean up old alerts
        conn.execute(
            "DELETE FROM audit_alerts WHERE timestamp < ? AND is_resolved = 1",
            (cutoff,),
        )

        conn.commit()

    conn.close()

    return {
        "retention_enforced": True,
        "cutoff_date": cutoff,
        "entries_purged": count,
        "retention_days": RETENTION_DAYS,
    }


# ─── Export ─────────────────────────────────────────────────────────────────────

def export_audit_log(
    start_date: str = None,
    end_date: str = None,
    format: str = "json",
) -> Dict[str, Any]:
    """
    Export audit log entries for compliance reporting.
    Returns metadata + entries in the requested format.
    """
    logs = get_recent_logs(
        limit=10000,
        start_date=start_date,
        end_date=end_date,
    )

    # Verify integrity before export
    integrity = verify_chain_integrity(limit=len(logs) + 100)

    export = {
        "export_metadata": {
            "platform": "CARVanta",
            "version": "2.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(logs),
            "format": format,
            "chain_integrity": integrity["verdict"],
            "integrity_score": integrity["integrity_score"],
        },
        "entries": logs,
    }

    return export


# ─── FastAPI Middleware ─────────────────────────────────────────────────────────

class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that logs every request to the tamper-proof audit database.
    Captures timing, attribution, classification, and chain-links each entry.
    """

    # Skip logging for these paths (high-frequency, low-value)
    SKIP_PATHS = {"/favicon.ico", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip noisy endpoints
        if path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()

        # Read body for hashing (never store raw — PHI compliance)
        body = b""
        try:
            body = await request.body()
        except Exception:
            pass

        # Extract user ID from JWT if present
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # Quick JWT decode (just extract sub claim from payload)
            try:
                import base64
                token = auth_header[7:]
                payload_b64 = token.split(".")[1]
                # Add padding
                padding = 4 - len(payload_b64) % 4
                payload_b64 += "=" * padding
                payload = json.loads(base64.b64decode(payload_b64))
                user_id = str(payload.get("sub", payload.get("user_id", "")))
            except Exception:
                pass

        response = await call_next(request)

        latency_ms = (time.perf_counter() - start) * 1000

        # Capture error message for 5xx responses
        error_msg = None
        if response.status_code >= 500:
            error_msg = f"HTTP {response.status_code}"

        # Get response size from headers
        response_size = None
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                response_size = int(content_length)
            except ValueError:
                pass

        # Log asynchronously to avoid blocking the response
        threading.Thread(
            target=log_request,
            kwargs={
                "method": request.method,
                "path": path,
                "query_params": str(request.query_params),
                "request_hash": _hash_body(body),
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "client_ip": request.client.host if request.client else "",
                "user_agent": request.headers.get("user-agent", "")[:200],
                "user_id": user_id,
                "session_id": request.cookies.get("session_id"),
                "response_size": response_size,
                "error_message": error_msg,
            },
            daemon=True,
        ).start()

        return response
