"""
CARVanta – Usage Analytics Engine
====================================
Real-time platform analytics, API telemetry, feature usage tracking,
and administrative dashboards for enterprise monitoring.

Provides:
  - Real-time API call analytics per user/organization
  - Feature usage heatmaps and trends
  - Session duration and engagement tracking
  - Platform health metrics and uptime
  - Anomaly detection for security monitoring
  - Exportable analytics reports
"""

import time
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from collections import defaultdict
from threading import Lock

from sqlalchemy.orm import Session
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, Boolean, Text,
    ForeignKey, Index, func,
)
from db.models import Base, User


# ─── Configuration ──────────────────────────────────────────────────────────────

ANALYTICS_RETENTION_DAYS = 90    # How long to keep detailed analytics
AGGREGATION_INTERVAL = 300       # 5-minute aggregation windows
SESSION_TIMEOUT_SECONDS = 1800   # 30 minutes of inactivity = session end


# ─── Database Models ───────────────────────────────────────────────────────────

class APICallLog(Base):
    """
    Detailed log of every API call made to the platform.
    Used for analytics, billing, and security monitoring.
    """
    __tablename__ = "api_call_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    endpoint = Column(String(256), nullable=False, index=True)
    method = Column(String(8), nullable=False)  # GET, POST, etc.
    status_code = Column(Integer, nullable=False, default=200)
    response_time_ms = Column(Float, nullable=True)
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_api_calls_user_endpoint", "user_id", "endpoint"),
        Index("idx_api_calls_time", "created_at"),
    )

    def __repr__(self):
        return f"<APICallLog {self.method} {self.endpoint} {self.status_code}>"


class FeatureUsageEvent(Base):
    """
    Tracks individual feature usage events across the platform.
    Used for heatmaps, trend analysis, and product decisions.
    """
    __tablename__ = "feature_usage_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    feature = Column(String(64), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # view, interact, complete, error
    duration_seconds = Column(Float, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_feature_usage_feature", "feature"),
        Index("idx_feature_usage_time", "created_at"),
    )

    def __repr__(self):
        return f"<FeatureUsageEvent {self.feature}:{self.action}>"


class AnalyticsSession(Base):
    """
    Tracks user sessions for engagement analytics.
    """
    __tablename__ = "analytics_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_token = Column(String(64), unique=True, nullable=False)
    started_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    page_views = Column(Integer, nullable=False, default=0)
    api_calls = Column(Integer, nullable=False, default=0)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    referrer = Column(String(512), nullable=True)

    __table_args__ = (
        Index("idx_session_user", "user_id"),
        Index("idx_session_time", "started_at"),
    )

    def __repr__(self):
        return f"<AnalyticsSession user={self.user_id} duration={self.duration_seconds}>"


class PlatformMetrics(Base):
    """
    Periodic platform health metrics snapshots.
    Captured every 5 minutes for monitoring dashboards.
    """
    __tablename__ = "platform_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(64), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    unit = Column(String(16), nullable=True)
    tags_json = Column(Text, nullable=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_metrics_name_time", "metric_name", "period_start"),
    )

    def __repr__(self):
        return f"<PlatformMetrics {self.metric_name}={self.metric_value}>"


# ─── In-Memory Real-Time Counters ──────────────────────────────────────────────

_counter_lock = Lock()
_realtime_counters: Dict[str, int] = defaultdict(int)
_hourly_window: Dict[str, List[float]] = defaultdict(list)


def _increment_counter(key: str, value: int = 1):
    """Thread-safe counter increment."""
    with _counter_lock:
        _realtime_counters[key] += value


def _get_counter(key: str) -> int:
    """Thread-safe counter read."""
    with _counter_lock:
        return _realtime_counters.get(key, 0)


# ─── API Call Tracking ──────────────────────────────────────────────────────────

def log_api_call(
    db: Session,
    user_id: int = None,
    organization_id: int = None,
    endpoint: str = "",
    method: str = "GET",
    status_code: int = 200,
    response_time_ms: float = None,
    request_size: int = None,
    response_size: int = None,
    ip_address: str = None,
    user_agent: str = None,
    error_message: str = None,
) -> None:
    """Log an API call for analytics and monitoring."""
    log = APICallLog(
        user_id=user_id,
        organization_id=organization_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        request_size_bytes=request_size,
        response_size_bytes=response_size,
        ip_address=ip_address,
        user_agent=user_agent,
        error_message=error_message,
    )
    db.add(log)
    db.commit()

    # Update real-time counters
    _increment_counter("total_api_calls")
    _increment_counter(f"api_{method.lower()}_calls")
    if status_code >= 400:
        _increment_counter("error_calls")
    if response_time_ms:
        _increment_counter("total_response_time_ms", int(response_time_ms))


# ─── Feature Usage Tracking ────────────────────────────────────────────────────

def track_feature_usage(
    db: Session,
    user_id: int,
    feature: str,
    action: str = "view",
    duration_seconds: float = None,
    metadata: Dict = None,
    organization_id: int = None,
) -> None:
    """Track a feature usage event."""
    event = FeatureUsageEvent(
        user_id=user_id,
        organization_id=organization_id,
        feature=feature,
        action=action,
        duration_seconds=duration_seconds,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(event)
    db.commit()

    _increment_counter(f"feature_{feature}")


# ─── Analytics Queries ──────────────────────────────────────────────────────────

def get_api_analytics(
    db: Session,
    user_id: int = None,
    organization_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    group_by: str = "endpoint",
) -> Dict[str, Any]:
    """
    Get API usage analytics with flexible filtering and grouping.
    """
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    query = db.query(APICallLog).filter(
        APICallLog.created_at >= start_date,
        APICallLog.created_at <= end_date,
    )

    if user_id:
        query = query.filter(APICallLog.user_id == user_id)
    if organization_id:
        query = query.filter(APICallLog.organization_id == organization_id)

    # Total stats
    total_calls = query.count()
    error_calls = query.filter(APICallLog.status_code >= 400).count()

    # Average response time
    avg_response = db.query(func.avg(APICallLog.response_time_ms)).filter(
        APICallLog.created_at >= start_date,
        APICallLog.created_at <= end_date,
    ).scalar() or 0

    # Group by endpoint
    endpoint_stats = {}
    if group_by == "endpoint":
        endpoints = db.query(
            APICallLog.endpoint,
            func.count(APICallLog.id),
            func.avg(APICallLog.response_time_ms),
        ).filter(
            APICallLog.created_at >= start_date,
            APICallLog.created_at <= end_date,
        ).group_by(APICallLog.endpoint).all()

        for ep, count, avg_time in endpoints:
            endpoint_stats[ep] = {
                "calls": count,
                "avg_response_ms": round(avg_time or 0, 2),
            }

    # Daily breakdown
    daily_stats = []
    current = start_date
    while current <= end_date:
        next_day = current + timedelta(days=1)
        day_count = query.filter(
            APICallLog.created_at >= current,
            APICallLog.created_at < next_day,
        ).count()
        daily_stats.append({
            "date": current.strftime("%Y-%m-%d"),
            "calls": day_count,
        })
        current = next_day

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "summary": {
            "total_calls": total_calls,
            "error_calls": error_calls,
            "success_rate": round((total_calls - error_calls) / max(total_calls, 1) * 100, 1),
            "avg_response_ms": round(avg_response, 2),
        },
        "by_endpoint": endpoint_stats,
        "daily": daily_stats,
    }


def get_feature_analytics(
    db: Session,
    start_date: datetime = None,
    end_date: datetime = None,
) -> Dict[str, Any]:
    """
    Get feature usage analytics — which features are most used.
    Returns data suitable for heatmap visualization.
    """
    if not start_date:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_date:
        end_date = datetime.now(timezone.utc)

    features = db.query(
        FeatureUsageEvent.feature,
        func.count(FeatureUsageEvent.id),
        func.count(func.distinct(FeatureUsageEvent.user_id)),
        func.avg(FeatureUsageEvent.duration_seconds),
    ).filter(
        FeatureUsageEvent.created_at >= start_date,
        FeatureUsageEvent.created_at <= end_date,
    ).group_by(FeatureUsageEvent.feature).all()

    feature_data = {}
    for feature, total_uses, unique_users, avg_duration in features:
        feature_data[feature] = {
            "total_uses": total_uses,
            "unique_users": unique_users,
            "avg_duration_seconds": round(avg_duration or 0, 1),
            "engagement_score": round(total_uses * (avg_duration or 1) / max(unique_users, 1), 1),
        }

    # Sort by engagement score
    sorted_features = dict(
        sorted(feature_data.items(), key=lambda x: x[1]["engagement_score"], reverse=True)
    )

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "features": sorted_features,
        "top_features": list(sorted_features.keys())[:10],
    }


# ─── Platform Health Metrics ───────────────────────────────────────────────────

def record_platform_metric(
    db: Session,
    metric_name: str,
    value: float,
    unit: str = None,
    tags: Dict = None,
) -> None:
    """Record a platform health metric snapshot."""
    now = datetime.now(timezone.utc)
    period_start = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)
    period_end = period_start + timedelta(minutes=5)

    metric = PlatformMetrics(
        metric_name=metric_name,
        metric_value=value,
        unit=unit,
        tags_json=json.dumps(tags) if tags else None,
        period_start=period_start,
        period_end=period_end,
    )
    db.add(metric)
    db.commit()


def get_platform_health(db: Session) -> Dict[str, Any]:
    """
    Get current platform health metrics for the admin dashboard.
    """
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_hour = now - timedelta(hours=1)
    last_24h = now - timedelta(hours=24)

    # API calls today
    calls_today = db.query(APICallLog).filter(
        APICallLog.created_at >= today
    ).count()

    # Errors in last hour
    errors_last_hour = db.query(APICallLog).filter(
        APICallLog.created_at >= last_hour,
        APICallLog.status_code >= 500,
    ).count()

    # Active users (last 24h)
    active_users = db.query(
        func.count(func.distinct(APICallLog.user_id))
    ).filter(
        APICallLog.created_at >= last_24h,
        APICallLog.user_id != None,
    ).scalar() or 0

    # Average response time (last hour)
    avg_response = db.query(
        func.avg(APICallLog.response_time_ms)
    ).filter(
        APICallLog.created_at >= last_hour,
    ).scalar() or 0

    # p95 response time (simplified)
    p95_response = db.query(
        func.max(APICallLog.response_time_ms)
    ).filter(
        APICallLog.created_at >= last_hour,
    ).scalar() or 0

    # Total users
    total_users = db.query(User).count()

    # Uptime (simplified — based on recent error rate)
    calls_last_hour = db.query(APICallLog).filter(
        APICallLog.created_at >= last_hour
    ).count()
    uptime = round((1 - errors_last_hour / max(calls_last_hour, 1)) * 100, 2)

    return {
        "status": "healthy" if uptime > 99 else "degraded" if uptime > 95 else "critical",
        "uptime_percentage": uptime,
        "metrics": {
            "api_calls_today": calls_today,
            "errors_last_hour": errors_last_hour,
            "active_users_24h": active_users,
            "total_users": total_users,
            "avg_response_ms": round(avg_response, 2),
            "p95_response_ms": round(p95_response, 2),
        },
        "timestamp": now.isoformat(),
    }


# ─── User Engagement Analytics ─────────────────────────────────────────────────

def get_user_engagement(
    db: Session,
    user_id: int = None,
    days: int = 30,
) -> Dict[str, Any]:
    """Get user engagement metrics over a time period."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    if user_id:
        # Single user metrics
        calls = db.query(APICallLog).filter(
            APICallLog.user_id == user_id,
            APICallLog.created_at >= start_date,
        ).count()

        features_used = db.query(
            func.count(func.distinct(FeatureUsageEvent.feature))
        ).filter(
            FeatureUsageEvent.user_id == user_id,
            FeatureUsageEvent.created_at >= start_date,
        ).scalar() or 0

        # Active days
        active_days = db.query(
            func.count(func.distinct(func.date(APICallLog.created_at)))
        ).filter(
            APICallLog.user_id == user_id,
            APICallLog.created_at >= start_date,
        ).scalar() or 0

        return {
            "user_id": user_id,
            "period_days": days,
            "total_api_calls": calls,
            "features_used": features_used,
            "active_days": active_days,
            "engagement_rate": round(active_days / max(days, 1) * 100, 1),
        }

    # Platform-wide engagement
    total_users = db.query(User).filter(User.is_active == True).count()
    active_users = db.query(
        func.count(func.distinct(APICallLog.user_id))
    ).filter(
        APICallLog.created_at >= start_date,
    ).scalar() or 0

    return {
        "period_days": days,
        "total_users": total_users,
        "active_users": active_users,
        "activation_rate": round(active_users / max(total_users, 1) * 100, 1),
    }


# ─── Analytics Export ──────────────────────────────────────────────────────────

def export_analytics_report(
    db: Session,
    start_date: datetime = None,
    end_date: datetime = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive analytics report for export.
    Combines API, feature, and engagement data.
    """
    api_data = get_api_analytics(db, start_date=start_date, end_date=end_date)
    feature_data = get_feature_analytics(db, start_date=start_date, end_date=end_date)
    health_data = get_platform_health(db)
    engagement_data = get_user_engagement(db)

    return {
        "report_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform": "CARVanta",
            "version": "5.0",
        },
        "api_analytics": api_data,
        "feature_analytics": feature_data,
        "platform_health": health_data,
        "user_engagement": engagement_data,
    }


# ─── Data Cleanup ──────────────────────────────────────────────────────────────

def cleanup_old_analytics(db: Session) -> Dict[str, Any]:
    """
    Clean up analytics data older than the retention period.
    Should be run as a scheduled task.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=ANALYTICS_RETENTION_DAYS)

    deleted_calls = db.query(APICallLog).filter(
        APICallLog.created_at < cutoff
    ).delete()

    deleted_events = db.query(FeatureUsageEvent).filter(
        FeatureUsageEvent.created_at < cutoff
    ).delete()

    deleted_sessions = db.query(AnalyticsSession).filter(
        AnalyticsSession.started_at < cutoff
    ).delete()

    deleted_metrics = db.query(PlatformMetrics).filter(
        PlatformMetrics.created_at < cutoff
    ).delete()

    db.commit()

    return {
        "cleanup_completed": True,
        "cutoff_date": cutoff.isoformat(),
        "deleted": {
            "api_call_logs": deleted_calls,
            "feature_events": deleted_events,
            "sessions": deleted_sessions,
            "platform_metrics": deleted_metrics,
        },
    }
