"""
CARVanta – Antigen Synergy Matrix v1
=======================================
CARVanta-Original: Multi-target combination scoring for CAR-T therapies.

Evaluates 2+ antigen combinations for synergistic CAR-T targeting.
Considers complementary expression, combined coverage, escape risk
reduction, and aggregate safety profiles.

Usage:
    from features.multi_target import score_combination, find_optimal_combo
    result = score_combination(["CD19", "CD22"])
"""

from features.tumor_features import generate_features, antigen_df
from scoring.cvs_engine import compute_cvs
from features.safety_features import compute_safety_profile


def _expression_complementarity(features_list: list) -> float:
    """
    CARVanta-Original: Compute how well antigens complement each other.

    High complementarity = when one antigen has low expression in a context,
    the other has high expression → better combined coverage.
    """
    if len(features_list) < 2:
        return 0.0

    # Compare tumor specificity profiles
    specificities = [f["tumor_specificity"] for f in features_list]
    risks = [f["normal_expression_risk"] for f in features_list]

    # Ideal: high average specificity with diversity (not all correlated)
    mean_spec = sum(specificities) / len(specificities)

    # Variance in specificities = diversity
    variance = sum((s - mean_spec) ** 2 for s in specificities) / len(specificities)
    diversity_bonus = min(variance * 2, 0.15)  # Up to 15% bonus for diversity

    # Penalize if all antigens have same risk profile (no complementarity)
    mean_risk = sum(risks) / len(risks)
    risk_variance = sum((r - mean_risk) ** 2 for r in risks) / len(risks)
    risk_complement = min(risk_variance * 2, 0.10)

    # Combined score
    complementarity = round(
        min(0.5 * mean_spec + 0.3 * diversity_bonus + 0.2 * risk_complement + 0.3, 1.0),
        3
    )
    return complementarity


def _escape_risk_reduction(features_list: list) -> float:
    """
    CARVanta-Original: Compute tumor escape risk reduction from multi-targeting.

    Single-target CAR-T: tumor can escape by downregulating one antigen.
    Multi-target: escape requires simultaneous downregulation of multiple antigens.

    Score 0-1 where 1.0 = minimal escape risk.
    """
    n_targets = len(features_list)
    if n_targets < 2:
        return 0.3  # Single target = moderate escape risk

    # Base reduction: each additional target exponentially reduces escape risk
    # P(escape) = P(lose target 1) × P(lose target 2) × ...
    # Assuming 30% chance of losing any single target
    single_escape_prob = 0.30
    combined_escape_prob = single_escape_prob ** n_targets

    # Stability matters: unstable antigens are easier to lose
    stabilities = [f["stability_score"] for f in features_list]
    mean_stability = sum(stabilities) / len(stabilities)

    # Adjusted escape probability
    adjusted_escape = combined_escape_prob * (1.5 - mean_stability)
    escape_reduction = round(1 - min(adjusted_escape, 0.9), 3)

    return escape_reduction


def _combined_safety_assessment(features_list: list, antigen_names: list) -> dict:
    """
    CARVanta-Original: Aggregate safety profile across multiple antigens.

    Evaluates combined off-target risk — if ANY antigen has high normal
    expression in a tissue, that tissue is at risk.
    """
    safety_profiles = [compute_safety_profile(f) for f in features_list]

    # Worst-case normal expression risk
    max_risk = max(f["normal_expression_risk"] for f in features_list)
    min_safety_margin = min(p["safety_margin"] for p in safety_profiles)

    # Aggregate toxicity flags (union of all flags)
    all_flags = []
    for i, profile in enumerate(safety_profiles):
        for flag in profile["toxicity_flags"]:
            all_flags.append(f"[{antigen_names[i]}] {flag}")

    # Overall safety = worst-case scenario
    if max_risk >= 0.50:
        risk_level = "High"
    elif max_risk >= 0.25:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    return {
        "combined_risk_level": risk_level,
        "min_safety_margin": min_safety_margin,
        "max_normal_expression_risk": round(max_risk, 3),
        "all_toxicity_flags": all_flags,
        "per_antigen_safety": {
            antigen_names[i]: safety_profiles[i]
            for i in range(len(antigen_names))
        },
        "overall_safe": risk_level == "Low" and len(all_flags) == 0,
    }


def _combined_coverage_score(features_list: list) -> float:
    """
    CARVanta-Original: Compute combined tumor coverage score.

    Multiple surface antigens increase the probability of hitting
    at least one target on every tumor cell.
    """
    # Surface accessibility scores
    surf_scores = [f.get("surface_accessibility", 0.5) for f in features_list]

    # P(hit at least one) = 1 - P(miss all)
    # P(miss one) = 1 - surface_accessibility
    p_miss_all = 1.0
    for s in surf_scores:
        p_miss_all *= (1 - s)

    coverage = round(1 - p_miss_all, 3)
    return coverage


def score_combination(antigen_names: list) -> dict:
    """
    Score a multi-antigen CAR-T combination.

    CARVanta-Original: Antigen Synergy Matrix Algorithm.

    Parameters
    ----------
    antigen_names : list of str
        2+ antigen names to evaluate as a combination.

    Returns
    -------
    dict with synergy_score, individual_scores, complementarity,
    escape_reduction, combined_safety, coverage, recommendation
    """
    if len(antigen_names) < 2:
        return {
            "error": "Need at least 2 antigens for combination scoring",
            "synergy_score": 0.0,
        }

    antigen_names = [a.upper() for a in antigen_names]

    # Generate features and individual CVS for each antigen
    features_list = []
    individual_scores = {}

    for antigen in antigen_names:
        features = generate_features(antigen)
        cvs_result = compute_cvs(features)
        features_list.append(features)
        individual_scores[antigen] = {
            "CVS": cvs_result["CVS"],
            "tier": cvs_result["tier"],
            "confidence": cvs_result["confidence"],
        }

    # Compute synergy components
    complementarity = _expression_complementarity(features_list)
    escape_reduction = _escape_risk_reduction(features_list)
    coverage = _combined_coverage_score(features_list)
    safety = _combined_safety_assessment(features_list, antigen_names)

    # Mean individual CVS
    mean_cvs = sum(s["CVS"] for s in individual_scores.values()) / len(individual_scores)

    # CARVanta-Original: Synergy Score Formula
    # Synergy = weighted combination of individual quality + combo benefits
    synergy_score = round(
        0.35 * mean_cvs +
        0.20 * complementarity +
        0.20 * escape_reduction +
        0.15 * coverage +
        0.10 * (1 - safety["max_normal_expression_risk"]),
        3
    )

    # Recommendation
    if synergy_score >= 0.80 and safety["overall_safe"]:
        recommendation = "Strongly Recommended — high synergy with favorable safety"
    elif synergy_score >= 0.70:
        recommendation = "Recommended — good combination with acceptable risk"
    elif synergy_score >= 0.55:
        recommendation = "Consider — moderate synergy, further validation needed"
    else:
        recommendation = "Not Recommended — insufficient synergy or safety concerns"

    return {
        "antigens": antigen_names,
        "synergy_score": synergy_score,
        "individual_scores": individual_scores,
        "complementarity": complementarity,
        "escape_risk_reduction": escape_reduction,
        "combined_coverage": coverage,
        "combined_safety": safety,
        "mean_individual_cvs": round(mean_cvs, 3),
        "recommendation": recommendation,
        "n_targets": len(antigen_names),
    }


def find_optimal_combo(
    candidates: list = None,
    n_targets: int = 2,
    top_n: int = 5,
    cancer_type: str = None,
) -> list:
    """
    Find the optimal multi-antigen combination from a candidate list.

    CARVanta-Original: Exhaustive pairwise synergy search.

    Parameters
    ----------
    candidates : list, optional
        List of antigen names to consider. If None, uses top 20 antigens.
    n_targets : int
        Number of antigens per combination (default: 2).
    top_n : int
        Number of top combinations to return.
    cancer_type : str, optional
        Filter candidates by cancer type.

    Returns
    -------
    list of top combinations sorted by synergy score
    """
    from itertools import combinations

    if candidates is None:
        # Get top antigens by CVS
        all_antigens = sorted(antigen_df["antigen_name"].unique().tolist())
        # Score all and take top 20
        scored = []
        for ag in all_antigens[:100]:  # Limit for performance
            features = generate_features(ag)
            cvs = compute_cvs(features)
            scored.append((ag, cvs["CVS"]))
        scored.sort(key=lambda x: x[1], reverse=True)
        candidates = [s[0] for s in scored[:20]]

    # Generate all combinations
    combos = list(combinations(candidates, n_targets))

    # Score each (limit to first 100 for performance)
    results = []
    for combo in combos[:100]:
        result = score_combination(list(combo))
        results.append(result)

    # Sort by synergy score
    results.sort(key=lambda x: x["synergy_score"], reverse=True)

    return results[:top_n]
