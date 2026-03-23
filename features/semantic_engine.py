"""
CARVanta — Semantic Query Engine
=================================
AI-powered query understanding using sentence-transformers.
Replaces hardcoded keyword matching with ML-based intent classification,
fuzzy cancer type matching, and intelligent entity extraction.

Uses `all-MiniLM-L6-v2` (~80MB, runs locally, no API keys).

Usage:
    from features.semantic_engine import get_engine
    engine = get_engine()
    result = engine.understand("which antigens should I avoid for brain tumors")
    # -> {intent: "worst", cancer_type: "Glioblastoma", sort_ascending: True, ...}
"""

import re
import logging
from difflib import get_close_matches
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_ENGINE_INSTANCE: Optional["SemanticQueryEngine"] = None


def get_engine() -> "SemanticQueryEngine":
    """Return a singleton SemanticQueryEngine (lazy-loaded on first call)."""
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = SemanticQueryEngine()
    return _ENGINE_INSTANCE


class SemanticQueryEngine:
    """
    3-tier AI query understanding engine:
      Tier 1: Semantic intent classification via cosine similarity
      Tier 2: Fuzzy entity extraction (cancer type, limit, tier, antigen names)
      Tier 3: Sort direction inference from embedding similarity
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        from features.intent_training_data import (
            INTENT_TRAINING_DATA,
            CANCER_REFERENCE_PHRASES,
            ASCENDING_PHRASES,
            DESCENDING_PHRASES,
        )

        self.is_available = False
        self._model = None
        self._intent_embeddings = None   # (N, 384) matrix
        self._intent_labels: list[str] = []
        self._cancer_embeddings: dict[str, np.ndarray] = {}
        self._cancer_names: list[str] = []
        self._asc_embedding = None
        self._desc_embedding = None

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading semantic model: %s", self.MODEL_NAME)
            self._model = SentenceTransformer(self.MODEL_NAME)

            # ── Pre-compute intent reference embeddings ───────────────────
            intent_texts = [t[0] for t in INTENT_TRAINING_DATA]
            self._intent_labels = [t[1] for t in INTENT_TRAINING_DATA]
            self._intent_embeddings = self._model.encode(
                intent_texts, convert_to_numpy=True, normalize_embeddings=True
            )

            # ── Pre-compute cancer type embeddings ────────────────────────
            self._cancer_phrase_map: dict[str, str] = {}
            all_cancer_phrases = []
            for cancer_name, phrases in CANCER_REFERENCE_PHRASES.items():
                self._cancer_names.append(cancer_name)
                for phrase in phrases:
                    self._cancer_phrase_map[phrase] = cancer_name
                    all_cancer_phrases.append(phrase)

            self._cancer_phrase_list = all_cancer_phrases
            self._cancer_phrase_embeddings = self._model.encode(
                all_cancer_phrases, convert_to_numpy=True, normalize_embeddings=True
            )

            # ── Pre-compute sort direction embeddings ─────────────────────
            self._asc_embedding = self._model.encode(
                ASCENDING_PHRASES, convert_to_numpy=True, normalize_embeddings=True
            ).mean(axis=0)
            self._desc_embedding = self._model.encode(
                DESCENDING_PHRASES, convert_to_numpy=True, normalize_embeddings=True
            ).mean(axis=0)

            self.is_available = True
            logger.info(
                "Semantic engine ready: %d intent refs, %d cancer phrases",
                len(intent_texts),
                len(all_cancer_phrases),
            )

        except Exception as e:
            logger.warning("Semantic engine unavailable: %s — falling back to keywords", e)
            self.is_available = False

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def understand(self, query: str) -> dict:
        """
        Understand a natural language query and return structured parameters.

        Returns
        -------
        dict with:
            intent: str           — best, worst, filter_cancer, filter_safety, ...
            intent_confidence: float
            cancer_type: str|None
            cancer_confidence: float|None
            sort_ascending: bool
            limit: int|None
            tier_filter: int|None
            safety_preference: str|None
            antigen_mentions: list[str]
            method: str           — "semantic" or "keyword_fallback"
        """
        if not self.is_available or self._model is None:
            return self._keyword_fallback(query)

        q_embedding = self._model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        )[0]

        # Tier 1: Intent classification
        intent, intent_conf = self._classify_intent(q_embedding)

        # Tier 2: Entity extraction
        cancer_type, cancer_conf = self._extract_cancer(query, q_embedding)
        limit = self._extract_limit(query)
        tier_filter = self._extract_tier(query)
        safety_pref = self._extract_safety(query, intent)
        antigen_mentions = self._extract_antigens(query)

        # Tier 3: Sort direction
        sort_ascending = self._infer_sort_direction(q_embedding, intent)

        return {
            "intent": intent,
            "intent_confidence": round(float(intent_conf), 3),
            "cancer_type": cancer_type,
            "cancer_confidence": round(float(cancer_conf), 3) if cancer_conf else None,
            "sort_ascending": sort_ascending,
            "limit": limit,
            "tier_filter": tier_filter,
            "safety_preference": safety_pref,
            "antigen_mentions": antigen_mentions,
            "method": "semantic",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Tier 1: Intent Classification
    # ─────────────────────────────────────────────────────────────────────────

    def _classify_intent(self, q_embedding: np.ndarray) -> tuple[str, float]:
        """Classify query intent via cosine similarity to reference embeddings."""
        similarities = q_embedding @ self._intent_embeddings.T  # (N,)

        # Get top-k matches and vote by label
        top_k = 5
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Weighted voting: each match votes with its similarity score
        label_scores: dict[str, float] = {}
        for idx in top_indices:
            label = self._intent_labels[idx]
            label_scores[label] = label_scores.get(label, 0) + similarities[idx]

        best_label = max(label_scores, key=label_scores.get)
        best_score = similarities[top_indices[0]]  # highest individual similarity

        return best_label, best_score

    # ─────────────────────────────────────────────────────────────────────────
    # Tier 2: Entity Extraction
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_cancer(
        self, query: str, q_embedding: np.ndarray
    ) -> tuple[Optional[str], Optional[float]]:
        """Extract cancer type via embedding similarity + fuzzy string matching."""
        q_lower = query.lower()

        # First: try exact/fuzzy substring match (fast)
        for phrase, cancer_name in self._cancer_phrase_map.items():
            if phrase in q_lower:
                return cancer_name, 0.99

        # Second: semantic similarity against cancer phrases
        similarities = q_embedding @ self._cancer_phrase_embeddings.T
        best_idx = int(np.argmax(similarities))
        best_sim = float(similarities[best_idx])

        if best_sim > 0.55:  # threshold for semantic cancer match
            matched_phrase = self._cancer_phrase_list[best_idx]
            cancer_name = self._cancer_phrase_map[matched_phrase]
            return cancer_name, best_sim

        return None, None

    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract result limit from query text."""
        q_lower = query.lower()

        # "top 10", "first 5", "show 20", "limit 50"
        patterns = [
            r"top\s+(\d+)", r"first\s+(\d+)", r"show\s+(\d+)",
            r"limit\s+(\d+)", r"(\d+)\s+results?", r"(\d+)\s+antigens?",
            r"(\d+)\s+targets?",
        ]
        for pattern in patterns:
            m = re.search(pattern, q_lower)
            if m:
                return min(int(m.group(1)), 200)

        return None

    def _extract_tier(self, query: str) -> Optional[int]:
        """Extract tier filter from query text."""
        q_lower = query.lower()
        tier_patterns = [
            (r"tier\s*1", 1), (r"tier\s*2", 2),
            (r"tier\s*3", 3), (r"tier\s*4", 4),
            (r"highly\s+viable", 1), (r"promising", 2),
        ]
        for pattern, tier in tier_patterns:
            if re.search(pattern, q_lower):
                return tier
        return None

    def _extract_safety(self, query: str, intent: str) -> Optional[str]:
        """Extract safety preference from query text."""
        q_lower = query.lower()
        safe_indicators = [
            "safe", "low toxicity", "non-toxic", "minimal risk",
            "good safety", "no side effect", "low off-target",
            "spare normal", "therapeutic index",
        ]
        for indicator in safe_indicators:
            if indicator in q_lower:
                return "low"

        if intent == "filter_safety":
            return "low"

        return None

    def _extract_antigens(self, query: str) -> list[str]:
        """Extract specific antigen names mentioned in the query."""
        # Common CAR-T antigen patterns
        antigen_pattern = r'\b(CD\d+\w*|BCMA|HER2|EGFR|EGFRvIII|GD2|MESOTHELIN|PSMA|GPC3|FLT3|EPCAM|MUC1|DLL3|ROR1|MET|NECTIN4|CLEC12A|SLAMF7|WT1|NKG2D)\b'
        matches = re.findall(antigen_pattern, query, re.IGNORECASE)
        return [m.upper() for m in matches]

    # ─────────────────────────────────────────────────────────────────────────
    # Tier 3: Sort Direction Inference
    # ─────────────────────────────────────────────────────────────────────────

    def _infer_sort_direction(self, q_embedding: np.ndarray, intent: str) -> bool:
        """
        Infer sort direction via semantic similarity to ascending/descending phrases.
        Returns True for ascending (worst first), False for descending (best first).
        """
        # Intent-based shortcut
        if intent == "worst":
            return True
        if intent in ("best", "filter_safety"):
            return False

        # Semantic comparison
        asc_sim = float(np.dot(q_embedding, self._asc_embedding))
        desc_sim = float(np.dot(q_embedding, self._desc_embedding))

        # Need meaningful difference to flip from default (descending)
        if asc_sim > desc_sim + 0.05:
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Fallback: keyword-based parsing (when model unavailable)
    # ─────────────────────────────────────────────────────────────────────────

    def _keyword_fallback(self, query: str) -> dict:
        """Simple keyword-based fallback when the ML model is not available."""
        q = query.lower()
        from features.intent_training_data import (
            CANCER_REFERENCE_PHRASES,
            ASCENDING_PHRASES,
            DESCENDING_PHRASES,
        )

        # Detect cancer
        cancer_type = None
        for cancer_name, phrases in CANCER_REFERENCE_PHRASES.items():
            for phrase in phrases:
                if phrase in q:
                    cancer_type = cancer_name
                    break
            if cancer_type:
                break

        # Detect sort direction
        sort_ascending = any(kw in q for kw in ASCENDING_PHRASES)

        # Detect intent
        intent = "general"
        if sort_ascending:
            intent = "worst"
        elif any(kw in q for kw in DESCENDING_PHRASES):
            intent = "best"
        elif cancer_type:
            intent = "filter_cancer"

        return {
            "intent": intent,
            "intent_confidence": 0.5,
            "cancer_type": cancer_type,
            "cancer_confidence": 0.9 if cancer_type else None,
            "sort_ascending": sort_ascending,
            "limit": self._extract_limit(query),
            "tier_filter": self._extract_tier(query),
            "safety_preference": self._extract_safety(query, intent),
            "antigen_mentions": self._extract_antigens(query),
            "method": "keyword_fallback",
        }
