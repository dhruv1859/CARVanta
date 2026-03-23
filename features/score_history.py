"""
CARVanta – Score Time-Series Tracker v1
==========================================
Tracks how antigen CVS scores change over time as new data and
model versions are released. Stores historical score snapshots
in SQLite for trend analysis.

CARVanta-Original: Score evolution tracking for time-series analysis.

Usage:
    from features.score_history import record_score, get_score_history
    record_score("CD19", 0.948, "v5", "Tier 1 - Highly Viable")
    history = get_score_history("CD19")
"""

import os
import sqlite3
import threading
from datetime import datetime, timezone


# ─── Database path ──────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DB_PATH = os.path.join(_BASE_DIR, "data", "score_history.db")

_write_lock = threading.Lock()


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(HISTORY_DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            antigen TEXT NOT NULL,
            cvs_score REAL NOT NULL,
            tier TEXT NOT NULL,
            model_version TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            cancer_type TEXT DEFAULT 'all',
            confidence REAL DEFAULT 0,
            notes TEXT DEFAULT ''
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sh_antigen ON score_history(antigen)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sh_timestamp ON score_history(timestamp)")
    conn.commit()
    conn.close()


_init_db()


def record_score(
    antigen: str,
    cvs_score: float,
    model_version: str,
    tier: str,
    cancer_type: str = "all",
    confidence: float = 0,
    notes: str = "",
):
    """Record a score snapshot for time-series tracking."""
    timestamp = datetime.now(timezone.utc).isoformat()

    with _write_lock:
        conn = _get_connection()
        conn.execute(
            """INSERT INTO score_history
               (antigen, cvs_score, tier, model_version, timestamp, cancer_type, confidence, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (antigen.upper(), round(cvs_score, 4), tier, model_version,
             timestamp, cancer_type, round(confidence, 2), notes),
        )
        conn.commit()
        conn.close()


def get_score_history(antigen: str, limit: int = 50) -> dict:
    """Get historical score data for an antigen."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM score_history WHERE antigen = ? ORDER BY timestamp DESC LIMIT ?",
        (antigen.upper(), limit),
    ).fetchall()
    conn.close()

    entries = [dict(row) for row in rows]

    if len(entries) < 2:
        trend = "insufficient_data"
        score_delta = 0
    else:
        latest = entries[0]["cvs_score"]
        oldest = entries[-1]["cvs_score"]
        score_delta = round(latest - oldest, 4)
        if score_delta > 0.01:
            trend = "improving"
        elif score_delta < -0.01:
            trend = "declining"
        else:
            trend = "stable"

    return {
        "antigen": antigen.upper(),
        "total_snapshots": len(entries),
        "trend": trend,
        "score_delta": score_delta,
        "current_score": entries[0]["cvs_score"] if entries else None,
        "history": entries,
    }


def record_batch_scores(scores: list):
    """
    Record multiple score snapshots at once.
    Each item: {"antigen": str, "cvs_score": float, "tier": str, "model_version": str}
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    with _write_lock:
        conn = _get_connection()
        for s in scores:
            conn.execute(
                """INSERT INTO score_history
                   (antigen, cvs_score, tier, model_version, timestamp, cancer_type, confidence, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (s.get("antigen", "").upper(),
                 round(s.get("cvs_score", 0), 4),
                 s.get("tier", ""),
                 s.get("model_version", "v5"),
                 timestamp,
                 s.get("cancer_type", "all"),
                 round(s.get("confidence", 0), 2),
                 s.get("notes", "")),
            )
        conn.commit()
        conn.close()


def get_all_tracked_antigens() -> dict:
    """List all antigens with score history."""
    conn = _get_connection()
    rows = conn.execute(
        """SELECT antigen, COUNT(*) as snapshots,
                  MIN(cvs_score) as min_score, MAX(cvs_score) as max_score,
                  MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
           FROM score_history
           GROUP BY antigen ORDER BY antigen"""
    ).fetchall()
    conn.close()

    return {
        "total_antigens": len(rows),
        "antigens": [dict(row) for row in rows],
    }
