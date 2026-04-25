"""
CARVanta Copilot — Chat Handler
==================================
Conversational AI controller that manages multi-turn research
dialogues, intent classification, context threading, and
response orchestration across the copilot sub-engines.

Routes user questions to appropriate backends:
  Literature → RAG Engine
  Protocol → Experiment Designer
  Review → Lit Reviewer
  General → Knowledge Templates

Security: Stateless sessions, input-sanitized, PII-free.
"""

import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("carvanta.copilot.chat_handler")

# ──────────────────────────────────────────────────────────────────────
# Intent Classification
# ──────────────────────────────────────────────────────────────────────

class UserIntent(Enum):
    """Classified user intent categories."""
    LITERATURE_SEARCH = "literature_search"
    TARGET_QUESTION = "target_question"
    SAFETY_QUESTION = "safety_question"
    PROTOCOL_REQUEST = "protocol_request"
    REVIEW_REQUEST = "review_request"
    COMPARISON = "comparison"
    MECHANISM = "mechanism"
    CLINICAL_DATA = "clinical_data"
    MANUFACTURING = "manufacturing"
    GENERAL = "general"
    GREETING = "greeting"
    CLARIFICATION = "clarification"


_INTENT_KEYWORDS: Dict[UserIntent, List[str]] = {
    UserIntent.LITERATURE_SEARCH: ["paper", "study", "publication", "research", "pubmed", "find", "search", "literature", "reference"],
    UserIntent.TARGET_QUESTION: ["target", "antigen", "cd19", "bcma", "her2", "msln", "gpc3", "dll3", "cd22", "cd47", "egfr", "psma"],
    UserIntent.SAFETY_QUESTION: ["toxicity", "crs", "icans", "safety", "adverse", "side effect", "on-target", "off-tumor", "risk"],
    UserIntent.PROTOCOL_REQUEST: ["protocol", "experiment", "design", "how to", "procedure", "method", "assay", "lab"],
    UserIntent.REVIEW_REQUEST: ["review", "summarize", "overview", "comprehensive", "state of the art", "landscape"],
    UserIntent.COMPARISON: ["compare", "versus", "vs", "better", "difference", "advantage"],
    UserIntent.MECHANISM: ["mechanism", "how does", "pathway", "signal", "biology", "why"],
    UserIntent.CLINICAL_DATA: ["clinical", "trial", "patient", "response", "survival", "remission", "fda", "approved"],
    UserIntent.MANUFACTURING: ["manufacturing", "production", "cost", "scale", "gmp", "vector", "lentiviral"],
    UserIntent.GREETING: ["hello", "hi", "hey", "thanks", "thank you", "good morning"],
}


def classify_intent(query: str) -> UserIntent:
    """Classify user intent from query text."""
    q = query.lower().strip()
    scores: Dict[UserIntent, int] = {}
    for intent, keywords in _INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            scores[intent] = score
    if not scores:
        return UserIntent.GENERAL
    return max(scores, key=lambda k: scores[k])


# ──────────────────────────────────────────────────────────────────────
# Conversation State
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ChatMessage:
    """Single chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = 0.0
    intent: Optional[str] = None
    sources_count: int = 0
    confidence: float = 0.0
    message_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
        if not self.message_id:
            self.message_id = str(uuid.uuid4())[:8]


@dataclass
class ChatSession:
    """Multi-turn chat session."""
    session_id: str = ""
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: float = 0.0
    last_active: float = 0.0
    context_targets: List[str] = field(default_factory=list)
    total_queries: int = 0

    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = time.time()
            self.last_active = self.created_at


# Session storage (in-memory)
_SESSIONS: Dict[str, ChatSession] = {}
_MAX_SESSIONS = 100
_MAX_HISTORY = 50


# ──────────────────────────────────────────────────────────────────────
# Response Templates
# ──────────────────────────────────────────────────────────────────────

_GREETING_RESPONSES = [
    "Hello! I'm the CARVanta AI Research Copilot. I can help you with:\n"
    "• 📚 Literature search across 500+ immunotherapy papers\n"
    "• 🎯 Target evaluation and comparison\n"
    "• 🧬 CAR-T design and mechanism questions\n"
    "• 🧪 Experiment protocol suggestions\n"
    "• ⚠️ Safety and toxicity information\n\nWhat would you like to explore?",
    "Hi there! I'm your AI immunotherapy research assistant. Ask me anything about "
    "CAR-T targets, clinical trials, mechanisms, or experimental design.",
]

_CLARIFICATION_PROMPTS = [
    "Could you be more specific? For example:\n"
    "• 'What papers discuss CD19 antigen loss?'\n"
    "• 'Compare 2nd vs 3rd generation CARs'\n"
    "• 'Design a protocol for testing BCMA CAR-T'",
]


# ──────────────────────────────────────────────────────────────────────
# Chat Handler Core
# ──────────────────────────────────────────────────────────────────────

async def create_session() -> ChatSession:
    """Create a new chat session."""
    # Evict oldest sessions if at capacity
    if len(_SESSIONS) >= _MAX_SESSIONS:
        oldest = min(_SESSIONS, key=lambda k: _SESSIONS[k].last_active)
        del _SESSIONS[oldest]

    session = ChatSession()
    _SESSIONS[session.session_id] = session
    logger.info(f"Created chat session {session.session_id}")
    return session


async def get_session(session_id: str) -> Optional[ChatSession]:
    """Retrieve an existing session."""
    return _SESSIONS.get(session_id)


async def handle_message(
    session_id: Optional[str],
    user_message: str,
) -> Dict[str, Any]:
    """
    Process a user message and generate a response.
    Routes to appropriate sub-engine based on intent.
    """
    # Input validation
    user_message = re.sub(r'[<>{}]', '', user_message.strip())
    if len(user_message) > 2000:
        user_message = user_message[:2000]

    if not user_message:
        return {"error": "Empty message", "session_id": session_id}

    # Get or create session
    session = _SESSIONS.get(session_id or "") if session_id else None
    if not session:
        session = await create_session()

    # Classify intent
    intent = classify_intent(user_message)

    # Add user message to history
    user_msg = ChatMessage(role="user", content=user_message, intent=intent.value)
    session.messages.append(user_msg)
    session.total_queries += 1
    session.last_active = time.time()

    # Extract target mentions for context
    target_pattern = re.compile(r'\b(CD19|CD22|BCMA|HER2|EGFR|MSLN|GPC3|DLL3|PSMA|CD47|EpCAM|B7.H3|GPRC5D)\b', re.IGNORECASE)
    mentions = target_pattern.findall(user_message.upper())
    for m in mentions:
        if m not in session.context_targets:
            session.context_targets.append(m)

    # Route to appropriate handler
    response_text = ""
    sources: List[Dict[str, Any]] = []
    confidence = 0.0
    ai_source = "rule_based"

    if intent == UserIntent.GREETING:
        response_text = _GREETING_RESPONSES[0]
        confidence = 1.0

    elif intent == UserIntent.CLARIFICATION:
        response_text = _CLARIFICATION_PROMPTS[0]
        confidence = 1.0

    else:
        # ── Try LLM first for ALL non-trivial intents ──
        from features.llm_insight import generate_copilot_response, is_llm_available

        if is_llm_available():
            # Build context from session history
            history_context = ""
            if session.context_targets:
                history_context += f"Targets discussed: {', '.join(session.context_targets)}\n"
            recent = session.messages[-6:]  # Last 3 exchanges
            if recent:
                history_context += "Recent conversation:\n"
                for m in recent:
                    history_context += f"  {m.role}: {m.content[:200]}\n"

            llm_response = generate_copilot_response(user_message, context=history_context)
            if llm_response:
                response_text = llm_response
                confidence = 0.9
                ai_source = "llm"

        # ── Fallback to built-in handlers if LLM failed ──
        if not response_text:
            if intent in (UserIntent.LITERATURE_SEARCH, UserIntent.TARGET_QUESTION,
                          UserIntent.SAFETY_QUESTION, UserIntent.CLINICAL_DATA,
                          UserIntent.MECHANISM, UserIntent.MANUFACTURING,
                          UserIntent.GENERAL):
                from copilot.rag_engine import generate_rag_answer
                rag_result = await generate_rag_answer(user_message, top_k=5)
                response_text = rag_result.answer
                sources = rag_result.sources
                confidence = rag_result.confidence

            elif intent == UserIntent.REVIEW_REQUEST:
                from copilot.lit_reviewer import generate_mini_review
                target = session.context_targets[-1] if session.context_targets else ""
                review = await generate_mini_review(target or user_message)
                response_text = review.get("review_text", "I'll generate a review on that topic.")
                sources = review.get("sources", [])
                confidence = review.get("confidence", 0.7)

            elif intent == UserIntent.PROTOCOL_REQUEST:
                from copilot.experiment_designer import suggest_protocol
                target = session.context_targets[-1] if session.context_targets else "CD19"
                protocol = await suggest_protocol(target, user_message)
                response_text = protocol.get("protocol_text", "Here's a suggested protocol.")
                confidence = protocol.get("confidence", 0.8)

            elif intent == UserIntent.COMPARISON:
                from copilot.rag_engine import generate_rag_answer
                rag_result = await generate_rag_answer(f"compare {user_message}", top_k=8)
                response_text = rag_result.answer
                sources = rag_result.sources
                confidence = rag_result.confidence

    # Add assistant response to history
    assistant_msg = ChatMessage(
        role="assistant", content=response_text,
        intent=intent.value, sources_count=len(sources),
        confidence=confidence,
    )
    session.messages.append(assistant_msg)

    # Trim history
    if len(session.messages) > _MAX_HISTORY:
        session.messages = session.messages[-_MAX_HISTORY:]

    return {
        "session_id": session.session_id,
        "message_id": assistant_msg.message_id,
        "response": response_text,
        "intent": intent.value,
        "confidence": round(confidence, 3),
        "ai_source": ai_source,
        "sources": sources,
        "context_targets": session.context_targets,
        "total_messages": len(session.messages),
    }


async def get_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """Get chat history for a session."""
    session = _SESSIONS.get(session_id)
    if not session:
        return []
    return [
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp,
            "intent": m.intent,
            "message_id": m.message_id,
        }
        for m in session.messages
    ]


async def get_session_stats() -> Dict[str, Any]:
    """Get aggregate session statistics."""
    total_msgs = sum(len(s.messages) for s in _SESSIONS.values())
    return {
        "active_sessions": len(_SESSIONS),
        "total_messages": total_msgs,
        "max_sessions": _MAX_SESSIONS,
    }
