"""
CARVanta – Semantic NLP Search v1
====================================
Uses sentence-transformers to provide real semantic search over antigen
profiles. Falls back to keyword matching if sentence-transformers is not
available.

Features:
- Encodes antigen profiles as text → dense vector embeddings
- Encodes user queries as embeddings
- Cosine similarity matching for semantic relevance
- Works on CPU, uses small model (all-MiniLM-L6-v2, ~80MB)

Usage:
    from features.nlp_semantic import SemanticSearch
    search = SemanticSearch()
    results = search.search("safe targets for brain cancer")
"""

import os
import sys
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to load sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False

from features.tumor_features import antigen_df, precompute_all_scores


def _build_antigen_texts(df) -> list:
    """
    Build natural language descriptions for each antigen row.
    These texts are what get embedded for semantic matching.
    """
    texts = []
    for _, row in df.iterrows():
        name = row["antigen_name"]
        cancer = row["cancer_type"]
        tumor = row["mean_tumor_expression"]
        normal = row["mean_normal_expression"]
        stab = row["stability_score"]
        lit = row["literature_support"]
        immuno = row.get("immunogenicity_score", 0.5)
        surface = row.get("surface_accessibility", 0.5)
        trials = row.get("clinical_trials_count", 0)

        # Compute derived characteristics
        specificity = tumor / (tumor + normal) if (tumor + normal) > 0 else 0.5
        safety = "safe" if normal < 2.0 else "moderate risk" if normal < 4.0 else "high risk"

        tier_score = (
            0.30 * specificity +
            0.25 * (1 - min(normal / 10.0, 1.0) ** 1.5) +
            0.15 * stab +
            0.10 * lit +
            0.10 * immuno +
            0.10 * surface
        )
        tier = (
            "tier 1 highly viable" if tier_score >= 0.85
            else "tier 2 promising" if tier_score >= 0.70
            else "tier 3 experimental" if tier_score >= 0.55
            else "tier 4 high risk"
        )

        surface_type = (
            "surface antigen membrane-bound" if surface > 0.7
            else "partial surface" if surface > 0.4
            else "intracellular"
        )

        immuno_level = (
            "highly immunogenic" if immuno > 0.8
            else "moderately immunogenic" if immuno > 0.5
            else "low immunogenicity"
        )

        text = (
            f"{name} antigen for {cancer}. "
            f"{tier}. "
            f"Tumor expression {tumor:.1f}, normal expression {normal:.1f}. "
            f"Specificity {specificity:.2f}. "
            f"Safety profile: {safety}. "
            f"{surface_type}. "
            f"{immuno_level}. "
            f"Stability {stab:.2f}. "
            f"Literature support {lit:.2f}. "
            f"Clinical trials: {trials}."
        )
        texts.append(text)
    return texts


class SemanticSearch:
    """
    CARVanta-Original: Semantic search over antigen profiles using
    sentence-transformers (all-MiniLM-L6-v2).

    Encodes all antigen profiles as text descriptions, then matches
    user queries by cosine similarity.
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.available = HAS_SEMANTIC
        self.model = None
        self.embeddings = None
        self._texts = None
        self._df = None

        if not HAS_SEMANTIC:
            return

        print("[SemanticSearch] Loading model...")
        self.model = SentenceTransformer(model_name)

        # Build antigen texts and encode
        self._df = antigen_df.copy()
        self._texts = _build_antigen_texts(self._df)

        print(f"[SemanticSearch] Encoding {len(self._texts)} antigen profiles...")
        self.embeddings = self.model.encode(
            self._texts,
            show_progress_bar=True,
            batch_size=256,
            normalize_embeddings=True,
        )
        print(f"[SemanticSearch] Ready. Embedding shape: {self.embeddings.shape}")

    def search(self, query: str, top_k: int = 25, cancer_type: str = None) -> list:
        """
        Search for antigens semantically similar to the query.

        Parameters
        ----------
        query : str
            Natural language query
        top_k : int
            Number of results to return
        cancer_type : str, optional
            Filter results to this cancer type

        Returns
        -------
        list of dicts with antigen info + similarity scores
        """
        if not self.available or self.model is None:
            return []

        # Encode query
        query_embedding = self.model.encode(
            [query], normalize_embeddings=True
        )[0]

        # Cosine similarity (embeddings are normalized, so dot product = cosine)
        similarities = np.dot(self.embeddings, query_embedding)

        # Get sorted indices
        sorted_indices = np.argsort(-similarities)

        results = []
        seen_antigens = set()  # Deduplicate by antigen name

        for idx in sorted_indices:
            if len(results) >= top_k:
                break

            row = self._df.iloc[idx]
            antigen_name = row["antigen_name"]
            row_cancer = row["cancer_type"]

            # Cancer type filter
            if cancer_type and row_cancer.lower() != cancer_type.lower():
                continue

            # Deduplicate: keep best match per antigen
            if antigen_name in seen_antigens:
                continue
            seen_antigens.add(antigen_name)

            tumor = row["mean_tumor_expression"]
            normal = row["mean_normal_expression"]
            specificity = tumor / (tumor + normal) if (tumor + normal) > 0 else 0.5

            safety_score = 1 - min(normal / 10.0, 1.0) ** 1.5
            stab = row["stability_score"]
            lit = row["literature_support"]
            immuno = row.get("immunogenicity_score", 0.5)
            surface = row.get("surface_accessibility", 0.5)

            cvs = (
                0.30 * specificity +
                0.25 * safety_score +
                0.15 * stab +
                0.10 * lit +
                0.10 * immuno +
                0.10 * surface
            )

            if cvs >= 0.85:
                tier = "Tier 1 - Highly Viable"
            elif cvs >= 0.70:
                tier = "Tier 2 - Promising"
            elif cvs >= 0.55:
                tier = "Tier 3 - Experimental"
            else:
                tier = "Tier 4 - High Risk"

            results.append({
                "antigen": antigen_name,
                "cancer_type": row_cancer,
                "CVS": round(cvs, 3),
                "tier": tier,
                "similarity": round(float(similarities[idx]), 3),
                "confidence": round(float((stab + lit + immuno) / 3), 3),
                "breakdown": {
                    "tumor_specificity": round(specificity, 3),
                    "safety_component": round(safety_score, 3),
                    "stability": round(stab, 3),
                    "evidence": round(lit, 3),
                    "immunogenicity": round(immuno, 3),
                    "surface_accessibility": round(surface, 3),
                },
            })

        return results

    @property
    def is_available(self):
        return self.available and self.model is not None


# Module-level singleton (lazy-loaded)
_semantic_search_instance = None


def get_semantic_search() -> SemanticSearch:
    """Get or create the semantic search singleton."""
    global _semantic_search_instance
    if _semantic_search_instance is None:
        _semantic_search_instance = SemanticSearch()
    return _semantic_search_instance
