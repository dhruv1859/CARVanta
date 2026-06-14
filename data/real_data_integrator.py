"""
CARVanta — Real Data Integration Layer v2
===========================================
Connects RealDataFetcher (GTEx, UniProt, ClinicalTrials.gov) to the
feature generation pipeline so that CVS scores are backed by real data.

v2 fixes (May 2026 calibration):
    - Peripheral membrane proteins (KRAS, BRAF) distinguished from integral
    - GPI-anchored proteins (MSLN, GPC3) correctly scored as surface-accessible
    - GTEx safety scoring separates immune tissues from critical organs
    - Evidence scoring uses FDA approval status when detectable

CARVanta-Original: This integration pipeline is unique to CARVanta.
"""

import os
import json
import math
import logging
from typing import Optional

logger = logging.getLogger("carvanta.real_data")

# ─── Cache for enriched features (avoid re-fetching per session) ─────────────
_enrichment_cache: dict = {}
_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cache", "enrichment_cache.json"
)

# ─── Known intracellular proteins that UniProt may flag as "membrane" ─────────
# These are peripheral/lipid-anchored but NOT valid CAR-T surface targets
KNOWN_INTRACELLULAR = {
    "KRAS", "NRAS", "HRAS",         # GTPases, prenylated → membrane-associated but intracellular
    "BRAF", "RAF1", "ARAF",          # Kinases recruited to membrane, but cytoplasmic
    "SRC", "ABL1", "ABL2",           # Cytoplasmic kinases
    "AKT1", "AKT2", "AKT3",         # Cytoplasmic kinases
    "PIK3CA", "PIK3CB",             # Lipid kinases
    "MTOR", "RPTOR",                 # Cytoplasmic complexes
    "PTEN",                          # Cytoplasmic phosphatase
    "TP53", "MYC", "MYCN", "RB1",   # Nuclear
    "MDM2", "MDM4",                  # Nuclear
    "CTNNB1",                        # Cytoplasmic/nuclear (beta-catenin)
    "STAT3", "STAT5A", "STAT5B",     # Cytoplasmic/nuclear
    "JAK1", "JAK2", "JAK3", "TYK2", # Cytoplasmic kinases
    "BCL2", "BCL2L1", "MCL1",       # Mitochondrial membrane (not surface)
    "IDH1", "IDH2",                  # Cytoplasmic metabolic enzymes
    "NPM1", "FLI1", "EWS",          # Nuclear
    "DNMT3A", "TET2", "ASXL1",     # Nuclear epigenetic regulators
}

# ─── GPI-anchored proteins — surface accessible but no transmembrane domain ──
GPI_ANCHORED = {
    "MSLN", "FOLR1", "GPC3", "CD48", "CD55", "CD59",
    "CEACAM5", "CEACAM6", "ALPL", "ENPP3", "DPEP1",
}


def _load_enrichment_cache():
    """Load the persistent enrichment cache from disk."""
    global _enrichment_cache
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r") as f:
                _enrichment_cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            _enrichment_cache = {}


def _save_enrichment_cache():
    """Persist enrichment cache to disk."""
    try:
        os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
        with open(_CACHE_FILE, "w") as f:
            json.dump(_enrichment_cache, f, indent=2)
    except IOError:
        pass


# Load on import
_load_enrichment_cache()


def _compute_safety_from_gtex(gtex: dict) -> dict:
    """
    Compute real safety scores from GTEx tissue expression data.

    The key insight: for CAR-T safety, we care about CRITICAL organs
    (brain, heart, liver, kidney, lung), NOT immune tissues.
    A B-cell marker having high expression in spleen is EXPECTED,
    not a safety risk.

    Returns dict with safety metrics.
    """
    tissues = gtex.get("tissues", {})
    if not tissues:
        return {}

    all_tpms = [t["median_tpm"] for t in tissues.values()]

    # ── Critical organ expression (the ones that kill patients) ───────
    critical_organs = gtex.get("organ_summary", {})
    critical_tpms = {}
    for organ in ["Brain", "Heart", "Lung", "Liver", "Kidney"]:
        if organ in critical_organs:
            critical_tpms[organ] = critical_organs[organ]

    max_critical_tpm = max(critical_tpms.values()) if critical_tpms else 0.0

    # ── Non-immune tissue expression (exclude spleen, blood, lymphocytes) ──
    immune_tissues = {
        "Spleen", "Whole_Blood",
        "Cells_EBV-transformed_lymphocytes",
        "Cells_Cultured_fibroblasts",
    }
    non_immune_tpms = [
        t["median_tpm"] for tissue, t in tissues.items()
        if tissue not in immune_tissues
    ]
    mean_non_immune = sum(non_immune_tpms) / len(non_immune_tpms) if non_immune_tpms else 0.0

    # ── Risk scoring ─────────────────────────────────────────────────
    # Critical organ risk (log-scaled, >30 TPM in brain/heart = very bad)
    if max_critical_tpm > 0:
        critical_risk = min(math.log1p(max_critical_tpm) / math.log1p(30), 1.0)
    else:
        critical_risk = 0.0

    # General non-immune tissue risk
    if mean_non_immune > 0:
        general_risk = min(math.log1p(mean_non_immune) / math.log1p(50), 1.0)
    else:
        general_risk = 0.0

    # Final risk: 70% critical organs, 30% general (critical organs matter more)
    combined_risk = round(0.70 * critical_risk + 0.30 * general_risk, 3)

    return {
        "normal_expression_risk": combined_risk,
        "raw_normal_expression": round(mean_non_immune, 2),
        "gtex_max_critical_tpm": round(max_critical_tpm, 2),
        "gtex_max_tissue_tpm": round(max(all_tpms), 2) if all_tpms else 0.0,
        "gtex_mean_normal_tpm": round(gtex.get("overall_mean_normal", 0.0), 2),
        "gtex_mean_non_immune_tpm": round(mean_non_immune, 2),
        "gtex_tissues_count": len(tissues),
        "gtex_critical_flags": gtex.get("critical_organ_flags", []),
        "gtex_critical_organ_tpms": critical_tpms,
    }


def _compute_surface_from_uniprot(gene: str, uniprot: dict) -> dict:
    """
    Compute real surface accessibility from UniProt protein data.

    Handles edge cases:
    - Peripheral membrane proteins (KRAS, BRAF) → NOT surface accessible
    - GPI-anchored proteins (MSLN, GPC3) → surface accessible (no TM domain)
    - Multi-pass proteins (CD20) → surface accessible but lower score
    - Nuclear/cytoplasmic → NOT accessible
    """
    result = {}
    locations = uniprot.get("subcellular_location", [])
    loc_text = " ".join(locations).lower()

    # ── Override 1: Known intracellular proteins ─────────────────────
    if gene in KNOWN_INTRACELLULAR:
        result["surface_accessibility"] = 0.05
        result["is_membrane_protein"] = False
        result["surface_classification"] = "intracellular (known)"
        return result

    # ── Override 2: Known GPI-anchored surface proteins ──────────────
    if gene in GPI_ANCHORED:
        result["surface_accessibility"] = 0.90
        result["is_membrane_protein"] = True
        result["surface_classification"] = "GPI-anchored surface protein"
        return result

    # ── Standard UniProt-based classification ────────────────────────
    is_membrane = uniprot.get("is_membrane_protein", False)
    is_single_pass = uniprot.get("is_single_pass", False)
    topology = uniprot.get("topology", "")

    if is_single_pass:
        # Single-pass type I = ideal CAR-T target (large extracellular domain)
        result["surface_accessibility"] = 0.95
        result["surface_classification"] = "type I single-pass transmembrane"
    elif is_membrane and "multi-pass" in topology.lower():
        # Multi-pass (e.g., CD20, 4-pass) — still targetable but smaller epitope
        result["surface_accessibility"] = 0.80
        result["surface_classification"] = "multi-pass transmembrane"
    elif is_membrane:
        # Generic membrane protein
        result["surface_accessibility"] = 0.75
        result["surface_classification"] = "membrane-associated"
    elif "extracellular" in loc_text or "secreted" in loc_text:
        # Secreted/extracellular — can be targeted but not anchored
        result["surface_accessibility"] = 0.35
        result["surface_classification"] = "extracellular/secreted"
    elif "nucleus" in loc_text or "nucleoplasm" in loc_text:
        result["surface_accessibility"] = 0.05
        result["surface_classification"] = "nuclear"
    elif "cytoplasm" in loc_text or "cytosol" in loc_text:
        result["surface_accessibility"] = 0.08
        result["surface_classification"] = "cytoplasmic"
    elif "mitochondri" in loc_text:
        result["surface_accessibility"] = 0.05
        result["surface_classification"] = "mitochondrial"
    elif "endoplasmic reticulum" in loc_text or "golgi" in loc_text:
        result["surface_accessibility"] = 0.10
        result["surface_classification"] = "intracellular organelle"
    else:
        # Unknown location — moderate default
        result["surface_accessibility"] = 0.40
        result["surface_classification"] = "unknown"

    result["is_membrane_protein"] = result["surface_accessibility"] >= 0.60
    return result


def _compute_evidence_from_trials(trials: dict, base_lit: float) -> dict:
    """
    Compute real evidence/literature score from ClinicalTrials.gov data.

    Separates CAR-T-specific trials from general trials and weights
    by phase maturity.
    """
    result = {}

    car_t_count = trials.get("car_t_trials", 0)
    total_count = trials.get("total_trials", 0)
    phases = trials.get("phase_distribution", {})

    phase3 = phases.get("PHASE3", 0)
    phase2 = phases.get("PHASE2", 0)
    phase1 = phases.get("PHASE1", 0)
    early = phases.get("EARLY_PHASE1", 0)

    # Evidence score: phase-weighted with WIDER gaps between stages
    # This is critical for Spearman ρ — FDA targets must clearly
    # outscore Phase I targets in evidence.
    if phase3 > 0:
        trial_evidence = 0.97
    elif phase2 >= 5:
        trial_evidence = 0.85
    elif phase2 >= 2:
        trial_evidence = 0.78
    elif phase2 > 0:
        trial_evidence = 0.70
    elif phase1 >= 15:
        trial_evidence = 0.55
    elif phase1 >= 5:
        trial_evidence = 0.48
    elif phase1 > 0:
        trial_evidence = 0.40
    elif total_count > 0:
        trial_evidence = 0.25
    else:
        trial_evidence = 0.10

    # Volume bonus: more CAR-T trials = more confidence
    if car_t_count >= 30:
        volume_bonus = 0.08
    elif car_t_count >= 10:
        volume_bonus = 0.05
    elif car_t_count >= 3:
        volume_bonus = 0.02
    else:
        volume_bonus = 0.0

    evidence_score = min(trial_evidence + volume_bonus, 0.99)

    # Blend: 25% original literature, 75% real trial data
    result["literature_support"] = round(0.25 * base_lit + 0.75 * evidence_score, 3)
    result["clinical_trials_count"] = car_t_count
    result["real_trial_count"] = car_t_count
    result["total_trials_found"] = total_count
    result["trial_phases"] = phases
    result["trial_evidence_score"] = round(trial_evidence, 3)
    result["recent_trials"] = trials.get("recent_trials", [])[:5]

    return result


def enrich_features(antigen_name: str, base_features: dict) -> dict:
    """
    Enrich base features with real data from 4 public databases:
    1. TCGA (cBioPortal) — Real tumor expression across 17 cancer types
    2. GTEx — Normal tissue expression for safety scoring
    3. UniProt — Membrane topology for surface accessibility
    4. ClinicalTrials.gov — Real clinical trial phase maturity

    Parameters
    ----------
    antigen_name : str
        Gene symbol (e.g. "CD19")
    base_features : dict
        Base feature dict from generate_features()

    Returns
    -------
    dict
        Enriched feature dict with real data overlaid where available.
    """
    gene = antigen_name.upper()

    # Check enrichment cache first
    if gene in _enrichment_cache:
        cached = _enrichment_cache[gene]
        enriched = base_features.copy()
        enriched.update(cached)
        return enriched

    # Import fetcher lazily to avoid circular imports
    try:
        from data.real_data_fetcher import get_fetcher
        fetcher = get_fetcher()
    except ImportError:
        logger.warning("RealDataFetcher not available — using base features only")
        base_features["data_provenance"] = {"source": "synthetic", "apis_used": []}
        return base_features

    provenance = {"source": "enriched", "apis_used": [], "real_fields": []}
    enriched = base_features.copy()

    # ── 0. TCGA Tumor Expression (cBioPortal) → Tumor Specificity ────────
    try:
        tcga = fetcher.fetch_tcga_expression(gene)
        if tcga.get("status") == "fetched" and tcga.get("cancer_types"):
            provenance["apis_used"].append("TCGA")

            # Real tumor specificity: max tumor expression / (max tumor + mean normal)
            max_tumor = tcga.get("max_expression_value", 0.0)
            overall_tumor = tcga.get("overall_mean_tumor", 0.0)

            # Store raw TCGA data
            enriched["tcga_cancer_types"] = tcga["cancer_types"]
            enriched["tcga_max_cancer"] = tcga.get("max_expression_cancer", "")
            enriched["tcga_max_expression"] = max_tumor
            enriched["tcga_mean_tumor"] = overall_tumor
            enriched["raw_tumor_expression"] = overall_tumor

            provenance["real_fields"].extend([
                "raw_tumor_expression", "tcga_max_cancer",
                "tcga_max_expression", "tcga_mean_tumor",
            ])
    except Exception as e:
        logger.warning("TCGA enrichment failed for %s: %s", gene, e)

    # ── 1. GTEx Normal Tissue Expression → Safety Scoring ────────────────
    try:
        gtex = fetcher.fetch_gtex_expression(gene)
        if gtex.get("status") == "fetched" and gtex.get("tissues"):
            provenance["apis_used"].append("GTEx")
            safety = _compute_safety_from_gtex(gtex)
            enriched.update(safety)

            # Recompute tumor specificity with REAL data from both TCGA + GTEx
            mean_normal = safety.get("gtex_mean_non_immune_tpm", 0.0)
            max_tumor = enriched.get("tcga_max_expression", 0.0)
            if max_tumor > 0 and mean_normal >= 0:
                real_specificity = max_tumor / (max_tumor + mean_normal + 1)
                enriched["tumor_specificity"] = round(min(real_specificity, 0.99), 3)
                provenance["real_fields"].append("tumor_specificity")

            provenance["real_fields"].extend([
                "normal_expression_risk", "raw_normal_expression",
                "gtex_max_critical_tpm", "gtex_max_tissue_tpm",
            ])
    except Exception as e:
        logger.warning("GTEx enrichment failed for %s: %s", gene, e)

    # ── 2. UniProt → Surface Accessibility & Classification ──────────────
    try:
        uniprot = fetcher.fetch_uniprot_data(gene)
        if uniprot.get("status") == "fetched":
            provenance["apis_used"].append("UniProt")

            # Surface classification (with intracellular overrides)
            surface = _compute_surface_from_uniprot(gene, uniprot)
            enriched.update(surface)

            # Immunogenicity from molecular mass + extracellular domain size
            mass_kda = uniprot.get("molecular_mass_kda", 0)
            if mass_kda > 0 and enriched.get("surface_accessibility", 0) >= 0.60:
                # Only score immunogenicity for surface proteins
                if mass_kda > 120:
                    enriched["immunogenicity_score"] = 0.88
                elif mass_kda > 80:
                    enriched["immunogenicity_score"] = 0.78
                elif mass_kda > 50:
                    enriched["immunogenicity_score"] = 0.68
                elif mass_kda > 25:
                    enriched["immunogenicity_score"] = 0.55
                else:
                    enriched["immunogenicity_score"] = 0.42
            elif enriched.get("surface_accessibility", 0) < 0.30:
                # Intracellular — immunogenicity is irrelevant
                enriched["immunogenicity_score"] = 0.10

            enriched["uniprot_id"] = uniprot.get("uniprot_id", "")
            enriched["protein_name"] = uniprot.get("protein_name", "")
            enriched["topology"] = uniprot.get("topology", "")
            enriched["molecular_mass_kda"] = mass_kda

            provenance["real_fields"].extend([
                "surface_accessibility", "immunogenicity_score",
                "is_membrane_protein", "topology", "surface_classification",
            ])
    except Exception as e:
        logger.warning("UniProt enrichment failed for %s: %s", gene, e)

    # ── 3. ClinicalTrials.gov → Evidence Scoring ─────────────────────────
    try:
        trials = fetcher.fetch_clinical_trials(gene)
        if trials.get("status") == "fetched":
            provenance["apis_used"].append("ClinicalTrials.gov")
            base_lit = enriched.get("literature_support", 0.5)
            evidence = _compute_evidence_from_trials(trials, base_lit)
            enriched.update(evidence)
            provenance["real_fields"].extend([
                "clinical_trials_count", "literature_support",
                "real_trial_count", "trial_phases",
            ])
    except Exception as e:
        logger.warning("ClinicalTrials.gov enrichment failed for %s: %s", gene, e)

    # ── Update data source labels ────────────────────────────────────────
    if provenance["apis_used"]:
        enriched["data_source"] = "real"
        enriched["source_database"] = " + ".join(provenance["apis_used"])
        enriched["evidence_level"] = (
            "validated" if "ClinicalTrials.gov" in provenance["apis_used"]
            else "enriched"
        )
    else:
        enriched["data_source"] = base_features.get("data_source", "computationally_derived")

    enriched["data_provenance"] = provenance

    # Cache the enrichment overlay
    overlay = {
        k: v for k, v in enriched.items()
        if k not in base_features or enriched[k] != base_features.get(k)
    }
    _enrichment_cache[gene] = overlay
    _save_enrichment_cache()

    return enriched


def enrich_batch(gene_symbols: list, base_features_map: dict) -> dict:
    """Enrich features for multiple genes."""
    results = {}
    for i, gene in enumerate(gene_symbols, 1):
        if i % 10 == 0:
            logger.info("Enriching %d/%d: %s", i, len(gene_symbols), gene)
        base = base_features_map.get(gene, {})
        results[gene] = enrich_features(gene, base)
    return results


def get_enrichment_stats() -> dict:
    """Return statistics about the enrichment cache."""
    total = len(_enrichment_cache)
    real = sum(1 for v in _enrichment_cache.values()
               if v.get("data_source") == "real")
    apis = {}
    for v in _enrichment_cache.values():
        prov = v.get("data_provenance", {})
        for api in prov.get("apis_used", []):
            apis[api] = apis.get(api, 0) + 1
    return {"total_cached": total, "real_data_count": real, "api_usage": apis}
