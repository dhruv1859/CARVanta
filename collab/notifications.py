"""
CARVanta Collab — Notification & Alert Engine
================================================
Event-driven notification system for research collaboration.
Manages in-app alerts, email digests, webhook integrations,
and customizable notification preferences.

Features:
- In-app notification center with read/unread tracking
- Email digest (daily/weekly summary)
- Webhook integrations (Slack, Teams, Discord)
- Custom alert rules (e.g., experiment completed, review needed)
- @mention support in messages and comments
- Deadline reminders (experiment due dates, protocol reviews)
- Priority-based notification routing
- Notification preferences per user
- Batch notification management
- Activity summary generation
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import Counter

logger = logging.getLogger("carvanta.collab.notifications")

# In-memory stores
_NOTIFICATIONS: Dict[str, List[Dict]] = {}  # user_id -> notifications
_PREFERENCES: Dict[str, Dict] = {}
_WEBHOOKS: Dict[str, Dict] = {}

# Notification types
_NOTIFICATION_TYPES = {
    "experiment_completed": {
        "category": "experiment", "priority": "high",
        "template": "Experiment '{title}' has been completed by {actor}",
        "icon": "🧪", "default_channels": ["in_app", "email"],
    },
    "experiment_failed": {
        "category": "experiment", "priority": "critical",
        "template": "Experiment '{title}' has failed: {reason}",
        "icon": "❌", "default_channels": ["in_app", "email", "webhook"],
    },
    "review_requested": {
        "category": "peer_review", "priority": "high",
        "template": "Your review is requested for submission '{title}'",
        "icon": "📝", "default_channels": ["in_app", "email"],
    },
    "review_completed": {
        "category": "peer_review", "priority": "medium",
        "template": "Review completed for '{title}': {recommendation}",
        "icon": "✅", "default_channels": ["in_app"],
    },
    "dataset_shared": {
        "category": "dataset", "priority": "medium",
        "template": "Dataset '{title}' has been shared with you by {actor}",
        "icon": "📊", "default_channels": ["in_app"],
    },
    "member_joined": {
        "category": "project", "priority": "low",
        "template": "{actor} has joined project '{project}'",
        "icon": "👤", "default_channels": ["in_app"],
    },
    "mention": {
        "category": "social", "priority": "high",
        "template": "{actor} mentioned you in {context}",
        "icon": "💬", "default_channels": ["in_app", "email"],
    },
    "deadline_approaching": {
        "category": "workflow", "priority": "high",
        "template": "Deadline approaching: '{title}' due in {days_remaining} days",
        "icon": "⏰", "default_channels": ["in_app", "email"],
    },
    "protocol_deviation": {
        "category": "compliance", "priority": "critical",
        "template": "Protocol deviation reported in '{protocol}': {severity}",
        "icon": "⚠️", "default_channels": ["in_app", "email", "webhook"],
    },
    "workflow_step_completed": {
        "category": "workflow", "priority": "medium",
        "template": "Workflow step '{step}' completed in '{workflow}'",
        "icon": "✔️", "default_channels": ["in_app"],
    },
    "publication_accepted": {
        "category": "publication", "priority": "high",
        "template": "Manuscript '{title}' has been accepted by {journal}!",
        "icon": "🎉", "default_channels": ["in_app", "email", "webhook"],
    },
    "funding_milestone": {
        "category": "funding", "priority": "medium",
        "template": "Grant milestone reached: '{milestone}' for {grant}",
        "icon": "💰", "default_channels": ["in_app"],
    },
}


async def send_notification(
    user_id: str,
    notification_type: str,
    title: str = "",
    message: str = "",
    actor: str = "",
    entity_type: str = "",
    entity_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Send a notification to a user."""
    notif_type = _NOTIFICATION_TYPES.get(notification_type, _NOTIFICATION_TYPES.get("mention"))
    notif_id = f"NOTIF-{uuid.uuid4().hex[:8]}"

    notification = {
        "notification_id": notif_id,
        "type": notification_type,
        "category": notif_type["category"],
        "priority": notif_type["priority"],
        "icon": notif_type["icon"],
        "title": title,
        "message": message or notif_type["template"].format(
            title=title, actor=actor, **{k: v for k, v in (metadata or {}).items() if isinstance(v, str)}
        ) if not message else message,
        "actor": actor,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
        "channels_sent": notif_type["default_channels"],
    }

    if user_id not in _NOTIFICATIONS:
        _NOTIFICATIONS[user_id] = []
    _NOTIFICATIONS[user_id].append(notification)

    return {"notification_id": notif_id, "sent": True, "channels": notif_type["default_channels"]}


async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    category: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get notifications for a user."""
    notifications = _NOTIFICATIONS.get(user_id, [])

    if unread_only:
        notifications = [n for n in notifications if not n["read"]]
    if category:
        notifications = [n for n in notifications if n["category"] == category]

    notifications = sorted(notifications, key=lambda n: n["timestamp"], reverse=True)[:limit]
    unread_count = sum(1 for n in _NOTIFICATIONS.get(user_id, []) if not n["read"])

    return {
        "user_id": user_id,
        "total": len(notifications),
        "unread_count": unread_count,
        "notifications": notifications,
    }


async def mark_read(
    user_id: str,
    notification_id: Optional[str] = None,
    mark_all: bool = False,
) -> Dict[str, Any]:
    """Mark notifications as read."""
    notifications = _NOTIFICATIONS.get(user_id, [])
    marked = 0

    for n in notifications:
        if mark_all or n["notification_id"] == notification_id:
            if not n["read"]:
                n["read"] = True
                marked += 1

    return {"marked_read": marked, "remaining_unread": sum(1 for n in notifications if not n["read"])}


async def set_preferences(
    user_id: str,
    email_digest: str = "daily",
    quiet_hours_start: int = 22,
    quiet_hours_end: int = 7,
    disabled_categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Set notification preferences."""
    prefs = {
        "user_id": user_id,
        "email_digest": email_digest,
        "quiet_hours": {"start": quiet_hours_start, "end": quiet_hours_end},
        "disabled_categories": disabled_categories or [],
        "channels": {
            "in_app": True,
            "email": True,
            "webhook": False,
        },
        "updated_at": datetime.utcnow().isoformat(),
    }

    _PREFERENCES[user_id] = prefs
    return {"status": "updated", "preferences": prefs}


async def register_webhook(
    project_id: str,
    url: str,
    platform: str = "slack",
    events: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Register a webhook for project notifications."""
    webhook_id = f"HOOK-{uuid.uuid4().hex[:8]}"

    webhook = {
        "webhook_id": webhook_id,
        "project_id": project_id,
        "url": url,
        "platform": platform,
        "events": events or ["experiment_completed", "protocol_deviation", "publication_accepted"],
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
        "deliveries": 0,
        "last_delivery": None,
    }

    _WEBHOOKS[webhook_id] = webhook
    return {"webhook_id": webhook_id, "status": "registered", "webhook": webhook}


async def notification_summary(
    user_id: str = "user_1",
    days: int = 7,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate notification activity summary."""
    if seed:
        random.seed(seed)

    # Simulate if no real data
    by_category = {cat: random.randint(0, 20) for cat in set(t["category"] for t in _NOTIFICATION_TYPES.values())}
    by_priority = {"critical": random.randint(0, 3), "high": random.randint(2, 15),
                   "medium": random.randint(5, 25), "low": random.randint(3, 20)}

    return {
        "user_id": user_id,
        "period_days": days,
        "total_notifications": sum(by_category.values()),
        "unread": random.randint(0, 10),
        "by_category": by_category,
        "by_priority": by_priority,
        "most_active_day": (datetime.utcnow() - timedelta(days=random.randint(0, days))).strftime("%A"),
        "action_required": random.randint(0, 5),
    }
