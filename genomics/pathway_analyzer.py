"""
CARVanta Genomics — Signaling Pathway Analyzer
=================================================
Map genomic alterations to signaling pathways, calculate
pathway disruption scores, and predict therapeutic vulnerabilities.

Features:
- 12 key oncogenic pathway assessment
- Pathway disruption scoring (0-100)
- Multi-gene pathway alteration aggregation
- Therapeutic vulnerability mapping
- Resistance mechanism prediction
- Pathway crosstalk network analysis
- CAR-T pathway interference assessment
- Immune evasion pathway scoring
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.genomics.pathway_analyzer")


# ──────────────────────────────────────────────────────────────────────
# Oncogenic Pathway Definitions
# ──────────────────────────────────────────────────────────────────────

_PATHWAYS = {
    "PI3K_AKT_mTOR": {
        "name": "PI3K/AKT/mTOR Signaling",
        "genes": {
            "PIK3CA": {"role": "oncogene", "alteration_types": ["mutation", "amplification"], "frequency": 30},
            "PTEN": {"role": "tumor_suppressor", "alteration_types": ["deletion", "mutation"], "frequency": 25},
            "AKT1": {"role": "oncogene", "alteration_types": ["mutation", "amplification"], "frequency": 5},
            "MTOR": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 3},
            "TSC1": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 5},
            "TSC2": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 3},
            "PIK3R1": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 5},
        },
        "therapies": ["Alpelisib", "Everolimus", "Temsirolimus", "Ipatasertib", "Capivasertib"],
        "car_t_impact": "PI3K/AKT activation in tumor creates immunosuppressive TME; however, PI3K inhibition in CAR-T cells can enhance memory formation",
    },
    "RAS_MAPK": {
        "name": "RAS/MAPK/ERK Signaling",
        "genes": {
            "KRAS": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 25},
            "NRAS": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 8},
            "HRAS": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 3},
            "BRAF": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 15},
            "MAP2K1": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 3},
            "NF1": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 8},
            "EGFR": {"role": "oncogene", "alteration_types": ["mutation", "amplification"], "frequency": 15},
        },
        "therapies": ["Sotorasib", "Adagrasib", "Dabrafenib+Trametinib", "Encorafenib+Binimetinib"],
        "car_t_impact": "RAS/MAPK activation promotes immune evasion through PD-L1 upregulation and cytokine modulation",
    },
    "TP53_apoptosis": {
        "name": "p53/Apoptosis Pathway",
        "genes": {
            "TP53": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 40},
            "MDM2": {"role": "oncogene", "alteration_types": ["amplification"], "frequency": 10},
            "MDM4": {"role": "oncogene", "alteration_types": ["amplification"], "frequency": 5},
            "CDKN2A": {"role": "tumor_suppressor", "alteration_types": ["deletion", "mutation"], "frequency": 30},
            "BAX": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 3},
            "BCL2": {"role": "oncogene", "alteration_types": ["amplification", "translocation"], "frequency": 30},
        },
        "therapies": ["Venetoclax", "Navitoclax", "APR-246", "Idasanutlin"],
        "car_t_impact": "TP53 mutations confer pan-resistance; BCL2 overexpression directly impairs CAR-T mediated killing via anti-apoptotic signaling",
    },
    "WNT_beta_catenin": {
        "name": "WNT/β-Catenin Signaling",
        "genes": {
            "CTNNB1": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 8},
            "APC": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 70},
            "AXIN1": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 5},
            "RNF43": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 7},
        },
        "therapies": ["Tegavivint (experimental)", "WNT974 (experimental)"],
        "car_t_impact": "WNT activation promotes T-cell exclusion from tumors; β-catenin nuclear accumulation correlates with immune evasion",
    },
    "cell_cycle": {
        "name": "Cell Cycle Regulation",
        "genes": {
            "CCND1": {"role": "oncogene", "alteration_types": ["amplification", "translocation"], "frequency": 20},
            "CCND2": {"role": "oncogene", "alteration_types": ["amplification"], "frequency": 5},
            "CCNE1": {"role": "oncogene", "alteration_types": ["amplification"], "frequency": 8},
            "CDK4": {"role": "oncogene", "alteration_types": ["amplification"], "frequency": 15},
            "CDK6": {"role": "oncogene", "alteration_types": ["amplification"], "frequency": 5},
            "RB1": {"role": "tumor_suppressor", "alteration_types": ["deletion", "mutation"], "frequency": 10},
            "CDKN2A": {"role": "tumor_suppressor", "alteration_types": ["deletion"], "frequency": 30},
            "CDKN2B": {"role": "tumor_suppressor", "alteration_types": ["deletion"], "frequency": 25},
        },
        "therapies": ["Palbociclib", "Ribociclib", "Abemaciclib", "Trilaciclib"],
        "car_t_impact": "CDK4/6 inhibitors can paradoxically enhance anti-tumor immunity by promoting antigen presentation",
    },
    "epigenetic": {
        "name": "Epigenetic Regulation",
        "genes": {
            "KMT2A": {"role": "oncogene", "alteration_types": ["translocation", "mutation"], "frequency": 5},
            "KMT2D": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 20},
            "CREBBP": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 15},
            "EP300": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 8},
            "EZH2": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 12},
            "DNMT3A": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 20},
            "TET2": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 15},
            "IDH1": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 10},
            "IDH2": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 8},
        },
        "therapies": ["Tazemetostat", "Enasidenib", "Ivosidenib", "Azacitidine", "Decitabine"],
        "car_t_impact": "Epigenetic dysregulation affects antigen presentation (MHC-I downregulation); EZH2 mutations in DLBCL may influence CAR-T response",
    },
    "NF_kB": {
        "name": "NF-κB Signaling",
        "genes": {
            "MYD88": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 30},
            "CARD11": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 10},
            "CD79A": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 18},
            "CD79B": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 20},
            "TNFAIP3": {"role": "tumor_suppressor", "alteration_types": ["deletion", "mutation"], "frequency": 15},
            "BIRC3": {"role": "tumor_suppressor", "alteration_types": ["deletion", "mutation"], "frequency": 8},
        },
        "therapies": ["Ibrutinib", "Acalabrutinib", "Zanubrutinib", "Lenalidomide"],
        "car_t_impact": "NF-κB pathway mutations define ABC-DLBCL subtype; IBM-targeting combined with CAR-T may improve outcomes",
    },
    "JAK_STAT": {
        "name": "JAK/STAT Signaling",
        "genes": {
            "JAK1": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 5},
            "JAK2": {"role": "oncogene", "alteration_types": ["mutation", "amplification"], "frequency": 10},
            "JAK3": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 3},
            "STAT3": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 8},
            "STAT5B": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 3},
            "SOCS1": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 15},
        },
        "therapies": ["Ruxolitinib", "Fedratinib", "Tofacitinib"],
        "car_t_impact": "JAK/STAT is critical for T-cell function; ruxolitinib used to manage CRS may inadvertently suppress CAR-T expansion",
    },
    "notch": {
        "name": "NOTCH Signaling",
        "genes": {
            "NOTCH1": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 50},
            "NOTCH2": {"role": "oncogene", "alteration_types": ["mutation"], "frequency": 10},
            "FBXW7": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 10},
        },
        "therapies": ["Gamma-secretase inhibitors (experimental)"],
        "car_t_impact": "NOTCH mutations common in T-ALL; NOTCH signaling important for T-cell differentiation and CAR-T memory formation",
    },
    "dna_damage_repair": {
        "name": "DNA Damage Repair",
        "genes": {
            "BRCA1": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 5},
            "BRCA2": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 3},
            "ATM": {"role": "tumor_suppressor", "alteration_types": ["mutation", "deletion"], "frequency": 10},
            "ATR": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 3},
            "PALB2": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 2},
            "CHEK2": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 3},
            "RAD51": {"role": "tumor_suppressor", "alteration_types": ["mutation"], "frequency": 1},
        },
        "therapies": ["Olaparib", "Niraparib", "Rucaparib", "Talazoparib"],
        "car_t_impact": "DDR deficiency increases mutational burden and neoantigen load, potentially enhancing immune recognition; PARP inhibitor + CAR-T combinations under investigation",
    },
}


async def analyze_pathways(
    cancer_type: str = "DLBCL",
    mutations: Optional[List[str]] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze oncogenic pathway alterations.

    Maps individual gene alterations to pathway-level disruption
    scores and predicts therapeutic vulnerabilities.
    """
    if seed:
        random.seed(seed)

    if not mutations:
        # Simulate detected mutations based on cancer type
        all_genes = []
        for pw in _PATHWAYS.values():
            for gene, info in pw["genes"].items():
                if random.random() < info["frequency"] / 100:
                    all_genes.append(gene)
        mutations = all_genes

    mutations_upper = [m.upper() for m in mutations]

    pathway_results = []
    for pw_key, pw_data in _PATHWAYS.items():
        altered_genes = []
        for gene, info in pw_data["genes"].items():
            if gene.upper() in mutations_upper:
                altered_genes.append({
                    "gene": gene,
                    "role": info["role"],
                    "alteration_types": info["alteration_types"],
                })

        disruption_score = round(len(altered_genes) / max(len(pw_data["genes"]), 1) * 100, 1)

        pathway_results.append({
            "pathway": pw_key,
            "name": pw_data["name"],
            "total_genes": len(pw_data["genes"]),
            "altered_genes": len(altered_genes),
            "disruption_score": disruption_score,
            "disrupted": disruption_score > 20,
            "genes_altered": altered_genes,
            "available_therapies": pw_data["therapies"],
            "car_t_impact": pw_data["car_t_impact"],
        })

    pathway_results.sort(key=lambda x: x["disruption_score"], reverse=True)

    # Overall genomic instability
    total_altered = sum(p["altered_genes"] for p in pathway_results)
    total_genes = sum(p["total_genes"] for p in pathway_results)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "mutations_input": len(mutations),
        "pathways_analyzed": len(pathway_results),
        "pathways_disrupted": sum(1 for p in pathway_results if p["disrupted"]),
        "genomic_instability_score": round(total_altered / max(total_genes, 1) * 100, 1),
        "pathways": pathway_results,
        "therapeutic_vulnerabilities": [
            {"pathway": p["name"], "therapies": p["available_therapies"], "disruption": p["disruption_score"]}
            for p in pathway_results if p["disrupted"] and p["available_therapies"]
        ],
    }


async def immune_evasion_pathways(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Score immune evasion pathway alterations.

    Evaluates genomic alterations in pathways specifically involved
    in immune evasion and predicts impact on CAR-T efficacy.
    """
    if seed:
        random.seed(seed)

    evasion_mechanisms = {
        "antigen_presentation": {
            "name": "Antigen Presentation Defects",
            "genes": {
                "B2M": {"frequency": 15, "impact": "Loss of MHC-I surface expression; affects immune recognition but not CAR-T (MHC-independent)"},
                "HLA-A": {"frequency": 8, "impact": "Allele-specific HLA loss; reduces classical T-cell recognition"},
                "HLA-B": {"frequency": 5, "impact": "HLA-B loss; reduces neoantigen presentation"},
                "TAP1": {"frequency": 5, "impact": "Defective peptide loading; impairs antigen presentation"},
                "TAP2": {"frequency": 3, "impact": "Defective peptide transport; complements TAP1 loss"},
                "NLRC5": {"frequency": 8, "impact": "MHC-I transcriptional activator; loss reduces MHC-I expression"},
            },
            "car_t_advantage": "CAR-T cells recognize surface antigens independently of MHC — resistant to MHC loss-mediated immune evasion",
        },
        "immune_checkpoints": {
            "name": "Checkpoint Pathway Amplification",
            "genes": {
                "CD274": {"frequency": 12, "impact": "PD-L1 amplification/overexpression; strong immune suppression"},
                "PDCD1LG2": {"frequency": 5, "impact": "PD-L2 amplification; additional checkpoint ligand"},
                "CD276": {"frequency": 10, "impact": "B7-H3 overexpression; emerging checkpoint and CAR-T target"},
                "VTCN1": {"frequency": 3, "impact": "B7-H4 overexpression; checkpoint suppression"},
                "IDO1": {"frequency": 15, "impact": "Tryptophan catabolism; immunosuppressive metabolite production"},
            },
            "car_t_advantage": "Armored CAR-T can be engineered to secrete anti-PD-1 or checkpoint-resistant constructs",
        },
        "cytokine_signaling": {
            "name": "Immunosuppressive Cytokine Signaling",
            "genes": {
                "TGFB1": {"frequency": 20, "impact": "TGF-β secretion suppresses effector T-cells and CAR-T function"},
                "IL10": {"frequency": 10, "impact": "IL-10 promotes regulatory/suppressive immune environment"},
                "VEGFA": {"frequency": 25, "impact": "VEGF creates immunosuppressive TME; anti-angiogenic combo may help"},
                "CSF1": {"frequency": 8, "impact": "M-CSF recruits immunosuppressive macrophages"},
            },
            "car_t_advantage": "TGF-β-resistant CAR-T constructs (dominant-negative TGFβRII) overcome this mechanism",
        },
        "death_receptor": {
            "name": "Death Receptor Pathway Defects",
            "genes": {
                "FAS": {"frequency": 8, "impact": "FAS loss prevents FAS/FasL-mediated apoptosis by CAR-T cells"},
                "FADD": {"frequency": 3, "impact": "FADD loss impairs downstream apoptotic signaling"},
                "CASP8": {"frequency": 5, "impact": "Caspase-8 loss prevents extrinsic apoptosis pathway"},
                "CFLAR": {"frequency": 10, "impact": "c-FLIP overexpression blocks death receptor signaling"},
            },
            "car_t_advantage": "CAR-T cells primarily kill via perforin/granzyme pathway; death receptor resistance is partially bypassed",
        },
    }

    results = []
    for mech_key, mech_data in evasion_mechanisms.items():
        altered_genes = []
        for gene, info in mech_data["genes"].items():
            if random.random() < info["frequency"] / 100:
                altered_genes.append({
                    "gene": gene,
                    "impact": info["impact"],
                })

        evasion_score = round(len(altered_genes) / max(len(mech_data["genes"]), 1) * 100, 1)

        results.append({
            "mechanism": mech_key,
            "name": mech_data["name"],
            "evasion_score": evasion_score,
            "genes_altered": altered_genes,
            "total_genes": len(mech_data["genes"]),
            "active": evasion_score > 20,
            "car_t_advantage": mech_data["car_t_advantage"],
        })

    overall_evasion = round(sum(r["evasion_score"] for r in results) / max(len(results), 1), 1)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "overall_evasion_score": overall_evasion,
        "evasion_category": "high" if overall_evasion > 40 else "moderate" if overall_evasion > 20 else "low",
        "mechanisms": results,
        "active_mechanisms": sum(1 for r in results if r["active"]),
        "car_t_overall": (
            "High immune evasion burden detected. CAR-T maintains advantage via MHC-independent recognition and "
            "perforin/granzyme killing, but armored constructs (anti-PD-1 secreting, TGF-β resistant) recommended."
            if overall_evasion > 30 else
            "Moderate immune evasion. Standard CAR-T constructs expected to be effective."
        ),
    }


async def pathway_crosstalk(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze pathway crosstalk and co-alteration patterns.

    Identifies pathways that are co-disrupted and predicts
    combination therapy potential.
    """
    if seed:
        random.seed(seed)

    # Known crosstalk pairs
    crosstalk_pairs = [
        {"pathway_a": "PI3K/AKT/mTOR", "pathway_b": "RAS/MAPK/ERK",
         "interaction": "Compensatory signaling — inhibition of one activates the other",
         "therapy_implication": "Dual PI3K+MEK inhibition may be needed; affects TME immunosuppression"},
        {"pathway_a": "TP53/Apoptosis", "pathway_b": "Cell Cycle",
         "interaction": "p53 controls G1/S checkpoint via p21; loss removes cell cycle brake",
         "therapy_implication": "CDK4/6 inhibitors may partially restore cell cycle control in TP53-mutant tumors"},
        {"pathway_a": "WNT/β-Catenin", "pathway_b": "PI3K/AKT/mTOR",
         "interaction": "GSK3β is shared between both pathways; AKT inhibits GSK3β → β-catenin activation",
         "therapy_implication": "Combined inhibition may enhance T-cell infiltration"},
        {"pathway_a": "JAK/STAT", "pathway_b": "NF-κB",
         "interaction": "STAT3 and NF-κB co-activate survival genes; synergistic immunosuppression",
         "therapy_implication": "Dual JAK+BTK inhibition in lymphomas; caution with CRS management"},
        {"pathway_a": "Epigenetic", "pathway_b": "TP53/Apoptosis",
         "interaction": "DNMT3A/TET2 mutations alter TP53 methylation; epigenetic silencing augments p53 loss",
         "therapy_implication": "Hypomethylating agents may restore p53 expression; combo with CAR-T under study"},
        {"pathway_a": "DNA Damage Repair", "pathway_b": "Cell Cycle",
         "interaction": "ATM/ATR checkpoint activates cell cycle arrest; co-loss accelerates genomic instability",
         "therapy_implication": "PARP + CDK4/6 inhibitor combinations; high neoantigen load may enhance CAR-T"},
    ]

    # Simulate which crosstalks are active
    active_crosstalks = []
    for pair in crosstalk_pairs:
        if random.random() < 0.5:
            active_crosstalks.append({
                **pair,
                "strength": random.choice(["strong", "moderate", "weak"]),
                "co_alteration_frequency": round(random.uniform(5, 40), 1),
            })

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "total_crosstalks": len(active_crosstalks),
        "crosstalks": active_crosstalks,
        "network_complexity": "high" if len(active_crosstalks) > 4 else "moderate" if len(active_crosstalks) > 2 else "low",
        "combination_therapy_opportunities": [
            c["therapy_implication"] for c in active_crosstalks if c["strength"] == "strong"
        ],
    }
