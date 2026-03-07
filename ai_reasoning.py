"""
CARVanta – AI Reasoning Engine v4
=====================================
CARVanta-Original: Custom rule-based AI reasoning that generates
intelligent, context-aware insights based on antigen scoring data.

This is NOT a copy of any external AI — it is a CARVanta-original
reasoning engine that uses domain-specific biomarker knowledge to
produce unique, data-driven insights for each antigen evaluation.

The engine analyzes:
1. Score patterns and component relationships
2. Safety-efficacy tradeoffs
3. Cancer-type-specific context
4. Clinical trial evidence strength
5. Comparative positioning against known benchmarks
"""


# ─── Benchmark targets (known clinical-grade antigens) ─────────────────────────
BENCHMARK_TARGETS = {
    "CD19":     {"cancer": "Leukemia", "status": "FDA-approved", "cvs_benchmark": 0.92},
    "BCMA":     {"cancer": "Myeloma",  "status": "FDA-approved", "cvs_benchmark": 0.90},
    "CD22":     {"cancer": "Leukemia", "status": "Phase III",    "cvs_benchmark": 0.85},
    "HER2":     {"cancer": "Breast Cancer", "status": "Phase II", "cvs_benchmark": 0.78},
    "GD2":      {"cancer": "Melanoma", "status": "Phase II",     "cvs_benchmark": 0.80},
    "EGFR":     {"cancer": "Glioblastoma", "status": "Phase I/II", "cvs_benchmark": 0.72},
    "MESOTHELIN": {"cancer": "Mesothelioma", "status": "Phase II", "cvs_benchmark": 0.75},
    "PSMA":     {"cancer": "Prostate Cancer", "status": "Phase I", "cvs_benchmark": 0.70},
}

# ─── Feature significance thresholds ──────────────────────────────────────────
THRESHOLDS = {
    "tumor_specificity":      {"excellent": 0.85, "good": 0.70, "poor": 0.50},
    "normal_expression_risk":  {"safe": 0.15,     "moderate": 0.30, "dangerous": 0.50},
    "stability_score":        {"stable": 0.80,    "moderate": 0.60, "unstable": 0.40},
    "immunogenicity_score":   {"strong": 0.75,    "moderate": 0.50, "weak": 0.30},
    "surface_accessibility":  {"accessible": 0.70, "moderate": 0.50, "poor": 0.30},
    "literature_support":     {"strong": 0.70,    "moderate": 0.40, "weak": 0.20},
}


def generate_ai_insight(cvs, ml_pred, ml_conf, antigen_name="", features=None):
    """
    CARVanta-Original: Generate primary AI insight.

    Analyzes agreement between rule-based CVS and ML prediction,
    then provides a nuanced, antigen-specific interpretation.
    """
    antigen = antigen_name.upper() if antigen_name else "This antigen"

    # Check if it's a benchmark target
    benchmark = BENCHMARK_TARGETS.get(antigen, None)
    benchmark_note = ""
    if benchmark:
        benchmark_note = (
            f" {antigen} is a {benchmark['status']} CAR-T target for "
            f"{benchmark['cancer']}, making this evaluation clinically grounded."
        )

    # ── Analyze model agreement ──────────────────────────────────────────────
    if cvs >= 0.85 and ml_pred == 1 and ml_conf >= 0.90:
        agreement = "strong_agree_positive"
    elif cvs >= 0.85 and ml_pred == 1:
        agreement = "agree_positive"
    elif cvs < 0.55 and ml_pred == 0 and ml_conf >= 0.85:
        agreement = "strong_agree_negative"
    elif cvs < 0.55 and ml_pred == 0:
        agreement = "agree_negative"
    elif cvs >= 0.70 and ml_pred == 0:
        agreement = "conflict_cvs_positive"
    elif cvs < 0.65 and ml_pred == 1:
        agreement = "conflict_ml_positive"
    elif ml_conf < 0.60:
        agreement = "uncertain"
    elif cvs >= 0.70 and ml_pred == 1:
        agreement = "moderate_positive"
    else:
        agreement = "mixed"

    # ── Generate insight based on agreement pattern ──────────────────────────
    insights = {
        "strong_agree_positive": (
            f"{antigen} demonstrates exceptional CAR-T target potential with "
            f"a CVS of {cvs:.3f} and high ML confidence ({ml_conf:.1%}). "
            f"Both scoring engines converge on strong viability — this indicates "
            f"robust tumor specificity coupled with an acceptable safety profile.{benchmark_note}"
        ),
        "agree_positive": (
            f"{antigen} shows strong promise as a CAR-T target (CVS: {cvs:.3f}, "
            f"ML confidence: {ml_conf:.1%}). The rule-based and ML models agree "
            f"on viability, though the ML shows moderate confidence, suggesting "
            f"some features may need further biological validation.{benchmark_note}"
        ),
        "strong_agree_negative": (
            f"{antigen} is not recommended as a CAR-T target at this time "
            f"(CVS: {cvs:.3f}). Both models strongly indicate low viability — "
            f"this is likely due to insufficient tumor specificity, elevated "
            f"normal tissue expression, or inadequate clinical evidence."
        ),
        "agree_negative": (
            f"{antigen} shows limited CAR-T therapeutic potential (CVS: {cvs:.3f}). "
            f"The scoring models agree on low viability. Consider this antigen only "
            f"if combination therapy or engineered safety switches are planned."
        ),
        "conflict_cvs_positive": (
            f"Interesting divergence for {antigen}: the rule-based CVS ({cvs:.3f}) "
            f"suggests viability, but the ML model predicts non-viability "
            f"(confidence: {ml_conf:.1%}). This pattern often indicates that "
            f"while individual features look promising, the ML has learned "
            f"interactions between features that raise concerns. Further "
            f"experimental validation is strongly recommended."
        ),
        "conflict_ml_positive": (
            f"Notable pattern for {antigen}: the ML model predicts viability "
            f"despite a lower CVS ({cvs:.3f}). This can occur when the ML "
            f"identifies non-obvious feature combinations that outperform "
            f"the weighted linear scoring of CVS. This target may have "
            f"underappreciated therapeutic potential worth investigating."
        ),
        "uncertain": (
            f"The ML model is uncertain about {antigen} (confidence: {ml_conf:.1%}). "
            f"With a CVS of {cvs:.3f}, this antigen falls in a decision boundary "
            f"where small changes in expression data could shift the prediction. "
            f"Recommend repeating analysis with cancer-specific expression data."
        ),
        "moderate_positive": (
            f"{antigen} shows moderate-to-good CAR-T target potential "
            f"(CVS: {cvs:.3f}, ML viable with {ml_conf:.1%} confidence). "
            f"This positions it as a Tier 2 candidate — promising but requiring "
            f"additional preclinical characterization before clinical advancement."
        ),
        "mixed": (
            f"{antigen} presents a complex scoring profile (CVS: {cvs:.3f}, "
            f"ML confidence: {ml_conf:.1%}). The models show partial agreement. "
            f"Review individual component scores to identify specific strengths "
            f"and weaknesses before making a clinical development decision."
        ),
    }

    return insights.get(agreement, insights["mixed"])


def generate_deep_insight(cvs, prediction, contributions, features=None, antigen_name=""):
    """
    CARVanta-Original: Generate detailed feature-level insight.

    Analyzes which biological features drive the prediction and
    identifies specific actionable opportunities or concerns.
    """
    if not contributions:
        return "Insufficient feature data for detailed analysis. Run full scoring to generate feature contributions."

    antigen = antigen_name.upper() if antigen_name else "This antigen"

    # ── Identify top drivers and limiters ────────────────────────────────────
    sorted_contrib = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    top_driver = sorted_contrib[0]
    limiter = sorted_contrib[-1]

    # ── Feature labels (human-readable) ──────────────────────────────────────
    labels = {
        "tumor_specificity": "tumor specificity",
        "normal_expression_risk": "normal tissue expression risk",
        "safety_margin": "safety margin",
        "stability_score": "expression stability",
        "literature_support": "clinical evidence base",
        "immunogenicity_score": "immune recognition potential",
        "surface_accessibility": "surface accessibility for CAR binding",
        "clinical_boost": "clinical trial evidence",
        "composite_score": "overall composite score",
    }

    driver_label = labels.get(top_driver[0], top_driver[0])
    limiter_label = labels.get(limiter[0], limiter[0])

    # ── Build detailed analysis ──────────────────────────────────────────────
    sections = []

    # Driver analysis
    if top_driver[1] > 0.15:
        sections.append(
            f"**Primary strength:** {driver_label} is the dominant positive factor "
            f"(contribution: +{top_driver[1]:.3f}), indicating that {antigen} excels "
            f"in this dimension compared to the training population."
        )
    else:
        sections.append(
            f"**Balanced profile:** No single feature dominates the prediction — "
            f"{driver_label} leads marginally (+{top_driver[1]:.3f}), suggesting "
            f"a well-rounded target without extreme strengths or weaknesses."
        )

    # Limiter analysis
    if limiter[1] < -0.05:
        sections.append(
            f"**Key limitation:** {limiter_label} is actively reducing the score "
            f"({limiter[1]:+.3f}). Improving this dimension through engineering "
            f"(e.g., affinity tuning, safety switches) could significantly "
            f"enhance therapeutic viability."
        )
    elif limiter[1] < 0.02:
        sections.append(
            f"**Minor concern:** {limiter_label} contributes minimally "
            f"({limiter[1]:+.3f}). While not actively harmful, strengthening "
            f"this aspect could elevate the overall profile."
        )

    # ── Specific feature warnings ────────────────────────────────────────────
    if features:
        ts = features.get("tumor_specificity", 0.5)
        ner = features.get("normal_expression_risk", 0.5)
        stab = features.get("stability_score", 0.5)
        imm = features.get("immunogenicity_score", 0.5)
        surf = features.get("surface_accessibility", 0.5)

        if ner > 0.40:
            sections.append(
                f"⚠️ **Toxicity alert:** Normal tissue expression risk is elevated "
                f"({ner:.3f}). CAR-T cells may attack healthy organs. Consider "
                f"incorporating a safety switch (e.g., inducible caspase-9) or "
                f"using affinity-tuned scFv domains."
            )

        if ts > 0.85 and ner < 0.15:
            sections.append(
                f"✅ **Ideal therapeutic window:** High tumor specificity ({ts:.3f}) "
                f"with low normal tissue risk ({ner:.3f}) creates an excellent "
                f"therapeutic index — the hallmark of a safe and effective target."
            )

        if stab < 0.50:
            sections.append(
                f"⚠️ **Stability concern:** Expression stability is low ({stab:.3f}). "
                f"This antigen may be heterogeneously expressed, leading to "
                f"incomplete tumor killing and potential antigen-negative relapse."
            )

        if imm > 0.80:
            sections.append(
                f"✅ **Strong immunogenicity:** High immune recognition ({imm:.3f}) "
                f"supports robust CAR-T cell activation and killing efficiency."
            )

        if surf < 0.40:
            sections.append(
                f"⚠️ **Accessibility issue:** Low surface accessibility ({surf:.3f}) "
                f"may reduce CAR binding efficiency. This antigen might be partially "
                f"intracellular or sterically obscured."
            )

    # ── Overall assessment ───────────────────────────────────────────────────
    viability = "viable" if prediction == 1 else "non-viable"
    if cvs >= 0.85:
        sections.append(
            f"**Assessment:** With a CVS of {cvs:.3f}, {antigen} is a high-priority "
            f"CAR-T target candidate suitable for preclinical development."
        )
    elif cvs >= 0.70:
        sections.append(
            f"**Assessment:** CVS of {cvs:.3f} positions {antigen} as a candidate "
            f"worth advancing to validation studies, with attention to the "
            f"limitations identified above."
        )
    elif cvs >= 0.55:
        sections.append(
            f"**Assessment:** CVS of {cvs:.3f} places {antigen} in the experimental "
            f"category. Significant additional characterization is needed before "
            f"clinical consideration."
        )
    else:
        sections.append(
            f"**Assessment:** CVS of {cvs:.3f} indicates {antigen} is currently "
            f"not suitable for CAR-T development. Consider alternative targets "
            f"or novel engineering approaches."
        )

    return " ".join(sections)


def generate_safety_insight(features, antigen_name=""):
    """
    CARVanta-Original: Generate safety-specific AI reasoning.

    Provides a detailed safety assessment based on normal tissue
    expression, toxicity risk, and therapeutic index.
    """
    antigen = antigen_name.upper() if antigen_name else "This antigen"

    ner = features.get("normal_expression_risk", 0.5)
    ts = features.get("tumor_specificity", 0.5)
    sm = features.get("safety_margin", 0.5)
    stab = features.get("stability_score", 0.5)

    therapeutic_index = ts / max(ner, 0.01)  # Higher = safer

    sections = []

    # Overall safety classification
    if ner < 0.10 and sm > 0.90:
        sections.append(
            f"🟢 **Excellent safety profile.** {antigen} shows minimal normal tissue "
            f"expression (risk: {ner:.3f}) with a wide safety margin ({sm:.3f}). "
            f"Therapeutic index: {therapeutic_index:.1f}x — this means tumor expression "
            f"is {therapeutic_index:.0f}× higher than normal tissue, providing a large "
            f"window for selective killing."
        )
    elif ner < 0.25 and sm > 0.70:
        sections.append(
            f"🔵 **Favorable safety profile.** {antigen} has manageable normal tissue "
            f"risk ({ner:.3f}) and adequate safety margin ({sm:.3f}). "
            f"Therapeutic index: {therapeutic_index:.1f}x. Standard monitoring "
            f"protocols should be sufficient."
        )
    elif ner < 0.40:
        sections.append(
            f"🟡 **Moderate safety concern.** {antigen} shows notable normal tissue "
            f"expression (risk: {ner:.3f}). Safety margin: {sm:.3f}. "
            f"Therapeutic index: {therapeutic_index:.1f}x. Consider dose titration "
            f"strategies and enhanced toxicity monitoring in clinical protocols."
        )
    else:
        sections.append(
            f"🔴 **Significant safety risk.** {antigen} has high normal tissue "
            f"expression (risk: {ner:.3f}) with a narrow safety margin ({sm:.3f}). "
            f"Therapeutic index: only {therapeutic_index:.1f}x. Engineering safety "
            f"mechanisms (kill switches, logic-gated CARs, or masked CARs) are "
            f"essential before clinical advancement."
        )

    # Stability implications for safety
    if stab < 0.60:
        sections.append(
            f"Note: Expression instability ({stab:.3f}) adds unpredictability — "
            f"some patients may experience variable on-target/off-tumor toxicity."
        )

    return " ".join(sections)


def generate_comparison_insight(results):
    """
    CARVanta-Original: Generate comparative AI insight for antigen comparison.

    Identifies the best candidate and explains WHY it wins,
    not just that it has the highest score.
    """
    if not results:
        return "No antigens to compare."

    sorted_results = sorted(results, key=lambda x: x.get("CVS", 0), reverse=True)
    best = sorted_results[0]
    worst = sorted_results[-1]

    best_name = best.get("antigen", "Unknown")
    worst_name = worst.get("antigen", "Unknown")
    best_cvs = best.get("CVS", 0)
    worst_cvs = worst.get("CVS", 0)
    gap = best_cvs - worst_cvs

    sections = []

    sections.append(
        f"**Recommended: {best_name}** (CVS: {best_cvs:.3f}) "
        f"outperforms the field by a margin of {gap:.3f} over the lowest-ranked candidate."
    )

    if gap < 0.05:
        sections.append(
            "The candidates are closely matched — selection should be based on "
            "cancer-type-specific expression data, safety profile, and clinical "
            "trial landscape rather than CVS alone."
        )
    elif gap > 0.20:
        sections.append(
            f"{best_name} is substantially ahead of alternatives. "
            f"This gap suggests it has fundamentally better biological "
            f"characteristics for CAR-T targeting."
        )

    benchmark = BENCHMARK_TARGETS.get(best_name.upper())
    if benchmark:
        sections.append(
            f"{best_name} is a {benchmark['status']} target for "
            f"{benchmark['cancer']}, lending additional clinical credibility."
        )

    return " ".join(sections)


def generate_global_insight(best_antigen):
    """
    CARVanta-Original: Generate global leaderboard insight.
    """
    if not best_antigen:
        return "No candidates identified in the current ranking."

    name = best_antigen.get("antigen", "Unknown")
    cvs = best_antigen.get("CVS", 0)
    tier = best_antigen.get("tier", "")

    benchmark = BENCHMARK_TARGETS.get(name.upper())

    if cvs > 0.90:
        insight = (
            f"**{name}** leads the global ranking with an exceptional "
            f"CVS of {cvs:.3f} ({tier}). This indicates best-in-class "
            f"tumor specificity, safety profile, and clinical evidence."
        )
    elif cvs > 0.80:
        insight = (
            f"**{name}** tops the ranking with a strong CVS of {cvs:.3f} "
            f"({tier}). This target shows broad therapeutic potential "
            f"across multiple evaluation criteria."
        )
    elif cvs > 0.65:
        insight = (
            f"**{name}** leads with a moderate CVS of {cvs:.3f} ({tier}). "
            f"While promising, no standout Tier 1 candidates emerged — "
            f"consider cancer-specific filtering for more targeted results."
        )
    else:
        insight = (
            f"**{name}** leads the ranking but with a modest CVS of {cvs:.3f}. "
            f"This suggests the current candidate pool lacks strong CAR-T targets. "
            f"Consider expanding the search or adjusting cancer type filters."
        )

    if benchmark:
        insight += (
            f" Note: {name} is a {benchmark['status']} target, "
            f"adding real-world clinical validation to this ranking."
        )

    return insight


def generate_synergy_insight(synergy_data):
    """
    CARVanta-Original: Generate multi-target synergy AI insight.
    """
    antigens = synergy_data.get("antigens", [])
    synergy = synergy_data.get("synergy_score", 0)
    comp = synergy_data.get("complementarity", 0)
    escape = synergy_data.get("escape_risk_reduction", 0)
    coverage = synergy_data.get("combined_coverage", 0)

    combo_name = " + ".join(antigens)
    sections = []

    if synergy >= 0.80:
        sections.append(
            f"**Excellent synergy detected.** The {combo_name} combination "
            f"scores {synergy:.3f}, indicating strong multi-target potential."
        )
    elif synergy >= 0.65:
        sections.append(
            f"**Good synergy.** The {combo_name} combination ({synergy:.3f}) "
            f"shows complementary targeting that improves upon individual targets."
        )
    else:
        sections.append(
            f"**Limited synergy.** The {combo_name} combination ({synergy:.3f}) "
            f"does not show significant benefit over individual targeting."
        )

    if escape > 0.85:
        sections.append(
            f"Escape risk is dramatically reduced ({escape:.3f}) — tumor cells "
            f"would need to downregulate {len(antigens)} antigens simultaneously "
            f"to evade this therapy."
        )

    if comp > 0.60:
        sections.append(
            f"Expression complementarity is strong ({comp:.3f}), meaning "
            f"these antigens cover different patient subpopulations effectively."
        )

    return " ".join(sections)


def generate_stratification_insight(strat_data):
    """
    CARVanta-Original: Generate patient stratification AI insight.
    """
    antigen = strat_data.get("antigen", "Unknown")
    cancer = strat_data.get("cancer_type", "cancer")
    eligibility = strat_data.get("estimated_eligibility_pct", 0)
    subtypes = strat_data.get("subtype_analysis", [])

    sections = []

    if eligibility >= 40:
        sections.append(
            f"**Broad eligibility.** An estimated {eligibility:.0f}% of "
            f"{cancer} patients could be eligible for {antigen}-targeted "
            f"CAR-T therapy, making this a commercially viable target."
        )
    elif eligibility >= 20:
        sections.append(
            f"**Moderate eligibility.** Approximately {eligibility:.0f}% of "
            f"{cancer} patients show sufficient {antigen} expression for "
            f"CAR-T targeting. Patient selection biomarkers are critical."
        )
    else:
        sections.append(
            f"**Limited eligibility.** Only ~{eligibility:.0f}% of {cancer} "
            f"patients would qualify. Consider combination strategies or "
            f"alternative antigen targets to expand coverage."
        )

    if subtypes:
        best_subtype = subtypes[0]
        sections.append(
            f"The highest-benefit subgroup is **{best_subtype['subtype']}** patients "
            f"(predicted benefit: {best_subtype['predicted_benefit']:.3f}, "
            f"~{best_subtype['population_share']} of cases)."
        )

    return " ".join(sections)