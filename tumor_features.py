import pandas as pd
import os
import numpy as np
from scoring.cvs_engine import compute_cvs

# ─── Load the biomarker database ────────────────────────────────────────────────
_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "biomarker_database.csv")


antigen_df = pd.read_csv(_DATA_PATH)

# Normalize column name if needed
if "gene_symbol" in antigen_df.columns and "antigen_name" not in antigen_df.columns:
    antigen_df.rename(columns={"gene_symbol": "antigen_name"}, inplace=True)

# ─── v2: Ensure new columns exist (backward compat with old CSVs) ───────────────
if "immunogenicity_score" not in antigen_df.columns:
    antigen_df["immunogenicity_score"] = 0.5
if "surface_accessibility" not in antigen_df.columns:
    antigen_df["surface_accessibility"] = 0.5
if "clinical_trials_count" not in antigen_df.columns:
    antigen_df["clinical_trials_count"] = 0

# v5: Ensure classification columns exist (backward compat)
if "data_source" not in antigen_df.columns:
    antigen_df["data_source"] = "computationally_derived"
if "source_database" not in antigen_df.columns:
    antigen_df["source_database"] = "Synthetic"
if "evidence_level" not in antigen_df.columns:
    antigen_df["evidence_level"] = "predicted"


def get_all_antigens():
    """Return a sorted list of unique antigen/gene names."""
    return sorted(antigen_df["antigen_name"].unique().tolist())


def compute_clinical_evidence_boost(lit_support: float, clinical_trials: int) -> float:
    """
    Boost literature support score based on clinical trial count.
    More trials → stronger evidence → higher effective score.
    """
    if clinical_trials >= 100:
        boost = 0.10
    elif clinical_trials >= 30:
        boost = 0.06
    elif clinical_trials >= 10:
        boost = 0.03
    elif clinical_trials >= 1:
        boost = 0.01
    else:
        boost = 0.0
    return min(round(lit_support + boost, 3), 0.99)


def generate_features(antigen_name: str) -> dict:
    """Generate the full feature vector for a given antigen (v2: 6 features)."""
    antigen_name = antigen_name.upper()

    match = antigen_df[
        antigen_df["antigen_name"].str.upper() == antigen_name
    ]

    if not match.empty:
        row = match.iloc[0]

        tumor_expr = float(row["mean_tumor_expression"])
        normal_expr = float(row["mean_normal_expression"])

        MAX_NORMAL_EXPRESSION = 10.0
        MIN_TUMOR_THRESHOLD = 5.0

        # Compute tumor specificity
        tumor_specificity = tumor_expr / (tumor_expr + normal_expr)
        if tumor_expr < MIN_TUMOR_THRESHOLD:
            tumor_specificity *= 0.8

        # Compute safety
        normal_expression_risk = (normal_expr / MAX_NORMAL_EXPRESSION) ** 1.5
        normal_expression_risk = min(normal_expression_risk, 1.0)

        # Clinical trial count & evidence boost
        clinical_trials = int(row.get("clinical_trials_count", 0))
        raw_lit = float(row["literature_support"])
        boosted_lit = compute_clinical_evidence_boost(raw_lit, clinical_trials)

        return {
            "tumor_specificity": round(tumor_specificity, 3),
            "normal_expression_risk": round(normal_expression_risk, 3),
            "stability_score": float(row["stability_score"]),
            "literature_support": boosted_lit,
            "immunogenicity_score": float(row.get("immunogenicity_score", 0.5)),
            "surface_accessibility": float(row.get("surface_accessibility", 0.5)),
            "clinical_trials_count": clinical_trials,
            # Raw values for safety analysis
            "raw_tumor_expression": tumor_expr,
            "raw_normal_expression": normal_expr,
            # v5: Classification columns
            "data_source": str(row.get("data_source", "computationally_derived")),
            "source_database": str(row.get("source_database", "Synthetic")),
            "evidence_level": str(row.get("evidence_level", "predicted")),
        }

    # Fallback for unknown antigens
    return {
        "tumor_specificity": 0.5,
        "normal_expression_risk": 0.5,
        "stability_score": 0.5,
        "literature_support": 0.3,
        "immunogenicity_score": 0.5,
        "surface_accessibility": 0.5,
        "clinical_trials_count": 0,
        "raw_tumor_expression": 3.0,
        "raw_normal_expression": 3.0,
        "data_source": "computationally_derived",
        "source_database": "Synthetic",
        "evidence_level": "predicted",
    }


def precompute_all_scores():
    """Precompute CVS v4 adaptive scores for all antigens.
    Returns one entry per unique antigen (first occurrence/cancer type).
    Uses BATCH ML ranker blending for speed."""

    unique_df = antigen_df.drop_duplicates(subset="antigen_name", keep="first").copy()

    # Try to load the ML ranker for adaptive scoring
    try:
        from models.predict import predict_ranking_scores_batch
        has_ranker = True
    except Exception:
        has_ranker = False

    MAX_NORMAL_EXPRESSION = 10.0
    MIN_TUMOR_THRESHOLD = 5.0

    # Vectorized feature engineering
    t = unique_df["mean_tumor_expression"]
    n = unique_df["mean_normal_expression"]

    tumor_specificity = t / (t + n)
    tumor_specificity = tumor_specificity.where(t >= MIN_TUMOR_THRESHOLD, tumor_specificity * 0.8)

    normal_expression_risk = ((n / MAX_NORMAL_EXPRESSION).clip(upper=1.0)) ** 1.5

    safety_score = 1 - normal_expression_risk
    stability = unique_df["stability_score"]
    evidence = unique_df["literature_support"]
    immunogenicity = unique_df["immunogenicity_score"]
    surface_access = unique_df["surface_accessibility"]

    # CVS rule-based (6-feature weighted formula)
    cvs = (
        0.30 * tumor_specificity +
        0.25 * safety_score +
        0.15 * stability +
        0.10 * evidence +
        0.10 * immunogenicity +
        0.10 * surface_access
    ).round(3)

    confidence = ((stability + evidence + immunogenicity) / 3).round(3)

    def get_tier(score):
        if score >= 0.85:
            return "Tier 1 - Highly Viable"
        elif score >= 0.70:
            return "Tier 2 - Promising"
        elif score >= 0.55:
            return "Tier 3 - Experimental"
        else:
            return "Tier 4 - High Risk"

    # ── Batch ML prediction (v4 optimization) ────────────────────────────
    ts_arr = tumor_specificity.values
    ner_arr = normal_expression_risk.values
    stab_arr = stability.values
    ev_arr = evidence.values
    im_arr = immunogenicity.values
    sa_arr = surface_access.values
    trials_arr = unique_df["clinical_trials_count"].fillna(0).astype(int).values
    cvs_arr = cvs.values
    conf_arr = confidence.values

    if has_ranker:
        # Build all feature dicts at once
        features_list = []
        for i in range(len(unique_df)):
            features_list.append({
                "tumor_specificity": float(ts_arr[i]),
                "normal_expression_risk": float(ner_arr[i]),
                "stability_score": float(stab_arr[i]),
                "literature_support": float(ev_arr[i]),
                "immunogenicity_score": float(im_arr[i]),
                "surface_accessibility": float(sa_arr[i]),
                "clinical_trials_count": int(trials_arr[i]),
            })

        try:
            # Single batch prediction for ALL antigens
            ml_scores = predict_ranking_scores_batch(features_list)

            # Vectorized adaptive blending
            import numpy as np
            ml_weights = 0.40 * (0.5 + 0.5 * conf_arr)
            adaptive_scores = np.round((1 - ml_weights) * cvs_arr + ml_weights * ml_scores, 3)
        except Exception:
            import numpy as np
            adaptive_scores = cvs_arr
            ml_scores = np.full(len(unique_df), 0.5)
    else:
        import numpy as np
        adaptive_scores = cvs_arr
        ml_scores = np.full(len(unique_df), 0.5)

    # ── Assemble results ─────────────────────────────────────────────────
    ss_arr = safety_score.values
    antigen_names = unique_df["antigen_name"].values
    cancer_types = unique_df["cancer_type"].values
    data_sources = unique_df["data_source"].values if "data_source" in unique_df.columns else ["computationally_derived"] * len(unique_df)

    results = []
    for i in range(len(unique_df)):
        a_score = float(adaptive_scores[i])
        results.append({
            "antigen": str(antigen_names[i]),
            "cancer_type": str(cancer_types[i]),
            "data_source": str(data_sources[i]),
            "CVS": a_score,
            "cvs_rule": float(cvs_arr[i]),
            "ml_score": round(float(ml_scores[i]), 3),
            "confidence": float(conf_arr[i]),
            "tier": get_tier(a_score),
            "breakdown": {
                "tumor_specificity": round(float(ts_arr[i]), 3),
                "safety_component": round(float(ss_arr[i]), 3),
                "stability": float(stab_arr[i]),
                "evidence": float(ev_arr[i]),
                "immunogenicity": float(im_arr[i]),
                "surface_accessibility": float(sa_arr[i]),
            }
        })

    # Sort by adaptive score (highest first)
    results.sort(key=lambda x: x["CVS"], reverse=True)
    return results


def generate_features_for_cancer(antigen_name: str, cancer_type: str) -> dict:
    """Generate features for an antigen in a SPECIFIC cancer type context.
    This is key to context-aware ranking — different cancer types use
    different expression data for the same antigen."""
    antigen_name = antigen_name.upper()
    cancer_type_lower = cancer_type.lower()

    match = antigen_df[
        (antigen_df["antigen_name"].str.upper() == antigen_name) &
        (antigen_df["cancer_type"].str.lower() == cancer_type_lower)
    ]

    if match.empty:
        # Fall back to any cancer type for this antigen
        return generate_features(antigen_name)

    row = match.iloc[0]
    tumor_expr = float(row["mean_tumor_expression"])
    normal_expr = float(row["mean_normal_expression"])

    MAX_NORMAL_EXPRESSION = 10.0
    MIN_TUMOR_THRESHOLD = 5.0

    tumor_specificity = tumor_expr / (tumor_expr + normal_expr)
    if tumor_expr < MIN_TUMOR_THRESHOLD:
        tumor_specificity *= 0.8

    normal_expression_risk = (normal_expr / MAX_NORMAL_EXPRESSION) ** 1.5
    normal_expression_risk = min(normal_expression_risk, 1.0)

    clinical_trials = int(row.get("clinical_trials_count", 0))
    raw_lit = float(row["literature_support"])
    boosted_lit = compute_clinical_evidence_boost(raw_lit, clinical_trials)

    return {
        "tumor_specificity": round(tumor_specificity, 3),
        "normal_expression_risk": round(normal_expression_risk, 3),
        "stability_score": float(row["stability_score"]),
        "literature_support": boosted_lit,
        "immunogenicity_score": float(row.get("immunogenicity_score", 0.5)),
        "surface_accessibility": float(row.get("surface_accessibility", 0.5)),
        "clinical_trials_count": clinical_trials,
        "raw_tumor_expression": tumor_expr,
        "raw_normal_expression": normal_expr,
        "cancer_type": str(row["cancer_type"]),
    }


def precompute_scores_for_cancer(cancer_type: str) -> list:
    """
    CARVanta v4: Compute rankings for a SPECIFIC cancer type.

    Uses cancer-type-specific expression data from the database.
    Different cancer types will produce genuinely different rankings.

    Parameters
    ----------
    cancer_type : str
        Cancer type (e.g., 'Leukemia', 'Melanoma', 'Glioblastoma')

    Returns
    -------
    list of dicts sorted by adaptive score (highest first)
    """
    cancer_type_lower = cancer_type.lower()

    # Filter to rows matching this cancer type
    cancer_df = antigen_df[
        antigen_df["cancer_type"].str.lower() == cancer_type_lower
    ].copy()

    if cancer_df.empty:
        # Fall back to global rankings
        return precompute_all_scores()

    # Try ML ranker
    try:
        from models.predict import predict_ranking_score
        has_ranker = True
    except Exception:
        has_ranker = False

    MAX_NORMAL_EXPRESSION = 10.0
    MIN_TUMOR_THRESHOLD = 5.0

    t = cancer_df["mean_tumor_expression"]
    n = cancer_df["mean_normal_expression"]

    tumor_specificity = t / (t + n)
    tumor_specificity = tumor_specificity.where(t >= MIN_TUMOR_THRESHOLD, tumor_specificity * 0.8)
    normal_expression_risk = ((n / MAX_NORMAL_EXPRESSION).clip(upper=1.0)) ** 1.5
    safety_score = 1 - normal_expression_risk
    stability = cancer_df["stability_score"]
    evidence = cancer_df["literature_support"]
    immunogenicity = cancer_df["immunogenicity_score"]
    surface_access = cancer_df["surface_accessibility"]

    cvs = (
        0.30 * tumor_specificity +
        0.25 * safety_score +
        0.15 * stability +
        0.10 * evidence +
        0.10 * immunogenicity +
        0.10 * surface_access
    ).round(3)

    confidence = ((stability + evidence + immunogenicity) / 3).round(3)

    def get_tier(score):
        if score >= 0.85:
            return "Tier 1 - Highly Viable"
        elif score >= 0.70:
            return "Tier 2 - Promising"
        elif score >= 0.55:
            return "Tier 3 - Experimental"
        else:
            return "Tier 4 - High Risk"

    results = []
    for i, (_, row) in enumerate(cancer_df.iterrows()):
        ts_val = round(float(tumor_specificity.iloc[i]), 3)
        ss_val = round(float(safety_score.iloc[i]), 3)
        st_val = float(row["stability_score"])
        ev_val = float(row["literature_support"])
        im_val = float(row["immunogenicity_score"])
        sa_val = float(row["surface_accessibility"])
        cvs_val = float(cvs.iloc[i])
        conf_val = float(confidence.iloc[i])

        if has_ranker:
            features = {
                "tumor_specificity": ts_val,
                "normal_expression_risk": round(float(normal_expression_risk.iloc[i]), 3),
                "stability_score": st_val,
                "literature_support": ev_val,
                "immunogenicity_score": im_val,
                "surface_accessibility": sa_val,
                "clinical_trials_count": int(row.get("clinical_trials_count", 0)),
            }
            try:
                ml_score = predict_ranking_score(features)
                ml_weight = 0.40 * (0.5 + 0.5 * conf_val)
                adaptive_score = (1 - ml_weight) * cvs_val + ml_weight * ml_score
                adaptive_score = round(adaptive_score, 3)
            except Exception:
                adaptive_score = cvs_val
                ml_score = 0.5
        else:
            adaptive_score = cvs_val
            ml_score = 0.5

        results.append({
            "antigen": row["antigen_name"],
            "cancer_type": str(row["cancer_type"]),
            "data_source": str(row.get("data_source", "computationally_derived")),
            "CVS": adaptive_score,
            "cvs_rule": cvs_val,
            "ml_score": round(ml_score, 3),
            "confidence": conf_val,
            "tier": get_tier(adaptive_score),
            "breakdown": {
                "tumor_specificity": ts_val,
                "safety_component": ss_val,
                "stability": st_val,
                "evidence": ev_val,
                "immunogenicity": im_val,
                "surface_accessibility": sa_val,
            }
        })

    results.sort(key=lambda x: x["CVS"], reverse=True)
    return results


def get_available_cancer_types() -> list:
    """Return sorted list of unique cancer types in the database."""
    return sorted(antigen_df["cancer_type"].unique().tolist())


def generate_explanation(breakdown: dict) -> dict:
    """Generate human-readable explanation from CVS breakdown (v2)."""
    explanation = {}

    if breakdown["tumor_specificity"] > 0.85:
        explanation["tumor_specificity"] = "High tumor selectivity observed."
    else:
        explanation["tumor_specificity"] = "Moderate tumor selectivity."

    if breakdown["safety_component"] > 0.85:
        explanation["safety"] = "Low off-target toxicity risk."
    else:
        explanation["safety"] = "Potential normal tissue expression risk."

    if breakdown["stability"] > 0.85:
        explanation["stability"] = "Stable antigen expression."
    else:
        explanation["stability"] = "Variable expression stability."

    if breakdown["evidence"] > 0.9:
        explanation["literature_support"] = "Strong clinical literature backing."
    else:
        explanation["literature_support"] = "Moderate literature support."

    # v2: new feature explanations
    immunogenicity = breakdown.get("immunogenicity", 0.5)
    surface_access = breakdown.get("surface_accessibility", 0.5)

    if immunogenicity > 0.85:
        explanation["immunogenicity"] = "High immune recognition potential."
    elif immunogenicity > 0.60:
        explanation["immunogenicity"] = "Moderate immunogenicity."
    else:
        explanation["immunogenicity"] = "Low immunogenicity — may evade immune response."

    if surface_access > 0.85:
        explanation["surface_accessibility"] = "Membrane-bound — excellent CAR-T accessibility."
    elif surface_access > 0.50:
        explanation["surface_accessibility"] = "Partial surface expression."
    else:
        explanation["surface_accessibility"] = "Primarily intracellular — limited CAR-T targeting."

    summary = (
        f"{'High' if breakdown['tumor_specificity'] > 0.85 else 'Moderate'} tumor selectivity, "
        f"{'low' if (1 - breakdown['safety_component']) < 0.3 else 'moderate'} off-target risk, "
        f"{'stable' if breakdown['stability'] > 0.85 else 'variable'} expression, "
        f"{'strong' if breakdown['evidence'] > 0.9 else 'moderate'} clinical support, "
        f"{'high' if immunogenicity > 0.85 else 'moderate'} immunogenicity, "
        f"{'surface-accessible' if surface_access > 0.85 else 'partially accessible'}."
    )
    return {
        "details": explanation,
        "summary": summary,
    }
