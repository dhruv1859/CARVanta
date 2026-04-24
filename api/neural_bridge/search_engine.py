"""
CARVanta Neural Bridge — Full-Text Search Engine
==================================================
Provides ranked, fuzzy-capable search across all entities in the
knowledge graph: antigens, diseases, pathways, and their relationships.

Features:
  - TF-IDF–style term scoring with BM25-inspired ranking
  - Trigram fuzzy matching for typo tolerance
  - Faceted search (filter by group, layer, score range)
  - Auto-complete / suggestion mode (prefix matching)
  - Search result highlighting
  - Related-entity expansion (show neighbours of matched nodes)
  - Search analytics (popular queries, zero-result queries)
"""

from __future__ import annotations

import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── Configuration ───────────────────────────────────────────────────────────

BM25_K1 = 1.5
BM25_B = 0.75
TRIGRAM_THRESHOLD = 0.30     # Minimum trigram similarity for fuzzy match
MAX_SUGGESTIONS = 15
MAX_SEARCH_RESULTS = 100


# ─── Data Structures ────────────────────────────────────────────────────────

@dataclass
class SearchHit:
    """A single search result."""
    node_id: str
    name: str
    group: str
    layer: str
    score: float       # BM25/relevance score
    highlights: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "group": self.group,
            "layer": self.layer,
            "relevance_score": round(self.score, 4),
            "highlights": self.highlights,
            **self.metadata,
        }


@dataclass
class SearchResult:
    """Complete search response."""
    query: str
    total_hits: int
    hits: List[SearchHit]
    facets: Dict[str, Dict[str, int]]
    took_ms: float
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_hits": self.total_hits,
            "hits": [h.to_dict() for h in self.hits],
            "facets": self.facets,
            "took_ms": round(self.took_ms, 2),
            "suggestions": self.suggestions,
        }


# ─── Trigram Similarity ─────────────────────────────────────────────────────

def _trigrams(text: str) -> Set[str]:
    """Generate character trigrams for fuzzy matching."""
    padded = f"  {text.lower()}  "
    return {padded[i:i + 3] for i in range(len(padded) - 2)}


def _trigram_similarity(a: str, b: str) -> float:
    """Jaccard similarity of trigram sets."""
    ta, tb = _trigrams(a), _trigrams(b)
    if not ta or not tb:
        return 0.0
    intersection = len(ta & tb)
    union = len(ta | tb)
    return intersection / union if union else 0.0


# ─── Tokeniser ──────────────────────────────────────────────────────────────

_SPLIT_RE = re.compile(r"[\s\-_/\(\),;:]+")

def _tokenise(text: str) -> List[str]:
    """Lowercase tokenisation with special-character splitting."""
    return [t for t in _SPLIT_RE.split(text.lower()) if len(t) >= 2]


# ─── Inverted Index ─────────────────────────────────────────────────────────

class InvertedIndex:
    """
    Memory-efficient inverted index for BM25-style ranked retrieval.
    """

    def __init__(self):
        # term → {doc_id: term_frequency}
        self._postings: Dict[str, Dict[str, int]] = defaultdict(dict)
        # doc_id → document length (in tokens)
        self._doc_len: Dict[str, int] = {}
        # doc_id → original node dict
        self._docs: Dict[str, Dict[str, Any]] = {}
        self._avg_dl: float = 0.0
        self._n_docs: int = 0

    def add_document(self, doc_id: str, text: str, node: Dict[str, Any]):
        """Index a single node."""
        tokens = _tokenise(text)
        self._doc_len[doc_id] = len(tokens)
        self._docs[doc_id] = node

        tf: Dict[str, int] = defaultdict(int)
        for t in tokens:
            tf[t] += 1

        for term, count in tf.items():
            self._postings[term][doc_id] = count

    def finalise(self):
        """Compute average document length (call after all adds)."""
        self._n_docs = len(self._doc_len)
        total = sum(self._doc_len.values())
        self._avg_dl = total / max(self._n_docs, 1)

    def bm25_score(self, query_tokens: List[str], doc_id: str) -> float:
        """Compute BM25 score for a document against query tokens."""
        score = 0.0
        dl = self._doc_len.get(doc_id, 0)
        for qt in query_tokens:
            posting = self._postings.get(qt, {})
            if doc_id not in posting:
                continue
            tf = posting[doc_id]
            df = len(posting)
            idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (BM25_K1 + 1)
            denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / max(self._avg_dl, 1))
            score += idf * (numerator / denominator)
        return score

    def search(
        self,
        query_tokens: List[str],
        limit: int = MAX_SEARCH_RESULTS,
    ) -> List[Tuple[str, float]]:
        """Return (doc_id, score) list sorted by relevance."""
        # Collect candidate docs (any doc matching at least one token)
        candidates: Set[str] = set()
        for qt in query_tokens:
            candidates |= set(self._postings.get(qt, {}).keys())

        scored = [(did, self.bm25_score(query_tokens, did)) for did in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    @property
    def terms(self) -> Set[str]:
        return set(self._postings.keys())


# ─── Search Engine ───────────────────────────────────────────────────────────

class GraphSearchEngine:
    """
    Full-text search over the knowledge graph with BM25 ranking,
    fuzzy matching, faceted filtering, and auto-complete.
    """

    def __init__(self):
        self._index = InvertedIndex()
        self._name_lookup: Dict[str, str] = {}   # lowercase name → node_id
        self._all_names: List[str] = []
        self._query_log: List[Dict[str, Any]] = []
        self._indexed = False

    # ── Indexing ────────────────────────────────────────────────────────

    def build_index(self, nodes: List[Dict[str, Any]]):
        """Build the search index from graph nodes."""
        self._index = InvertedIndex()
        self._name_lookup = {}
        self._all_names = []

        for node in nodes:
            nid = node.get("id", "")
            name = node.get("name", "")
            group = node.get("group", "")
            layer = node.get("layer", "")

            # Searchable text combines name, group, and layer
            text = f"{name} {group} {layer} {nid}"
            self._index.add_document(nid, text, node)

            ln = name.lower()
            self._name_lookup[ln] = nid
            self._all_names.append(name)

        self._index.finalise()
        self._indexed = True

    # ── Main Search ─────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        group_filter: Optional[str] = None,
        layer_filter: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 50,
        fuzzy: bool = True,
    ) -> SearchResult:
        """
        Execute a ranked search with optional filters and fuzzy matching.
        """
        start = time.perf_counter()

        if not self._indexed:
            return SearchResult(
                query=query, total_hits=0, hits=[], facets={},
                took_ms=0, suggestions=["Index not built yet"],
            )

        query_tokens = _tokenise(query)
        if not query_tokens:
            return SearchResult(query=query, total_hits=0, hits=[], facets={}, took_ms=0)

        # BM25 search
        raw_hits = self._index.search(query_tokens, limit=limit * 3)  # over-fetch for filtering

        # Fuzzy expansion: if few hits, try trigram matching
        if fuzzy and len(raw_hits) < 5:
            fuzzy_additions = self._fuzzy_expand(query, limit=20)
            existing_ids = {h[0] for h in raw_hits}
            for fid, fscore in fuzzy_additions:
                if fid not in existing_ids:
                    raw_hits.append((fid, fscore * 0.7))  # discount fuzzy matches

        # Build SearchHit objects with filtering
        hits: List[SearchHit] = []
        facets_group: Dict[str, int] = defaultdict(int)
        facets_layer: Dict[str, int] = defaultdict(int)

        for doc_id, score in raw_hits:
            node = self._index._docs.get(doc_id, {})
            grp = node.get("group", "Unknown")
            lyr = node.get("layer", "unknown")
            node_score = node.get("score", 0.5)

            # Apply filters
            if group_filter and grp.lower() != group_filter.lower():
                continue
            if layer_filter and lyr.lower() != layer_filter.lower():
                continue
            if min_score is not None and node_score < min_score:
                continue

            # Build highlights
            name = node.get("name", "")
            highlights = []
            for qt in query_tokens:
                if qt in name.lower():
                    highlights.append(f"Matched '{qt}' in name")

            hits.append(SearchHit(
                node_id=doc_id,
                name=name,
                group=grp,
                layer=lyr,
                score=score,
                highlights=highlights,
                metadata={"cvs_score": round(node_score, 3), "val": node.get("val", 5)},
            ))

            facets_group[grp] += 1
            facets_layer[lyr] += 1

        # Sort by score and limit
        hits.sort(key=lambda h: h.score, reverse=True)
        total = len(hits)
        hits = hits[:limit]

        elapsed = (time.perf_counter() - start) * 1000

        # Log query
        self._query_log.append({
            "query": query,
            "hits": total,
            "took_ms": round(elapsed, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(self._query_log) > 500:
            self._query_log = self._query_log[-500:]

        return SearchResult(
            query=query,
            total_hits=total,
            hits=hits,
            facets={"group": dict(facets_group), "layer": dict(facets_layer)},
            took_ms=elapsed,
            suggestions=self.suggest(query, limit=5) if total < 3 else [],
        )

    # ── Fuzzy Expand ────────────────────────────────────────────────────

    def _fuzzy_expand(self, query: str, limit: int = 20) -> List[Tuple[str, float]]:
        """Find nodes whose names are similar to the query via trigrams."""
        results = []
        for name, nid in self._name_lookup.items():
            sim = _trigram_similarity(query, name)
            if sim >= TRIGRAM_THRESHOLD:
                results.append((nid, sim))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    # ── Auto-Complete / Suggestions ─────────────────────────────────────

    def suggest(self, prefix: str, limit: int = MAX_SUGGESTIONS) -> List[str]:
        """Return node names matching a prefix (for auto-complete)."""
        p = prefix.lower()
        matches = [n for n in self._all_names if n.lower().startswith(p)]
        if len(matches) < limit:
            # Fallback: substring match
            matches.extend(
                n for n in self._all_names
                if p in n.lower() and n not in matches
            )
        return matches[:limit]

    # ── Neighbours ──────────────────────────────────────────────────────

    def get_neighbours(
        self,
        node_id: str,
        adj: Dict[str, Set[str]],
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """Expand a node's neighbourhood up to `depth` hops."""
        visited: Set[str] = {node_id}
        frontier: Set[str] = {node_id}
        results: List[Dict[str, Any]] = []

        for d in range(depth):
            next_frontier: Set[str] = set()
            for nid in frontier:
                for nb in adj.get(nid, set()):
                    if nb not in visited:
                        visited.add(nb)
                        next_frontier.add(nb)
                        node_info = self._index._docs.get(nb, {"id": nb})
                        results.append({**node_info, "depth": d + 1})
            frontier = next_frontier

        return results

    # ── Analytics ───────────────────────────────────────────────────────

    def search_analytics(self) -> Dict[str, Any]:
        """Return search usage analytics."""
        if not self._query_log:
            return {"total_searches": 0}

        queries = [q["query"] for q in self._query_log]
        zero_result = [q for q in self._query_log if q["hits"] == 0]

        # Term frequency
        term_freq: Dict[str, int] = defaultdict(int)
        for q in queries:
            for t in _tokenise(q):
                term_freq[t] += 1

        top_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            "total_searches": len(self._query_log),
            "unique_queries": len(set(queries)),
            "zero_result_queries": len(zero_result),
            "avg_response_ms": round(
                sum(q["took_ms"] for q in self._query_log) / len(self._query_log), 2
            ),
            "top_search_terms": [{"term": t, "count": c} for t, c in top_terms],
            "recent_zero_results": [
                q["query"] for q in zero_result[-10:]
            ],
        }


# ─── Module-level singleton ─────────────────────────────────────────────────

search_engine = GraphSearchEngine()
