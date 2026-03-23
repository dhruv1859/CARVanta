#!/usr/bin/env python3
"""
CARVanta — Biomarker Classification Migration Script
=====================================================
Adds three new columns to biomarker_database.csv:
  - data_source:     real | validated | synthetic
  - source_database:  TCGA | UniProt | Literature | Synthetic
  - evidence_level:   clinical | preclinical | predicted

Classification logic:
  1. Known CAR-T antigens (curated list) with clinical_trials_count > 10 → real / TCGA or Literature / clinical
  2. Known CAR-T antigens with clinical_trials_count ≤ 10              → validated / UniProt or Literature / preclinical
  3. Everything else (ABC-prefixed synthetic names)                     → synthetic / Synthetic / predicted
"""

import os
import sys
import pandas as pd

# ── Known real CAR-T antigens (curated from the database) ──────────────────────
KNOWN_ANTIGENS = {
    "CD19", "BCMA", "CD22", "GPRC5D", "PSMA", "GD2", "GPC3", "FOLR1",
    "CLDN18", "ROR1", "DLL3", "CD70", "CD138", "CAIX", "IL13RA2",
    "NECTIN4", "GUCY2C", "NKG2D", "STEAP1", "PSCA", "ALPPL2", "LYPD3",
    "NYESO1", "WT1", "PRAME", "TYRP1", "MAGEA4", "LAGE1", "SSX2",
    "HER2", "EGFR", "MESOTHELIN", "B7H3", "TROP2", "EPCAM", "CEACAM5",
    "CD30", "CCR4", "CD33", "FLT3", "TEM1", "MUC1", "MUC16", "GPNMB",
    "CMET", "FGFR2", "CEACAM7", "CD276", "AXL", "PDGFRA", "CD44V6",
    "CLEC12A", "CD123", "SLAMF7", "CD37", "FCRH5", "EGFRVIII", "CD5",
    "CD7", "CLDN6", "FAPalpha", "CEACAM6", "CD20", "CD38", "TIGIT",
    "LAG3", "CD79B", "CD117", "CD79A", "NECTIN2",
}

# Antigens that are specifically from TCGA data sources (solid tumor targets)
TCGA_ANTIGENS = {
    "HER2", "EGFR", "MESOTHELIN", "B7H3", "TROP2", "EPCAM", "CEACAM5",
    "MUC1", "MUC16", "GPNMB", "CMET", "FGFR2", "CD276", "AXL",
    "PDGFRA", "CD44V6", "GPC3", "FOLR1", "CLDN18", "NECTIN4",
    "PSMA", "PSCA", "STEAP1", "GUCY2C", "ALPPL2", "LYPD3",
    "DLL3", "GD2", "CAIX", "IL13RA2", "TEM1",
}


def classify_row(row):
    """Classify a single row into data_source, source_database, evidence_level."""
    name = str(row["antigen_name"]).upper()
    trials = int(row.get("clinical_trials_count", 0))

    # Check if this is a known real antigen
    if name in {a.upper() for a in KNOWN_ANTIGENS}:
        if trials > 10:
            source_db = "TCGA" if name in {a.upper() for a in TCGA_ANTIGENS} else "Literature"
            return pd.Series(["real", source_db, "clinical"])
        else:
            source_db = "UniProt" if name in {a.upper() for a in TCGA_ANTIGENS} else "Literature"
            return pd.Series(["validated", source_db, "preclinical"])
    else:
        return pd.Series(["synthetic", "Synthetic", "predicted"])


def main():
    # Resolve path relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "biomarker_database.csv")

    if not os.path.exists(csv_path):
        print(f"ERROR: Cannot find {csv_path}")
        sys.exit(1)

    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df):,} rows, {df['antigen_name'].nunique():,} unique antigens")

    # Apply classification
    print("Classifying biomarkers...")
    df[["data_source", "source_database", "evidence_level"]] = df.apply(classify_row, axis=1)

    # Summary stats
    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)

    ds_counts = df["data_source"].value_counts()
    unique_by_source = df.groupby("data_source")["antigen_name"].nunique()
    
    for src in ["real", "validated", "synthetic"]:
        rows = ds_counts.get(src, 0)
        unique = unique_by_source.get(src, 0)
        print(f"  {src:>12}: {rows:>7,} rows  |  {unique:>5,} unique antigens")

    print(f"\n  Total rows:           {len(df):>7,}")
    print(f"  Total unique antigens: {df['antigen_name'].nunique():>6,}")
    print(f"  Unique biomarkers:     {df['antigen_name'].nunique():>6,}")

    print("\nSource database breakdown:")
    for db, count in df["source_database"].value_counts().items():
        print(f"  {db:>12}: {count:>7,} rows")

    print("\nEvidence level breakdown:")
    for level, count in df["evidence_level"].value_counts().items():
        print(f"  {level:>12}: {count:>7,} rows")

    # Save
    print(f"\nSaving updated CSV to {csv_path}...")
    df.to_csv(csv_path, index=False)
    print("Done! CSV now has columns:", list(df.columns))


if __name__ == "__main__":
    main()
