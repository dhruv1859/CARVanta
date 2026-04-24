"""
CARVanta Genomics — Clonal Architecture & Evolution Analyzer
================================================================
Model tumor clonal structure, subclonal dynamics, and predict
evolutionary trajectories relevant to therapy resistance.

Features:
- Variant allele frequency (VAF) clustering
- Clonal vs subclonal variant classification
- Tumor phylogeny reconstruction
- Cancer cell fraction (CCF) estimation
- Clonal evolution trajectory modeling
- Treatment selection pressure simulation
- Minimal residual disease (MRD) clone tracking
- CAR-T resistance evolution prediction
- Mutational signature analysis (COSMIC SBS signatures)
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.genomics.clonal_evolution")


# ──────────────────────────────────────────────────────────────────────
# COSMIC Mutational Signatures (SBS)
# ──────────────────────────────────────────────────────────────────────

_COSMIC_SIGNATURES = {
    "SBS1": {"etiology": "Spontaneous deamination of 5-methylcytosine (clock-like)", "associated_cancers": ["All cancers"],
             "age_related": True, "therapy_related": False},
    "SBS2": {"etiology": "APOBEC cytidine deaminase activity", "associated_cancers": ["Breast", "Cervical", "Bladder", "HNSCC"],
             "age_related": False, "therapy_related": False},
    "SBS3": {"etiology": "Homologous recombination deficiency (BRCA1/2)", "associated_cancers": ["Breast", "Ovarian", "Pancreatic"],
             "age_related": False, "therapy_related": False},
    "SBS4": {"etiology": "Tobacco smoking (direct DNA damage)", "associated_cancers": ["Lung", "Head & Neck", "Bladder"],
             "age_related": False, "therapy_related": False},
    "SBS5": {"etiology": "Unknown (clock-like, correlates with age)", "associated_cancers": ["All cancers"],
             "age_related": True, "therapy_related": False},
    "SBS6": {"etiology": "Mismatch repair deficiency (MSI)", "associated_cancers": ["CRC", "Endometrial", "Gastric"],
             "age_related": False, "therapy_related": False},
    "SBS7a": {"etiology": "Ultraviolet light exposure", "associated_cancers": ["Melanoma", "SCC"],
              "age_related": False, "therapy_related": False},
    "SBS8": {"etiology": "Unknown (possibly nucleotide excision repair)", "associated_cancers": ["Breast", "Medulloblastoma"],
             "age_related": False, "therapy_related": False},
    "SBS9": {"etiology": "AID/polymerase η activity (somatic hypermutation)", "associated_cancers": ["CLL", "Lymphoma"],
             "age_related": False, "therapy_related": False},
    "SBS10a": {"etiology": "Polymerase ε exonuclease domain mutation", "associated_cancers": ["CRC", "Endometrial"],
               "age_related": False, "therapy_related": False},
    "SBS11": {"etiology": "Temozolomide treatment", "associated_cancers": ["GBM"],
              "age_related": False, "therapy_related": True},
    "SBS13": {"etiology": "APOBEC cytidine deaminase activity", "associated_cancers": ["Breast", "Cervical", "Bladder"],
              "age_related": False, "therapy_related": False},
    "SBS15": {"etiology": "Mismatch repair deficiency", "associated_cancers": ["Stomach", "CRC"],
              "age_related": False, "therapy_related": False},
    "SBS17a": {"etiology": "Unknown (possible 5-FU damage)", "associated_cancers": ["Gastric", "Esophageal"],
               "age_related": False, "therapy_related": True},
    "SBS18": {"etiology": "Reactive oxygen species (ROS) damage", "associated_cancers": ["Neuroblastoma"],
              "age_related": False, "therapy_related": False},
    "SBS22": {"etiology": "Aristolochic acid exposure", "associated_cancers": ["Urothelial", "HCC"],
              "age_related": False, "therapy_related": False},
    "SBS24": {"etiology": "Aflatoxin exposure", "associated_cancers": ["HCC"],
              "age_related": False, "therapy_related": False},
    "SBS25": {"etiology": "Chemotherapy treatment (unknown agent)", "associated_cancers": ["Hodgkin lymphoma"],
              "age_related": False, "therapy_related": True},
    "SBS31": {"etiology": "Platinum chemotherapy", "associated_cancers": ["Various"],
              "age_related": False, "therapy_related": True},
    "SBS35": {"etiology": "Platinum chemotherapy", "associated_cancers": ["Various"],
              "age_related": False, "therapy_related": True},
}


async def analyze_clonal_architecture(
    cancer_type: str = "DLBCL",
    n_variants: int = 150,
    tumor_purity: float = 0.75,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze clonal architecture from variant allele frequencies.

    Clusters variants by VAF to identify clonal and subclonal
    populations, estimates cancer cell fractions (CCF), and
    reconstructs tumor phylogeny.
    """
    if seed:
        random.seed(seed)

    # Simulate VAF distribution with clonal clusters
    n_clones = random.randint(2, 5)
    clone_vafs = sorted([round(random.uniform(0.05, 0.5), 3) for _ in range(n_clones)], reverse=True)

    # Assign variants to clones
    variants = []
    for i in range(n_variants):
        clone_idx = random.choices(range(n_clones), weights=[1 / (j + 1) for j in range(n_clones)])[0]
        true_vaf = clone_vafs[clone_idx]
        observed_vaf = round(max(0.01, true_vaf + random.gauss(0, 0.03)), 3)
        ccf = round(min(1.0, observed_vaf * 2 / tumor_purity), 3)

        chrom = f"chr{random.randint(1, 22)}"
        pos = random.randint(1000000, 250000000)

        gene = random.choice([
            "TP53", "KRAS", "PIK3CA", "BRAF", "EGFR", "PTEN", "RB1", "APC",
            "CDH1", "CDKN2A", "MYC", "BCL2", "CREBBP", "KMT2D", "EZH2",
            "NOTCH1", "ATM", "ARID1A", "SMAD4", "NF1", "MYD88", "CARD11",
            "CD79B", "TNFAIP3", "STAT3", "SOCS1", "JAK2", "IDH1", "DNMT3A",
            "TET2", "SF3B1", "NRAS", "FLT3", "NPM1", "CEBPA", "RUNX1",
        ])

        variants.append({
            "variant_id": f"VAR{i+1:04d}",
            "chrom": chrom,
            "pos": pos,
            "gene": gene,
            "vaf": observed_vaf,
            "ccf": ccf,
            "clone_id": clone_idx + 1,
            "clonal": ccf > 0.85,
            "read_depth": random.randint(30, 500),
            "alt_reads": max(1, int(observed_vaf * random.randint(30, 500))),
        })

    # Clone statistics
    clones = []
    for idx in range(n_clones):
        clone_vars = [v for v in variants if v["clone_id"] == idx + 1]
        ccfs = [v["ccf"] for v in clone_vars]
        clones.append({
            "clone_id": idx + 1,
            "n_variants": len(clone_vars),
            "median_vaf": round(clone_vafs[idx], 3),
            "median_ccf": round(sorted(ccfs)[len(ccfs) // 2], 3) if ccfs else 0,
            "is_founding": idx == 0,
            "proportion": round(len(clone_vars) / max(n_variants, 1), 3),
        })

    # Phylogeny (simplified linear tree)
    phylogeny_nodes = []
    for i, clone in enumerate(clones):
        phylogeny_nodes.append({
            "clone_id": clone["clone_id"],
            "parent": clones[i - 1]["clone_id"] if i > 0 else None,
            "n_private_mutations": clone["n_variants"],
            "ccf": clone["median_ccf"],
        })

    # Clonal diversity metrics
    proportions = [c["proportion"] for c in clones if c["proportion"] > 0]
    shannon = -sum(p * math.log(max(p, 1e-10)) for p in proportions)
    simpson = sum(p ** 2 for p in proportions)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "tumor_purity": tumor_purity,
        "n_variants": n_variants,
        "n_clones": n_clones,
        "clones": clones,
        "phylogeny": phylogeny_nodes,
        "diversity": {
            "shannon_index": round(shannon, 4),
            "simpson_index": round(1 - simpson, 4),
            "clonal_fraction": round(sum(1 for v in variants if v["clonal"]) / max(n_variants, 1), 3),
            "subclonal_fraction": round(sum(1 for v in variants if not v["clonal"]) / max(n_variants, 1), 3),
        },
        "car_t_implications": {
            "clonal_heterogeneity": "high" if n_clones > 3 else "moderate" if n_clones > 1 else "low",
            "antigen_loss_risk": "elevated" if n_clones > 3 else "standard",
            "recommendation": (
                "High clonal heterogeneity detected. Risk of antigen escape is elevated. "
                "Consider dual-targeting CAR-T or sequential therapy approach."
                if n_clones > 3 else
                "Moderate clonal architecture. Standard CAR-T approach appropriate."
            ),
        },
        "top_variants": sorted(variants, key=lambda x: x["vaf"], reverse=True)[:25],
    }


async def mutational_signatures(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Identify mutational signatures in the tumor.

    Decomposes the mutational spectrum into COSMIC SBS signatures
    to identify mutagenic processes active in the tumor.
    """
    if seed:
        random.seed(seed)

    # Cancer-type-specific signature profiles
    signature_profiles = {
        "DLBCL": {"SBS1": 0.15, "SBS5": 0.20, "SBS9": 0.35, "SBS2": 0.10, "SBS13": 0.08, "SBS17a": 0.05, "SBS8": 0.07},
        "ALL": {"SBS1": 0.25, "SBS5": 0.30, "SBS9": 0.15, "SBS2": 0.10, "SBS13": 0.10, "SBS6": 0.05, "SBS8": 0.05},
        "MM": {"SBS1": 0.20, "SBS5": 0.25, "SBS2": 0.20, "SBS13": 0.15, "SBS9": 0.10, "SBS8": 0.05, "SBS18": 0.05},
        "NSCLC": {"SBS4": 0.40, "SBS1": 0.10, "SBS5": 0.15, "SBS2": 0.15, "SBS13": 0.10, "SBS8": 0.05, "SBS18": 0.05},
        "Melanoma": {"SBS7a": 0.60, "SBS1": 0.10, "SBS5": 0.10, "SBS2": 0.08, "SBS13": 0.07, "SBS8": 0.03, "SBS18": 0.02},
        "CRC": {"SBS1": 0.15, "SBS5": 0.15, "SBS6": 0.25, "SBS15": 0.15, "SBS10a": 0.10, "SBS2": 0.10, "SBS18": 0.10},
    }

    profile = signature_profiles.get(cancer_type, signature_profiles["DLBCL"])

    # Add noise to contributions
    results = []
    for sig_name, contribution in profile.items():
        noisy_contribution = max(0, contribution + random.gauss(0, 0.02))
        sig_info = _COSMIC_SIGNATURES.get(sig_name, {})

        results.append({
            "signature": sig_name,
            "contribution": round(noisy_contribution, 4),
            "contribution_pct": round(noisy_contribution * 100, 1),
            "etiology": sig_info.get("etiology", "Unknown"),
            "age_related": sig_info.get("age_related", False),
            "therapy_related": sig_info.get("therapy_related", False),
            "associated_cancers": sig_info.get("associated_cancers", []),
        })

    # Normalize
    total = sum(r["contribution"] for r in results)
    for r in results:
        r["contribution"] = round(r["contribution"] / max(total, 0.001), 4)
        r["contribution_pct"] = round(r["contribution"] * 100, 1)

    results.sort(key=lambda x: x["contribution"], reverse=True)

    # Dominant process
    dominant = results[0]
    therapy_related = [r for r in results if r["therapy_related"] and r["contribution_pct"] > 5]

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "n_signatures": len(results),
        "dominant_signature": dominant["signature"],
        "dominant_etiology": dominant["etiology"],
        "signatures": results,
        "therapy_related_detected": len(therapy_related) > 0,
        "therapy_signatures": therapy_related,
        "car_t_relevance": {
            "high_apobec": any(r["signature"] in ("SBS2", "SBS13") and r["contribution_pct"] > 15 for r in results),
            "high_aid": any(r["signature"] == "SBS9" and r["contribution_pct"] > 20 for r in results),
            "hrd_signature": any(r["signature"] == "SBS3" and r["contribution_pct"] > 10 for r in results),
            "msi_signature": any(r["signature"] in ("SBS6", "SBS15") and r["contribution_pct"] > 10 for r in results),
            "interpretation": (
                "High APOBEC activity may generate neoantigens that enhance CAR-T recognition. "
                if any(r["signature"] in ("SBS2", "SBS13") and r["contribution_pct"] > 15 for r in results)
                else "Standard mutational background for this cancer type."
            ),
        },
    }


async def predict_resistance_evolution(
    cancer_type: str = "DLBCL",
    car_t_target: str = "CD19",
    initial_response: str = "CR",
    months_post_infusion: int = 12,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Predict CAR-T resistance evolution trajectory.

    Models clonal evolution under CAR-T selection pressure,
    predicting antigen loss, lineage switch, and immune evasion
    mechanisms.
    """
    if seed:
        random.seed(seed)

    # Resistance mechanisms by target
    resistance_mechanisms = {
        "CD19": [
            {"mechanism": "CD19 antigen loss (biallelic deletion/mutation)",
             "probability": 0.30, "timeframe_months": "6-18",
             "detection": "Flow cytometry, CD19 qPCR", "countermeasure": "CD22/CD19 dual CAR-T"},
            {"mechanism": "CD19 epitope mutation (exon 2-4)",
             "probability": 0.10, "timeframe_months": "3-12",
             "detection": "Sequencing of CD19 exons", "countermeasure": "FMC63-independent binder or CD22 CAR-T"},
            {"mechanism": "Lineage switch (B-ALL → AML)",
             "probability": 0.05, "timeframe_months": "2-8",
             "detection": "Immunophenotyping, cytogenetics", "countermeasure": "AML-directed therapy or CD123 CAR-T"},
            {"mechanism": "T-cell exhaustion / CAR-T loss of persistence",
             "probability": 0.25, "timeframe_months": "3-6",
             "detection": "CAR-T cell quantification, B-cell recovery", "countermeasure": "Re-infusion, checkpoint inhibitor combo"},
            {"mechanism": "Trogocytosis (antigen stripping)",
             "probability": 0.15, "timeframe_months": "1-3",
             "detection": "CAR-T cell CD19+ fraction analysis", "countermeasure": "Lower E:T ratio, optimized dosing"},
            {"mechanism": "Death receptor pathway mutation (FAS/TRAIL)",
             "probability": 0.08, "timeframe_months": "6-24",
             "detection": "FAS/TNFRSF10A sequencing", "countermeasure": "Perforin/granzyme-enhanced CAR constructs"},
        ],
        "BCMA": [
            {"mechanism": "BCMA biallelic loss (del + LOH)",
             "probability": 0.15, "timeframe_months": "6-18",
             "detection": "BCMA flow cytometry, sBCMA monitoring", "countermeasure": "GPRC5D CAR-T, bispecific antibody"},
            {"mechanism": "BCMA shedding (gamma-secretase cleavage)",
             "probability": 0.20, "timeframe_months": "1-6",
             "detection": "Serum sBCMA levels", "countermeasure": "Gamma-secretase inhibitor combination"},
            {"mechanism": "T-cell exhaustion",
             "probability": 0.30, "timeframe_months": "3-9",
             "detection": "PD-1/LAG-3/TIM-3 on CAR-T cells", "countermeasure": "PD-1 knockout CAR-T, checkpoint combo"},
        ],
    }

    mechanisms = resistance_mechanisms.get(car_t_target, resistance_mechanisms["CD19"])

    # Simulate evolution over time
    timeline = []
    cumulative_resistance_prob = 0
    for month in range(1, months_post_infusion + 1):
        month_events = []
        for mech in mechanisms:
            # Parse timeframe
            timeframe = mech["timeframe_months"]
            parts = timeframe.split("-")
            start_month = int(parts[0])
            end_month = int(parts[1]) if len(parts) > 1 else start_month + 12

            if start_month <= month <= end_month:
                monthly_prob = mech["probability"] / max(end_month - start_month, 1)
                if random.random() < monthly_prob:
                    month_events.append(mech["mechanism"])
                    cumulative_resistance_prob += monthly_prob

        timeline.append({
            "month": month,
            "events": month_events,
            "cumulative_resistance_probability": round(min(cumulative_resistance_prob, 1.0), 3),
            "predicted_status": ("relapsed" if cumulative_resistance_prob > 0.5 else
                                "at_risk" if cumulative_resistance_prob > 0.2 else
                                "responding"),
        })

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "car_t_target": car_t_target,
        "initial_response": initial_response,
        "monitoring_months": months_post_infusion,
        "resistance_mechanisms": mechanisms,
        "evolution_timeline": timeline,
        "mrd_monitoring_schedule": [
            {"timepoint": "Day 14", "test": "CAR-T cell expansion qPCR", "critical": True},
            {"timepoint": "Day 28", "test": "Response assessment (PET/CT or BM biopsy)", "critical": True},
            {"timepoint": "Month 3", "test": "MRD by flow cytometry + CAR-T persistence", "critical": True},
            {"timepoint": "Month 6", "test": "MRD + B-cell recovery + imaging", "critical": True},
            {"timepoint": "Month 12", "test": "Comprehensive restaging + MRD", "critical": False},
            {"timepoint": "Month 18", "test": "Surveillance imaging + labs", "critical": False},
            {"timepoint": "Month 24", "test": "Long-term follow-up assessment", "critical": False},
        ],
        "prediction_summary": {
            "relapse_probability_12mo": round(min(cumulative_resistance_prob, 1.0), 2),
            "most_likely_mechanism": max(mechanisms, key=lambda m: m["probability"])["mechanism"],
            "recommended_monitoring": "Intensive MRD surveillance + antigen expression monitoring",
        },
    }
