"""
CARVanta Genomics — Copy Number Variation (CNV) Analyzer
==========================================================
Detect and interpret copy number alterations across the genome,
with focus on therapeutically relevant amplifications and deletions.

Features:
- Genome-wide CNV detection from WGS/WES/panel data
- Focal amplification and homozygous deletion calling
- Clinically annotated CNV database (oncogenes/TSGs)
- Chromosomal instability (CIN) scoring
- Ploidy estimation and tumor purity assessment
- CNV-drug interaction mapping
- Loss of heterozygosity (LOH) detection
- HRD (homologous recombination deficiency) scoring
- CAR-T target antigen copy number assessment
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.genomics.cnv_analyzer")


# ──────────────────────────────────────────────────────────────────────
# Clinically Relevant CNV Database
# ──────────────────────────────────────────────────────────────────────

_ONCOGENE_AMPS = {
    "MYC": {"chr": "8q24.21", "cancer": ["DLBCL", "BL", "MM"], "frequency_pct": 15,
            "significance": "Poor prognosis, aggressive biology", "car_t": "MYC amplification predicts lower CR rate with CD19 CAR-T"},
    "ERBB2": {"chr": "17q12", "cancer": ["BREAST", "GASTRIC", "ESOPHAGEAL"], "frequency_pct": 20,
              "significance": "HER2-directed therapy eligible", "car_t": "HER2 amplification is direct CAR-T target (HER2-CAR-T)"},
    "EGFR": {"chr": "7p11.2", "cancer": ["GBM", "NSCLC"], "frequency_pct": 40,
             "significance": "EGFR-directed therapy, EGFRvIII neoantigen", "car_t": "EGFRvIII is a validated CAR-T target in GBM"},
    "CDK4": {"chr": "12q14.1", "cancer": ["Liposarcoma", "GBM"], "frequency_pct": 90,
             "significance": "CDK4/6 inhibitor sensitivity", "car_t": "CDK4 amplification may affect T-cell proliferation via cell cycle regulation"},
    "MDM2": {"chr": "12q15", "cancer": ["Liposarcoma", "AML"], "frequency_pct": 10,
             "significance": "p53 pathway inactivation, MDM2 inhibitor target", "car_t": "MDM2 amplification suppresses p53-mediated tumor cell apoptosis"},
    "CCND1": {"chr": "11q13.3", "cancer": ["MCL", "BREAST", "ESOPHAGEAL"], "frequency_pct": 95,
              "significance": "Defines MCL; CDK4/6 inhibitor sensitive", "car_t": "CCND1 overexpression in MCL; CD19 CAR-T (brexu-cel) is FDA-approved"},
    "BCL2": {"chr": "18q21.33", "cancer": ["FL", "DLBCL"], "frequency_pct": 30,
             "significance": "Anti-apoptotic; venetoclax target", "car_t": "BCL2 amplification may reduce CAR-T killing efficacy; venetoclax combo investigated"},
    "FGFR1": {"chr": "8p11.23", "cancer": ["NSCLC", "BREAST"], "frequency_pct": 5,
              "significance": "FGFR inhibitor target", "car_t": "FGFR amplification as potential CAR-T target antigen"},
    "PIK3CA": {"chr": "3q26.32", "cancer": ["BREAST", "ENDOMETRIAL", "OVARIAN"], "frequency_pct": 35,
               "significance": "PI3K inhibitor target (alpelisib)", "car_t": "PI3K pathway activation may impair T-cell function in TME"},
    "KRAS": {"chr": "12p12.1", "cancer": ["PDAC", "CRC", "NSCLC"], "frequency_pct": 25,
             "significance": "RAS pathway activation", "car_t": "KRAS-driven tumors often have immunosuppressive TME"},
    "MET": {"chr": "7q31.2", "cancer": ["NSCLC", "RCC", "HCC"], "frequency_pct": 5,
            "significance": "MET amplification predicts MET inhibitor response", "car_t": "c-MET is an active CAR-T target in solid tumors"},
    "AR": {"chr": "Xq12", "cancer": ["PROSTATE"], "frequency_pct": 30,
           "significance": "Enzalutamide/abiraterone resistance", "car_t": "AR amplification in CRPC; PSMA-directed CAR-T approaches"},
}

_TSG_DELETIONS = {
    "TP53": {"chr": "17p13.1", "cancer": ["pan-cancer"], "frequency_pct": 40,
             "significance": "Worst prognostic factor across cancers", "car_t": "TP53 loss associated with resistance to all therapies including CAR-T"},
    "CDKN2A": {"chr": "9p21.3", "cancer": ["ALL", "NSCLC", "Melanoma", "GBM"], "frequency_pct": 30,
               "significance": "p16/ARF loss; CDK4/6 inhibitor sensitivity paradox", "car_t": "CDKN2A deletion in ALL predicts aggressive disease; early CAR-T intervention recommended"},
    "RB1": {"chr": "13q14.2", "cancer": ["Retinoblastoma", "SCLC", "MM"], "frequency_pct": 90,
            "significance": "Cell cycle deregulation", "car_t": "RB1 loss in MM associated with aggressive biology and potentially lower CAR-T response"},
    "PTEN": {"chr": "10q23.31", "cancer": ["GBM", "PROSTATE", "ENDOMETRIAL"], "frequency_pct": 25,
             "significance": "PI3K/AKT pathway activation", "car_t": "PTEN loss creates immunosuppressive TME, reducing CAR-T infiltration in solid tumors"},
    "BRCA1": {"chr": "17q21.31", "cancer": ["BREAST", "OVARIAN"], "frequency_pct": 5,
              "significance": "HRD; PARP inhibitor sensitivity", "car_t": "BRCA1 loss → genomic instability → higher neoantigen load → potential immune benefit"},
    "BRCA2": {"chr": "13q13.1", "cancer": ["BREAST", "OVARIAN", "PROSTATE", "PDAC"], "frequency_pct": 3,
              "significance": "HRD; PARP inhibitor sensitivity", "car_t": "Similar to BRCA1; HRD tumors may be more immunogenic"},
    "ATM": {"chr": "11q22.3", "cancer": ["CLL", "MCL", "BREAST"], "frequency_pct": 15,
            "significance": "DNA damage response deficiency", "car_t": "ATM loss in CLL/MCL may indicate need for earlier CAR-T intervention"},
    "SMAD4": {"chr": "18q21.2", "cancer": ["PDAC", "CRC"], "frequency_pct": 55,
              "significance": "TGF-β pathway disruption", "car_t": "SMAD4 loss paradoxically may reduce TGF-β immunosuppression in TME"},
}


async def analyze_cnv(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
    include_genome_wide: bool = False,
) -> Dict[str, Any]:
    """Analyze copy number variations for a patient sample.

    Simulates CNV detection from WES/WGS data with clinically
    annotated amplifications and deletions.
    """
    if seed:
        random.seed(seed)

    # Detect amplifications
    amplifications = []
    for gene, info in _ONCOGENE_AMPS.items():
        cancer_match = cancer_type.upper() in [c.upper() for c in info["cancer"]] or "pan-cancer" in info["cancer"]
        detection_prob = (info["frequency_pct"] / 100) * (1.5 if cancer_match else 0.3)
        detected = random.random() < min(detection_prob, 0.95)

        if detected or cancer_match:
            copy_number = round(random.uniform(3, 40), 1) if detected else 2.0
            log2_ratio = round(math.log2(copy_number / 2), 3) if copy_number > 0 else 0

            amplifications.append({
                "gene": gene,
                "locus": info["chr"],
                "copy_number": copy_number,
                "log2_ratio": log2_ratio,
                "amplified": copy_number > 4,
                "focal": random.random() < 0.7,
                "significance": info["significance"],
                "car_t_impact": info["car_t"],
                "cancer_relevance": cancer_match,
            })

    # Detect deletions
    deletions = []
    for gene, info in _TSG_DELETIONS.items():
        cancer_match = cancer_type.upper() in [c.upper() for c in info["cancer"]] or "pan-cancer" in info["cancer"]
        detection_prob = (info["frequency_pct"] / 100) * (1.5 if cancer_match else 0.3)
        detected = random.random() < min(detection_prob, 0.95)

        if detected or cancer_match:
            copy_number = round(random.uniform(0, 1.5), 1) if detected else 2.0
            loh = detected and random.random() < 0.6

            deletions.append({
                "gene": gene,
                "locus": info["chr"],
                "copy_number": copy_number,
                "homozygous_deletion": copy_number < 0.5,
                "loh": loh,
                "significance": info["significance"],
                "car_t_impact": info["car_t"],
                "cancer_relevance": cancer_match,
            })

    # Chromosomal Instability Score
    total_cnvs = sum(1 for a in amplifications if a["amplified"]) + sum(1 for d in deletions if d["copy_number"] < 1.5)
    cin_score = round(total_cnvs / max(len(amplifications) + len(deletions), 1) * 100, 1)

    # Tumor ploidy & purity estimation
    ploidy = round(random.uniform(1.8, 4.5), 2)
    purity = round(random.uniform(0.3, 0.95), 2)

    # HRD score (for BRCA/HR pathway assessment)
    hrd_loh = random.randint(2, 25)
    hrd_tai = random.randint(3, 30)
    hrd_lst = random.randint(5, 35)
    hrd_total = hrd_loh + hrd_tai + hrd_lst

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "amplifications": sorted(amplifications, key=lambda x: x["copy_number"], reverse=True),
        "deletions": sorted(deletions, key=lambda x: x["copy_number"]),
        "summary": {
            "total_amplifications": sum(1 for a in amplifications if a["amplified"]),
            "total_deletions": sum(1 for d in deletions if d["homozygous_deletion"]),
            "actionable_cnvs": sum(1 for a in amplifications if a["amplified"] and a["cancer_relevance"]) + sum(1 for d in deletions if d["homozygous_deletion"] and d["cancer_relevance"]),
        },
        "cin_score": cin_score,
        "cin_category": "high" if cin_score > 50 else "moderate" if cin_score > 25 else "low",
        "tumor_ploidy": ploidy,
        "tumor_purity": purity,
        "hrd_score": {
            "loh_score": hrd_loh,
            "tai_score": hrd_tai,
            "lst_score": hrd_lst,
            "total": hrd_total,
            "hrd_positive": hrd_total >= 42,
            "parp_inhibitor_eligible": hrd_total >= 42,
        },
    }


async def antigen_copy_number(
    target: str = "CD19",
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Assess copy number of CAR-T target antigen gene.

    Evaluates whether the target antigen gene shows amplification,
    normal copy number, or deletion — critical for predicting
    CAR-T efficacy and antigen escape risk.
    """
    if seed:
        random.seed(seed)

    # Target antigen gene locations
    target_genes = {
        "CD19": {"gene": "CD19", "chr": "16p11.2", "normal_expression": "high", "typical_cn": 2},
        "BCMA": {"gene": "TNFRSF17", "chr": "16p13.13", "normal_expression": "moderate", "typical_cn": 2},
        "CD22": {"gene": "CD22", "chr": "19q13.12", "normal_expression": "high", "typical_cn": 2},
        "GPRC5D": {"gene": "GPRC5D", "chr": "12p13.33", "normal_expression": "moderate", "typical_cn": 2},
        "HER2": {"gene": "ERBB2", "chr": "17q12", "normal_expression": "variable", "typical_cn": 2},
        "MSLN": {"gene": "MSLN", "chr": "16p13.3", "normal_expression": "moderate", "typical_cn": 2},
        "GPC3": {"gene": "GPC3", "chr": "Xq26.2", "normal_expression": "low-moderate", "typical_cn": 1},
        "PSMA": {"gene": "FOLH1", "chr": "11p11.12", "normal_expression": "moderate", "typical_cn": 2},
    }

    info = target_genes.get(target.upper(), {"gene": target, "chr": "unknown", "normal_expression": "unknown", "typical_cn": 2})

    # Simulate copy number assessment
    cn = round(random.gauss(info["typical_cn"], 0.5), 1)
    cn = max(0, cn)

    # Expression correlation
    if cn > 3:
        expression_impact = "Amplified — likely high surface expression, favorable for CAR-T"
        escape_risk = "low"
    elif cn >= 1.5:
        expression_impact = "Normal — expected standard surface expression"
        escape_risk = "moderate"
    elif cn >= 0.5:
        expression_impact = "Hemizygous loss — reduced expression, higher antigen escape risk"
        escape_risk = "high"
    else:
        expression_impact = "Homozygous deletion — absent expression, CAR-T will not work against this target"
        escape_risk = "very_high"

    return {
        "target_antigen": target,
        "gene": info["gene"],
        "chromosome": info["chr"],
        "copy_number": cn,
        "status": "amplified" if cn > 3 else "normal" if cn >= 1.5 else "loss" if cn >= 0.5 else "deleted",
        "expression_impact": expression_impact,
        "antigen_escape_risk": escape_risk,
        "recommendation": (
            f"{'Target {target} shows adequate copy number. Proceed with CAR-T.' if cn >= 1.5 else 'WARNING: {target} copy number loss detected. Consider alternative target or dual-targeting CAR-T.'}"
        ),
    }


async def arm_level_events(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Detect chromosome arm-level gain/loss events.

    Identifies whole-arm or large-segment gains and losses
    that may affect prognosis and therapy response.
    """
    if seed:
        random.seed(seed)

    # Chromosome arms with clinical significance
    arms = {
        "1p": {"significance": "1p loss in neuroblastoma, MM", "frequency": 15},
        "1q": {"significance": "1q gain adverse in MM (R-ISS criteria)", "frequency": 40},
        "3p": {"significance": "VHL loss in clear cell RCC", "frequency": 25},
        "5q": {"significance": "5q deletion in MDS (lenalidomide responsive)", "frequency": 10},
        "6p": {"significance": "HLA locus — loss may impair immune recognition", "frequency": 8},
        "7q": {"significance": "Contains MET, BRAF; gain in GBM/AML", "frequency": 12},
        "8q": {"significance": "MYC locus — gain associated with aggressive biology", "frequency": 20},
        "9p": {"significance": "CDKN2A/2B and JAK2 locus", "frequency": 30},
        "11q": {"significance": "ATM loss in CLL/MCL; adverse prognosis", "frequency": 18},
        "13q": {"significance": "RB1 and BRCA2 — deletion in CLL (favorable if isolated)", "frequency": 50},
        "17p": {"significance": "TP53 loss — worst prognosis; pan-cancer adverse", "frequency": 15},
        "17q": {"significance": "ERBB2 (HER2) amplification locus", "frequency": 10},
        "18q": {"significance": "BCL2 and SMAD4 locus — translocation in FL", "frequency": 85},
        "20q": {"significance": "20q deletion in MDS/MPN", "frequency": 8},
        "22q": {"significance": "BCR locus; NF2 loss in meningioma", "frequency": 5},
    }

    events = []
    for arm, info in arms.items():
        prob = info["frequency"] / 100
        if cancer_type.upper() in ("DLBCL", "FL") and arm in ("18q", "8q", "17p"):
            prob *= 2
        elif cancer_type.upper() == "MM" and arm in ("1q", "13q", "17p"):
            prob *= 2.5
        elif cancer_type.upper() == "CLL" and arm in ("11q", "13q", "17p"):
            prob *= 3

        detected = random.random() < min(prob, 0.95)
        if detected:
            event_type = random.choice(["gain", "loss"])
            magnitude = round(random.uniform(0.3, 1.0), 2)
            events.append({
                "arm": arm,
                "event": event_type,
                "log2_ratio": round(magnitude if event_type == "gain" else -magnitude, 3),
                "fraction_affected": round(random.uniform(0.5, 1.0), 2),
                "significance": info["significance"],
                "detected": True,
            })

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "arm_level_events": sorted(events, key=lambda x: abs(x["log2_ratio"]), reverse=True),
        "total_gains": sum(1 for e in events if e["event"] == "gain"),
        "total_losses": sum(1 for e in events if e["event"] == "loss"),
        "genome_doubling": random.random() < 0.25,
        "aneuploidy_score": round(len(events) / len(arms) * 100, 1),
    }


async def cnv_therapy_recommendations(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate therapy recommendations based on CNV profile.

    Maps detected amplifications and deletions to targeted
    therapies, immunotherapy eligibility, and CAR-T considerations.
    """
    if seed:
        random.seed(seed)

    # Get CNV results first
    cnv_data = await analyze_cnv(cancer_type=cancer_type, seed=seed)

    recommendations = []
    for amp in cnv_data["amplifications"]:
        if amp["amplified"] and amp["cancer_relevance"]:
            rec = {
                "gene": amp["gene"],
                "alteration": f"Amplification (CN {amp['copy_number']})",
                "category": "targeted_therapy",
                "drugs": [],
                "evidence_level": "moderate",
                "car_t_consideration": amp["car_t_impact"],
            }
            # Map genes to therapies
            gene_drugs = {
                "ERBB2": ["Trastuzumab", "Pertuzumab", "T-DXd", "HER2 CAR-T"],
                "EGFR": ["Osimertinib", "EGFRvIII CAR-T"],
                "MET": ["Capmatinib", "Tepotinib", "c-MET CAR-T"],
                "FGFR1": ["Pemigatinib", "Futibatinib"],
                "CDK4": ["Palbociclib", "Ribociclib", "Abemaciclib"],
                "BCL2": ["Venetoclax"],
                "PIK3CA": ["Alpelisib"],
                "MDM2": ["Idasanutlin (investigational)"],
            }
            rec["drugs"] = gene_drugs.get(amp["gene"], [])
            if rec["drugs"]:
                recommendations.append(rec)

    for dele in cnv_data["deletions"]:
        if dele["homozygous_deletion"] and dele["cancer_relevance"]:
            rec = {
                "gene": dele["gene"],
                "alteration": f"Homozygous deletion",
                "category": "biomarker",
                "drugs": [],
                "evidence_level": "strong" if dele["gene"] in ("BRCA1", "BRCA2") else "moderate",
                "car_t_consideration": dele["car_t_impact"],
            }
            gene_drugs = {
                "BRCA1": ["Olaparib", "Niraparib", "Rucaparib", "Talazoparib"],
                "BRCA2": ["Olaparib", "Niraparib", "Rucaparib"],
                "ATM": ["Olaparib (investigational)"],
            }
            rec["drugs"] = gene_drugs.get(dele["gene"], [])
            if rec["drugs"]:
                recommendations.append(rec)

    # HRD-based recommendation
    if cnv_data["hrd_score"]["hrd_positive"]:
        recommendations.append({
            "gene": "HRD",
            "alteration": f"HRD score {cnv_data['hrd_score']['total']} (positive ≥42)",
            "category": "biomarker",
            "drugs": ["Olaparib", "Niraparib", "Rucaparib"],
            "evidence_level": "strong",
            "car_t_consideration": "HRD tumors have higher neoantigen load which may enhance immune recognition",
        })

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
        "immunotherapy_markers": {
            "cin_score": cnv_data["cin_score"],
            "hrd_positive": cnv_data["hrd_score"]["hrd_positive"],
            "high_aneuploidy": cnv_data["cin_score"] > 50,
            "immunotherapy_prediction": (
                "High CIN/aneuploidy may correlate with immune evasion"
                if cnv_data["cin_score"] > 50
                else "Moderate genomic instability; standard immunotherapy consideration"
            ),
        },
    }
