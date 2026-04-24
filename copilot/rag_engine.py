"""
CARVanta Copilot — RAG Engine
================================
Retrieval-Augmented Generation engine for immunotherapy research.

Implements vector-based semantic search over the paper index, context
assembly for LLM prompts, and source-cited answer generation.

Architecture:
  Query → Embedding → Vector Search → Context Assembly → LLM Generation → Cited Answer

Security: Stateless, async, input-validated. No external model calls (simulated).
"""

import hashlib
import logging
import math
import random
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("carvanta.copilot.rag_engine")

# ──────────────────────────────────────────────────────────────────────
# Vector Embedding (Simulated — production would use sentence-transformers)
# ──────────────────────────────────────────────────────────────────────

_EMBEDDING_DIM = 128


def _hash_embed(text: str) -> List[float]:
    """
    Generate a deterministic pseudo-embedding from text content.
    In production, this would use a transformer encoder like PubMedBERT.
    """
    tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
    vec = [0.0] * _EMBEDDING_DIM
    for t in tokens:
        h = hashlib.sha256(t.encode()).hexdigest()
        for i in range(min(_EMBEDDING_DIM, len(h) // 2)):
            val = int(h[i * 2:i * 2 + 2], 16) / 255.0
            vec[i] += val
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class EmbeddedDocument:
    """Document with vector embedding."""
    doc_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0


@dataclass
class RetrievedContext:
    """Retrieved document context for RAG."""
    doc_id: str
    text: str
    similarity: float
    source: str
    year: int
    pmid: str
    rank: int = 0


@dataclass
class GeneratedAnswer:
    """RAG-generated answer with citations."""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    query: str
    context_used: int
    model: str = "carvanta-copilot-v5"
    tokens_used: int = 0


# ──────────────────────────────────────────────────────────────────────
# Vector Store (In-Memory)
# ──────────────────────────────────────────────────────────────────────

class VectorStore:
    """In-memory vector store for document embeddings."""

    def __init__(self) -> None:
        self.documents: List[EmbeddedDocument] = []
        self._built = False

    async def index_documents(self, papers: List[Dict[str, Any]]) -> int:
        """Index papers into the vector store."""
        if self._built:
            return len(self.documents)

        for paper in papers:
            text = f"{paper.get('title', '')}. {' '.join(paper.get('abstract_keywords', []))}. Targets: {', '.join(paper.get('targets', []))}."
            embedding = _hash_embed(text)
            doc = EmbeddedDocument(
                doc_id=paper.get("pmid", ""),
                text=text,
                embedding=embedding,
                metadata={
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", []),
                    "journal": paper.get("journal", ""),
                    "year": paper.get("year", 0),
                    "citations": paper.get("citations", 0),
                    "targets": paper.get("targets", []),
                },
            )
            self.documents.append(doc)

        self._built = True
        logger.info(f"Indexed {len(self.documents)} documents into vector store")
        return len(self.documents)

    async def search(self, query: str, top_k: int = 5) -> List[RetrievedContext]:
        """Search vector store for most relevant documents."""
        query_embedding = _hash_embed(query)
        scored: List[Tuple[float, EmbeddedDocument]] = []

        for doc in self.documents:
            sim = _cosine_similarity(query_embedding, doc.embedding)
            scored.append((sim, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[RetrievedContext] = []
        for i, (sim, doc) in enumerate(scored[:top_k]):
            results.append(RetrievedContext(
                doc_id=doc.doc_id,
                text=doc.text,
                similarity=round(sim, 4),
                source=f"{doc.metadata.get('title', '')} ({doc.metadata.get('journal', '')}, {doc.metadata.get('year', '')})",
                year=doc.metadata.get("year", 0),
                pmid=doc.doc_id,
                rank=i + 1,
            ))
        return results

    @property
    def size(self) -> int:
        return len(self.documents)


# ──────────────────────────────────────────────────────────────────────
# Knowledge Base Templates (Simulated LLM Output)
# ──────────────────────────────────────────────────────────────────────

_ANSWER_TEMPLATES: Dict[str, List[str]] = {
    "car-t": [
        "CAR-T cell therapy involves engineering a patient's T cells to express chimeric antigen receptors "
        "that recognize specific tumor antigens. The CAR construct typically includes an scFv domain for "
        "antigen binding, a hinge/transmembrane region, and intracellular signaling domains (CD3ζ + co-stimulatory).",
        "Five generations of CAR designs have been developed: 1st (CD3ζ only), 2nd (+CD28 or 4-1BB), "
        "3rd (+two co-stimulatory domains), 4th (TRUCKs with cytokine release), and 5th (IL-2Rβ for STAT signaling).",
    ],
    "cd19": [
        "CD19 is the most validated CAR-T target, with FDA-approved products including tisagenlecleucel (Kymriah), "
        "axicabtagene ciloleucel (Yescarta), lisocabtagene maraleucel (Breyanzi), and brexucabtagene autoleucel (Tecartus). "
        "CD19 is expressed on virtually all B-cell malignancies with limited normal tissue expression.",
        "Clinical outcomes with CD19 CAR-T include CR rates of 80-90% in pediatric ALL (ELIANA trial) and "
        "58-83% ORR in DLBCL. Key challenges include CRS, ICANS, B-cell aplasia, and antigen loss relapse.",
    ],
    "bcma": [
        "BCMA (B-cell maturation antigen) is the leading CAR-T target for multiple myeloma. FDA-approved "
        "products include idecabtagene vicleucel (Abecma, 4-1BB co-stim) and ciltacabtagene autoleucel "
        "(Carvykti, dual BCMA-binding domains). ORR ranges from 73-98% in relapsed/refractory MM.",
    ],
    "toxicity": [
        "The two major toxicities of CAR-T therapy are CRS (cytokine release syndrome) and ICANS "
        "(immune effector cell-associated neurotoxicity). CRS is managed with tocilizumab (anti-IL-6R) "
        "and corticosteroids. ICANS requires dexamethasone. On-target off-tumor toxicity (e.g., B-cell aplasia "
        "with CD19 CARs) is managed with IVIG supplementation.",
    ],
    "solid_tumor": [
        "CAR-T therapy faces significant challenges in solid tumors: (1) hostile TME with immunosuppressive "
        "cells (Tregs, MDSCs, TAMs), (2) physical barriers to T cell infiltration, (3) heterogeneous antigen "
        "expression, (4) T cell exhaustion from chronic stimulation, and (5) on-target off-tumor toxicity. "
        "Strategies including armored CARs (IL-12, PD-1 DNR), logic-gated CARs, and local delivery are being explored.",
    ],
    "manufacturing": [
        "CAR-T manufacturing involves apheresis → T cell isolation → activation → viral transduction → "
        "expansion → quality control → infusion. Key challenges include vein-to-vein time (3-5 weeks), "
        "cost ($300-500K), autologous variability, and scalability. Allogeneic 'off-the-shelf' approaches "
        "using gene-edited donor cells are being developed to address these limitations.",
    ],
}


def _generate_answer(query: str, contexts: List[RetrievedContext]) -> str:
    """
    Generate a cited answer from retrieved contexts.
    In production, this would use an LLM with RAG prompting.
    """
    query_lower = query.lower()
    answer_parts: List[str] = []

    # Match to template answers based on query keywords
    for key, templates in _ANSWER_TEMPLATES.items():
        key_parts = key.replace("-", " ").replace("_", " ").split()
        if any(kp in query_lower for kp in key_parts):
            answer_parts.extend(random.sample(templates, min(len(templates), 2)))

    if not answer_parts:
        # Generic synthesis from context
        answer_parts.append(
            f"Based on {len(contexts)} relevant papers in the CARVanta knowledge base, "
            f"here is what we know about '{query}':"
        )
        for ctx in contexts[:3]:
            answer_parts.append(f"• {ctx.source}: {ctx.text[:150]}")

    # Add citations
    citations = []
    for ctx in contexts[:5]:
        citations.append(f"[{ctx.rank}] {ctx.source} (PMID: {ctx.pmid})")

    full_answer = "\n\n".join(answer_parts)
    if citations:
        full_answer += "\n\n**References:**\n" + "\n".join(citations)

    return full_answer


# ──────────────────────────────────────────────────────────────────────
# RAG Pipeline
# ──────────────────────────────────────────────────────────────────────

_VECTOR_STORE: Optional[VectorStore] = None


async def _get_vector_store() -> VectorStore:
    """Get or initialize the vector store."""
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        from copilot.paper_index import PAPER_DATABASE
        _VECTOR_STORE = VectorStore()
        await _VECTOR_STORE.index_documents(PAPER_DATABASE)
    return _VECTOR_STORE


async def retrieve_context(query: str, top_k: int = 5) -> List[RetrievedContext]:
    """Retrieve relevant context for a query."""
    store = await _get_vector_store()
    return await store.search(query, top_k=top_k)


async def generate_rag_answer(
    query: str,
    top_k: int = 5,
    include_sources: bool = True,
) -> GeneratedAnswer:
    """
    Full RAG pipeline: retrieve → assemble context → generate answer.
    """
    if not query or len(query.strip()) < 3:
        return GeneratedAnswer(
            answer="Please provide a more specific question.",
            confidence=0.0, sources=[], query=query, context_used=0,
        )

    contexts = await retrieve_context(query, top_k=top_k)
    answer_text = _generate_answer(query, contexts)
    avg_sim = sum(c.similarity for c in contexts) / len(contexts) if contexts else 0
    confidence = min(0.95, avg_sim * 1.5 + 0.3)

    sources = []
    if include_sources:
        for ctx in contexts:
            sources.append({
                "pmid": ctx.pmid,
                "title": ctx.source,
                "relevance": ctx.similarity,
                "rank": ctx.rank,
            })

    return GeneratedAnswer(
        answer=answer_text,
        confidence=round(confidence, 3),
        sources=sources,
        query=query,
        context_used=len(contexts),
        tokens_used=len(answer_text.split()) * 2,
    )
