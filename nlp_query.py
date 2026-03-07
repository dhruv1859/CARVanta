"""
CARVanta – Query Language v1
================================
CARVanta-Original: Keyword-based NLP parser for natural language
antigen discovery queries.

Parses queries like:
    "Find me targets for triple-negative breast cancer with low toxicity risk"
    "Show CAR-T antigens for leukemia tier 1 only"
    "Best surface antigens for myeloma with high immunogenicity"

Extracts: cancer type, safety preference, tier preference, expression
thresholds, immunogenicity requirements, surface requirements.

Usage:
    from features.nlp_query import parse_query, execute_query
    results = execute_query("Find targets for leukemia with low toxicity")
"""

import re
from features.tumor_features import (
    antigen_df, generate_features, precompute_all_scores,
    precompute_scores_for_cancer,
)
from scoring.cvs_engine import compute_cvs
from features.safety_features import compute_safety_profile

# Cache for expensive score computations
_GLOBAL_SCORES_CACHE = None
_CANCER_SCORES_CACHE = {}


def _get_global_scores():
    """Return cached global scores, computing once on first call."""
    global _GLOBAL_SCORES_CACHE
    if _GLOBAL_SCORES_CACHE is None:
        _GLOBAL_SCORES_CACHE = precompute_all_scores()
    return _GLOBAL_SCORES_CACHE


def _get_cancer_scores(cancer_type: str):
    """Return cached cancer-specific scores, computing once per cancer type."""
    global _CANCER_SCORES_CACHE
    key = cancer_type.lower().strip()
    if key not in _CANCER_SCORES_CACHE:
        _CANCER_SCORES_CACHE[key] = precompute_scores_for_cancer(cancer_type)
    return _CANCER_SCORES_CACHE[key]


# ─── Cancer type keyword mapping ────────────────────────────────────────────────
CANCER_KEYWORDS = {
    "breast cancer": "Breast Cancer",
    "breast": "Breast Cancer",
    "tnbc": "Breast Cancer",
    "triple-negative breast": "Breast Cancer",
    "triple negative breast": "Breast Cancer",
    "lung": "Lung Adenocarcinoma",
    "lung cancer": "Lung Adenocarcinoma",
    "lung adenocarcinoma": "Lung Adenocarcinoma",
    "nsclc": "Lung Adenocarcinoma",
    "glioblastoma": "Glioblastoma",
    "gbm": "Glioblastoma",
    "brain cancer": "Glioblastoma",
    "brain tumor": "Glioblastoma",
    "prostate": "Prostate Cancer",
    "prostate cancer": "Prostate Cancer",
    "colorectal": "Colorectal Cancer",
    "colorectal cancer": "Colorectal Cancer",
    "colon": "Colorectal Cancer",
    "colon cancer": "Colorectal Cancer",
    "ovarian": "Ovarian Cancer",
    "ovarian cancer": "Ovarian Cancer",
    "leukemia": "Leukemia",
    "leukaemia": "Leukemia",
    "aml": "Leukemia",
    "all": "Leukemia",
    "cll": "Leukemia",
    "melanoma": "Melanoma",
    "skin cancer": "Melanoma",
    "liver cancer": "Liver Cancer",
    "liver": "Liver Cancer",
    "hepatocellular": "Liver Cancer",
    "hcc": "Liver Cancer",
    "renal": "Renal Cancer",
    "renal cancer": "Renal Cancer",
    "kidney": "Renal Cancer",
    "kidney cancer": "Renal Cancer",
    "gastric": "Gastric Cancer",
    "gastric cancer": "Gastric Cancer",
    "stomach": "Gastric Cancer",
    "stomach cancer": "Gastric Cancer",
    "pancreatic": "Pancreatic Cancer",
    "pancreatic cancer": "Pancreatic Cancer",
    "pancreas": "Pancreatic Cancer",
    "lymphoma": "Lymphoma",
    "dlbcl": "Lymphoma",
    "myeloma": "Myeloma",
    "multiple myeloma": "Myeloma",
    "bladder": "Bladder Cancer",
    "bladder cancer": "Bladder Cancer",
    "head and neck": "Head & Neck Cancer",
    "head & neck": "Head & Neck Cancer",
    "hnsc": "Head & Neck Cancer",
    "endometrial": "Endometrial Cancer",
    "endometrial cancer": "Endometrial Cancer",
    "uterine": "Endometrial Cancer",
    "thyroid": "Thyroid Cancer",
    "thyroid cancer": "Thyroid Cancer",
}

# ─── Safety preference keywords ──────────────────────────────────────────────────
SAFETY_KEYWORDS = {
    "safe": "low",
    "low toxicity": "low",
    "low risk": "low",
    "minimal risk": "low",
    "no toxicity": "low",
    "safe targets": "low",
    "favorable safety": "low",
    "low off-target": "low",
    "any risk": "any",
    "high risk ok": "any",
    "experimental": "any",
}

# ─── Tier keywords ───────────────────────────────────────────────────────────────
TIER_KEYWORDS = {
    "tier 1": 1,
    "tier1": 1,
    "highly viable": 1,
    "best": 1,
    "top": 1,
    "highest": 1,
    "tier 2": 2,
    "tier2": 2,
    "promising": 2,
    "tier 3": 3,
    "tier3": 3,
    "experimental": 3,
    "tier 4": 4,
    "tier4": 4,
}

# ─── Feature preference keywords ─────────────────────────────────────────────────
FEATURE_KEYWORDS = {
    "immunogenic": {"immunogenicity_min": 0.7},
    "high immunogenicity": {"immunogenicity_min": 0.8},
    "low immunogenicity": {"immunogenicity_max": 0.4},
    "surface": {"surface_min": 0.6},
    "surface antigen": {"surface_min": 0.7},
    "membrane": {"surface_min": 0.65},
    "intracellular": {"surface_max": 0.4},
    "stable": {"stability_min": 0.8},
    "high expression": {"tumor_expr_min": 7.0},
    "overexpressed": {"tumor_expr_min": 8.0},
    "specific": {"specificity_min": 0.75},
    "highly specific": {"specificity_min": 0.85},
}


def parse_query(query: str) -> dict:
    """
    CARVanta-Original: Parse a natural language antigen discovery query.

    Parameters
    ----------
    query : str
        Natural language query, e.g.:
        "Find me targets for triple-negative breast cancer with low toxicity risk"

    Returns
    -------
    dict with parsed filters:
        - cancer_type: str or None
        - safety_preference: str or None
        - tier_filter: int or None
        - feature_filters: dict
        - sort_by: str
        - limit: int
        - raw_query: str
    """
    q = query.lower().strip()

    parsed = {
        "cancer_type": None,
        "safety_preference": None,
        "tier_filter": None,
        "feature_filters": {},
        "sort_by": "CVS",
        "limit": 25,
        "raw_query": query,
    }

    # ── Extract cancer type ─────────────────────────────────────────────────
    # Sort keywords by length (longest first) for greedy matching
    sorted_cancer = sorted(CANCER_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_cancer:
        if keyword in q:
            parsed["cancer_type"] = CANCER_KEYWORDS[keyword]
            break

    # ── Extract safety preference ───────────────────────────────────────────
    sorted_safety = sorted(SAFETY_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_safety:
        if keyword in q:
            parsed["safety_preference"] = SAFETY_KEYWORDS[keyword]
            break

    # ── Extract tier filter ─────────────────────────────────────────────────
    sorted_tiers = sorted(TIER_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_tiers:
        if keyword in q:
            parsed["tier_filter"] = TIER_KEYWORDS[keyword]
            break

    # ── Extract feature preferences ─────────────────────────────────────────
    sorted_features = sorted(FEATURE_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_features:
        if keyword in q:
            parsed["feature_filters"].update(FEATURE_KEYWORDS[keyword])

    # ── Extract limit ───────────────────────────────────────────────────────
    limit_match = re.search(r"top\s+(\d+)", q)
    if limit_match:
        parsed["limit"] = min(int(limit_match.group(1)), 100)

    # ── Sort preference ─────────────────────────────────────────────────────
    if "safest" in q or "safety" in q:
        parsed["sort_by"] = "safety"
    elif "immunogen" in q:
        parsed["sort_by"] = "immunogenicity"
    elif "surface" in q:
        parsed["sort_by"] = "surface_accessibility"

    return parsed


def execute_query(query: str, precomputed_scores=None) -> dict:
    """
    CARVanta v4: Execute a natural language antigen query.

    Pipeline:
    1. Parse query for structured filters (cancer type, safety, tier, etc.)
    2. Load cancer-context-aware scores (or use precomputed global scores)
    3. Apply structured filters
    4. Re-rank using semantic similarity (if sentence-transformers available)
    5. Return ranked results

    Parameters
    ----------
    query : str
        Natural language query.
    precomputed_scores : list, optional
        Pre-computed global scores from API startup cache to avoid recomputing.

    Returns
    -------
    dict with parsed_query, results, total_matches, summary, search_method
    """
    parsed = parse_query(query)

    # v4: Use cached cancer-context-aware scoring when cancer type is detected
    if parsed["cancer_type"]:
        all_scores = _get_cancer_scores(parsed["cancer_type"])
    elif precomputed_scores is not None:
        all_scores = precomputed_scores
    else:
        all_scores = _get_global_scores()

    # Apply structured filters
    filtered = []

    for entry in all_scores:
        antigen = entry["antigen"]
        cvs = entry["CVS"]
        tier = entry["tier"]
        breakdown = entry["breakdown"]

        # Cancer type filter (already handled by context-aware scoring,
        # but keep for global scores filtering)
        if parsed["cancer_type"] and not parsed.get("_used_context_scoring"):
            ct = entry.get("cancer_type", "")
            if ct != parsed["cancer_type"]:
                continue

        # Tier filter
        if parsed["tier_filter"]:
            tier_num = int(tier.split(" ")[1]) if "Tier" in tier else 4
            if tier_num > parsed["tier_filter"]:
                continue

        # Safety preference filter
        if parsed["safety_preference"] == "low":
            safety_component = breakdown.get("safety_component", 0.5)
            if safety_component < 0.70:
                continue

        # Feature filters
        ff = parsed["feature_filters"]
        if ff.get("immunogenicity_min") and breakdown.get("immunogenicity", 0.5) < ff["immunogenicity_min"]:
            continue
        if ff.get("immunogenicity_max") and breakdown.get("immunogenicity", 0.5) > ff["immunogenicity_max"]:
            continue
        if ff.get("surface_min") and breakdown.get("surface_accessibility", 0.5) < ff["surface_min"]:
            continue
        if ff.get("surface_max") and breakdown.get("surface_accessibility", 0.5) > ff["surface_max"]:
            continue
        if ff.get("stability_min") and breakdown.get("stability", 0.5) < ff["stability_min"]:
            continue
        if ff.get("specificity_min") and breakdown.get("tumor_specificity", 0.5) < ff["specificity_min"]:
            continue

        filtered.append(entry)

    # v4: Try semantic re-ranking
    search_method = "keyword+context-aware"
    try:
        from features.nlp_semantic import get_semantic_search
        sem = get_semantic_search()
        if sem.is_available:
            sem_results = sem.search(
                query,
                top_k=100,
                cancer_type=parsed["cancer_type"],
            )
            # Build a similarity lookup
            sim_lookup = {r["antigen"]: r["similarity"] for r in sem_results}

            # Blend: 60% adaptive CVS + 40% semantic similarity
            for entry in filtered:
                sim = sim_lookup.get(entry["antigen"], 0.0)
                entry["semantic_similarity"] = sim
                entry["blended_score"] = round(
                    0.60 * entry["CVS"] + 0.40 * sim, 3
                )

            search_method = "semantic+context-aware"
    except Exception:
        # Semantic search not available, use standard scoring
        for entry in filtered:
            entry["semantic_similarity"] = 0.0
            entry["blended_score"] = entry["CVS"]

    # Sort by blended score (semantic + CVS) or just CVS
    sort_key = parsed["sort_by"]
    if sort_key == "CVS":
        filtered.sort(
            key=lambda x: x.get("blended_score", x["CVS"]),
            reverse=True,
        )
    elif sort_key == "safety":
        filtered.sort(
            key=lambda x: x["breakdown"].get("safety_component", 0),
            reverse=True,
        )
    elif sort_key == "immunogenicity":
        filtered.sort(
            key=lambda x: x["breakdown"].get("immunogenicity", 0),
            reverse=True,
        )
    elif sort_key == "surface_accessibility":
        filtered.sort(
            key=lambda x: x["breakdown"].get("surface_accessibility", 0),
            reverse=True,
        )

    # Limit results
    results = filtered[:parsed["limit"]]

    # Generate summary
    summary = _generate_query_summary(parsed, len(filtered), results)

    return {
        "parsed_query": parsed,
        "results": results,
        "total_matches": len(filtered),
        "returned": len(results),
        "summary": summary,
        "search_method": search_method,
    }


def _generate_query_summary(parsed: dict, total: int, results: list) -> str:
    """Generate a human-readable summary of query results."""
    parts = []

    if total == 0:
        return "No antigens matched your search criteria. Try broadening your filters."

    parts.append(f"Found {total} antigens")

    if parsed["cancer_type"]:
        parts.append(f"for {parsed['cancer_type']}")

    if parsed["safety_preference"] == "low":
        parts.append("with favorable safety profile")

    if parsed["tier_filter"]:
        parts.append(f"in Tier {parsed['tier_filter']} or above")

    ff = parsed["feature_filters"]
    if ff.get("surface_min"):
        parts.append("with surface accessibility")
    if ff.get("immunogenicity_min"):
        parts.append("with high immunogenicity")

    summary = " ".join(parts) + "."

    if results:
        top = results[0]
        summary += (
            f" Top candidate: {top['antigen']} "
            f"(CVS: {top['CVS']}, {top['tier']})."
        )

    return summary
