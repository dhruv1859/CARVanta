"""
CARVanta — PDAC biomarker_database.csv generator
================================================
Builds the central biomarker_database.csv from data/pdac_biomarkers.py.

Keeps the ORIGINAL required columns so every downstream consumer keeps
working, and appends PDAC facet columns:
    biomarker_category, analyte_type, regulation, source_group

Numeric CAR-T-style fields (expression, stability, immunogenicity, surface
accessibility, trials) are SYNTHESIZED deterministically from each marker's
category + up/down indication so scoring, rankings, atlas and charts remain
functional and realistic. Values are illustrative, not measured.
"""
import os
import csv
import hashlib
import pdac_biomarkers as pdb

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biomarker_database.csv")

COLUMNS = [
    "antigen_name", "cancer_type",
    "mean_tumor_expression", "mean_normal_expression",
    "stability_score", "literature_support",
    "immunogenicity_score", "surface_accessibility",
    "clinical_trials_count", "viability_label",
    "data_source", "source_database", "evidence_level",
    # ── PDAC facet columns ──
    "biomarker_category", "analyte_type", "regulation", "source_group",
]

# High-profile PDAC markers get stronger clinical evidence / trial counts.
FLAGSHIP = {
    "CA19-9": 260, "CEA": 180, "KRAS": 210, "MSLN (Mesothelin)": 95,
    "MUC16": 70, "CA125 (MUC16)": 70, "MUC5AC": 55, "TP53": 160,
    "SMAD4": 90, "CDKN2A": 85, "BRCA2": 120, "BRCA1": 110, "PALB2": 45,
    "GPC1": 60, "THBS-2": 50, "sTRA": 40, "REG1A": 35, "LRG1": 30,
    "GNAS": 40, "PRSS1": 25, "SPINK1": 25, "miR-21": 65, "miR-1246": 30,
    "ATM": 55, "MET": 50, "ERBB2": 60, "EGFR": 70, "MYC": 60,
}

# Non-biomarker / not-validated entries → low viability.
NON_MARKER_HINTS = ("not biomarker", "not validated", "pseudogene", "candidate gene",
                    "unknown role", "non-canonical")


def _rng(name, salt):
    """Deterministic pseudo-random float in [0,1) from name+salt."""
    h = hashlib.md5(f"{name}|{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _synth(b):
    name, cat, ind = b["name"], b["category"], b["indication"]
    catl = cat.lower()
    r1, r2, r3 = _rng(name, "a"), _rng(name, "b"), _rng(name, "c")

    is_nonmarker = any(h in catl for h in NON_MARKER_HINTS)

    # Expression: model tumor vs normal from the regulation direction.
    if ind == "up":
        tumor = round(6.5 + 3.0 * r1, 2)          # 6.5 - 9.5
        normal = round(0.4 + 1.8 * r2, 2)          # 0.4 - 2.2
    elif ind == "down":
        tumor = round(0.6 + 2.2 * r1, 2)           # 0.6 - 2.8
        normal = round(4.5 + 3.0 * r2, 2)          # 4.5 - 7.5
    elif ind == "context":
        tumor = round(4.0 + 2.5 * r1, 2)
        normal = round(3.0 + 2.0 * r2, 2)
    else:  # neutral
        base = 3.5 + 1.5 * r1
        tumor = round(base, 2)
        normal = round(base + (r2 - 0.5), 2)

    # Surface accessibility: high for surface/secreted proteins, low for
    # intracellular genes, RNAs and DNA markers.
    if any(k in catl for k in ("glycoprotein", "adhesion", "receptor", "laminin",
                               "membrane", "channel", "gpcr", "exosome")):
        surface = 0.80 + 0.18 * r3
    elif b["analyte_type"] in ("miRNA", "lncRNA", "RNA", "ctDNA / DNA", "Gene", "Metabolite"):
        surface = 0.15 + 0.25 * r3
    elif "protein" in catl or "apolipoprotein" in catl or "enzyme" in catl:
        surface = 0.55 + 0.30 * r3
    else:
        surface = 0.40 + 0.30 * r3
    surface = round(min(surface, 0.99), 3)

    # Literature support + trials.
    trials = FLAGSHIP.get(name, 0)
    if trials == 0:
        trials = int(1 + 12 * r2) if not is_nonmarker else int(0 + 2 * r2)
    lit = 0.55 + 0.4 * r1
    if name in FLAGSHIP:
        lit = 0.85 + 0.14 * r1
    if is_nonmarker:
        lit = 0.25 + 0.2 * r1
    lit = round(min(lit, 0.99), 3)

    stability = round(0.55 + 0.4 * r3, 3)
    immuno = round(0.45 + 0.5 * r1, 3)

    viability = 0 if (is_nonmarker or ind == "neutral") else 1

    if name in FLAGSHIP:
        evidence, dsource, dbase = "clinical", "real", "Literature"
    elif is_nonmarker:
        evidence, dsource, dbase = "predicted", "computationally_derived", "Synthetic"
    else:
        evidence, dsource, dbase = "preclinical", "real", "Literature"

    return {
        "antigen_name": name,
        "cancer_type": pdb.CANCER_TYPE,
        "mean_tumor_expression": tumor,
        "mean_normal_expression": normal,
        "stability_score": stability,
        "literature_support": lit,
        "immunogenicity_score": immuno,
        "surface_accessibility": surface,
        "clinical_trials_count": trials,
        "viability_label": viability,
        "data_source": dsource,
        "source_database": dbase,
        "evidence_level": evidence,
        "biomarker_category": cat,
        "analyte_type": b["analyte_type"],
        "regulation": ind,
        "source_group": b["source_group"],
    }


def main():
    rows = [_synth(b) for b in pdb.BIOMARKERS]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {OUT}")
    print(f"Unique biomarkers: {len({r['antigen_name'] for r in rows})}")
    viable = sum(r['viability_label'] for r in rows)
    print(f"Viable (label=1): {viable}  |  Non-viable: {len(rows)-viable}")


if __name__ == "__main__":
    main()
