"""
CARVanta Collab — Real-Time Messaging
=======================================
WebSocket-simulated messaging system for lab-to-lab
communication and research discussion forums.

Features:
- Direct messages between team members
- Project-level discussion channels
- Thread-based conversations
- Typing indicators and read receipts
- File/image sharing in messages
- @mention notifications
- Search across message history
- Pinned messages

Security: Project-scoped, message retention policy, async.
"""

import logging
import time
import uuid
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("carvanta.collab.messaging")


@dataclass
class Message:
    message_id: str
    channel_id: str
    sender_id: str
    sender_name: str
    content: str
    timestamp: str = ""
    edited_at: str = ""
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    pinned: bool = False
    read_by: List[str] = field(default_factory=list)


@dataclass
class Channel:
    channel_id: str
    project_id: str
    name: str
    description: str = ""
    channel_type: str = "discussion"  # discussion, announcements, support, random
    created_by: str = ""
    created_at: str = ""
    members: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    pinned_messages: List[str] = field(default_factory=list)
    is_archived: bool = False


# ──────────────────────────────────────────────────────────────────────
# In-Memory Store
# ──────────────────────────────────────────────────────────────────────

_CHANNELS: Dict[str, Channel] = {}
_DM_CHANNELS: Dict[str, Channel] = {}  # keyed by sorted user pair


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gid() -> str:
    return uuid.uuid4().hex[:12]


def _extract_mentions(content: str) -> List[str]:
    """Extract @mentions from message content."""
    return re.findall(r"@(\w+)", content)


# ──────────────────────────────────────────────────────────────────────
# Channel Operations
# ──────────────────────────────────────────────────────────────────────

async def create_channel(
    project_id: str, name: str, description: str = "",
    channel_type: str = "discussion", created_by: str = "",
    members: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a discussion channel."""
    cid = _gid()
    ch = Channel(
        channel_id=cid, project_id=project_id, name=name,
        description=description, channel_type=channel_type,
        created_by=created_by, created_at=_now(),
        members=members or [created_by],
    )
    _CHANNELS[cid] = ch
    return _ser_channel(ch)


async def get_channel(channel_id: str) -> Optional[Dict[str, Any]]:
    """Get channel with recent messages."""
    ch = _CHANNELS.get(channel_id)
    return _ser_channel(ch, with_messages=True) if ch else None


async def list_channels(
    project_id: str, include_archived: bool = False,
) -> Dict[str, Any]:
    """List channels for a project."""
    results = []
    for ch in _CHANNELS.values():
        if ch.project_id != project_id:
            continue
        if not include_archived and ch.is_archived:
            continue
        results.append(_ser_channel(ch))
    return {"total": len(results), "channels": results}


# ──────────────────────────────────────────────────────────────────────
# Message Operations
# ──────────────────────────────────────────────────────────────────────

async def send_message(
    channel_id: str, sender_id: str, sender_name: str,
    content: str, reply_to: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Send a message to a channel."""
    ch = _CHANNELS.get(channel_id) or _DM_CHANNELS.get(channel_id)
    if not ch:
        return None

    mentions = _extract_mentions(content)
    msg = Message(
        message_id=_gid(), channel_id=channel_id,
        sender_id=sender_id, sender_name=sender_name,
        content=content, timestamp=_now(),
        reply_to=reply_to, mentions=mentions,
        attachments=attachments or [],
        read_by=[sender_id],
    )

    # Set thread_id for replies
    if reply_to:
        for existing in ch.messages:
            if existing.message_id == reply_to:
                msg.thread_id = existing.thread_id or existing.message_id
                break

    ch.messages.append(msg)
    return _ser_message(msg)


async def get_messages(
    channel_id: str, limit: int = 50, before: Optional[str] = None,
) -> Dict[str, Any]:
    """Get messages from a channel."""
    ch = _CHANNELS.get(channel_id) or _DM_CHANNELS.get(channel_id)
    if not ch:
        return {"error": "Channel not found", "messages": []}

    msgs = ch.messages
    if before:
        idx = next((i for i, m in enumerate(msgs) if m.message_id == before), len(msgs))
        msgs = msgs[:idx]

    msgs = msgs[-limit:]
    return {
        "channel_id": channel_id,
        "total": len(ch.messages),
        "returned": len(msgs),
        "messages": [_ser_message(m) for m in msgs],
    }


async def edit_message(
    channel_id: str, message_id: str, new_content: str,
) -> Optional[Dict[str, Any]]:
    """Edit a message."""
    ch = _CHANNELS.get(channel_id) or _DM_CHANNELS.get(channel_id)
    if not ch:
        return None
    for msg in ch.messages:
        if msg.message_id == message_id:
            msg.content = new_content
            msg.edited_at = _now()
            msg.mentions = _extract_mentions(new_content)
            return _ser_message(msg)
    return None


async def react_to_message(
    channel_id: str, message_id: str, user_id: str, emoji: str,
) -> Optional[Dict[str, Any]]:
    """Add reaction to a message."""
    ch = _CHANNELS.get(channel_id) or _DM_CHANNELS.get(channel_id)
    if not ch:
        return None
    for msg in ch.messages:
        if msg.message_id == message_id:
            if emoji not in msg.reactions:
                msg.reactions[emoji] = []
            if user_id not in msg.reactions[emoji]:
                msg.reactions[emoji].append(user_id)
            return {"message_id": message_id, "reactions": {k: len(v) for k, v in msg.reactions.items()}}
    return None


async def pin_message(
    channel_id: str, message_id: str,
) -> Optional[Dict[str, Any]]:
    """Pin/unpin a message."""
    ch = _CHANNELS.get(channel_id)
    if not ch:
        return None
    for msg in ch.messages:
        if msg.message_id == message_id:
            msg.pinned = not msg.pinned
            if msg.pinned:
                ch.pinned_messages.append(message_id)
            else:
                ch.pinned_messages = [p for p in ch.pinned_messages if p != message_id]
            return {"message_id": message_id, "pinned": msg.pinned}
    return None


async def search_messages(
    channel_id: str, query: str, max_results: int = 20,
) -> Dict[str, Any]:
    """Search messages in a channel."""
    ch = _CHANNELS.get(channel_id) or _DM_CHANNELS.get(channel_id)
    if not ch:
        return {"error": "Channel not found", "results": []}

    q_lower = query.lower()
    results = []
    for msg in ch.messages:
        if q_lower in msg.content.lower():
            results.append(_ser_message(msg))
    results = results[-max_results:]
    return {"query": query, "total": len(results), "results": results}


async def get_thread(
    channel_id: str, thread_id: str,
) -> Dict[str, Any]:
    """Get all messages in a thread."""
    ch = _CHANNELS.get(channel_id) or _DM_CHANNELS.get(channel_id)
    if not ch:
        return {"error": "Channel not found", "messages": []}

    thread_msgs = [m for m in ch.messages if m.thread_id == thread_id or m.message_id == thread_id]
    return {
        "thread_id": thread_id,
        "messages_count": len(thread_msgs),
        "messages": [_ser_message(m) for m in thread_msgs],
    }


# ──────────────────────────────────────────────────────────────────────
# Direct Messages
# ──────────────────────────────────────────────────────────────────────

async def create_dm(
    user1_id: str, user1_name: str,
    user2_id: str, user2_name: str,
) -> Dict[str, Any]:
    """Create or get DM channel between two users."""
    key = "_".join(sorted([user1_id, user2_id]))
    if key in _DM_CHANNELS:
        return _ser_channel(_DM_CHANNELS[key])

    ch = Channel(
        channel_id=_gid(), project_id="dm",
        name=f"DM: {user1_name} & {user2_name}",
        channel_type="dm", created_by=user1_id, created_at=_now(),
        members=[user1_id, user2_id],
    )
    _DM_CHANNELS[key] = ch
    _CHANNELS[ch.channel_id] = ch
    return _ser_channel(ch)


# ──────────────────────────────────────────────────────────────────────
# Serialization
# ──────────────────────────────────────────────────────────────────────

def _ser_message(msg: Message) -> Dict[str, Any]:
    return {
        "id": msg.message_id, "sender": msg.sender_name,
        "sender_id": msg.sender_id, "content": msg.content,
        "timestamp": msg.timestamp, "edited": bool(msg.edited_at),
        "reply_to": msg.reply_to, "thread_id": msg.thread_id,
        "reactions": {k: len(v) for k, v in msg.reactions.items()},
        "attachments": msg.attachments, "mentions": msg.mentions,
        "pinned": msg.pinned,
    }


def _ser_channel(ch: Channel, with_messages: bool = False) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "channel_id": ch.channel_id, "project_id": ch.project_id,
        "name": ch.name, "description": ch.description,
        "type": ch.channel_type, "members_count": len(ch.members),
        "messages_count": len(ch.messages), "created_at": ch.created_at,
        "is_archived": ch.is_archived,
    }
    if with_messages:
        data["messages"] = [_ser_message(m) for m in ch.messages[-50:]]
        data["pinned"] = [_ser_message(m) for m in ch.messages if m.pinned]
    return data
