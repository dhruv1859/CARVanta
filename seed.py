"""
CARVanta – Database Seed Script
=================================
Migrates data from CSV files into the database.
Run once to initialize, or re-run to refresh data.

Usage:
    py -m db.seed
    py db/seed.py
"""

import os
import sys
import hashlib
import pandas as pd

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from db.models import Base, Biomarker, APIKey
from db.connection import engine, SessionLocal


def seed_biomarkers(session, csv_path: str) -> int:
    """Load biomarker data from CSV into database."""
    if not os.path.exists(csv_path):
        print(f"  WARNING: CSV not found at {csv_path}")
        return 0

    print(f"  Loading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df):,} rows, {df['antigen_name'].nunique()} unique antigens")

    # Clear existing biomarker data
    existing = session.query(Biomarker).count()
    if existing > 0:
        print(f"  Clearing {existing:,} existing biomarker records...")
        session.query(Biomarker).delete()
        session.flush()

    # Batch insert
    BATCH_SIZE = 5000
    records = []
    for _, row in df.iterrows():
        records.append(Biomarker(
            antigen_name=str(row["antigen_name"]),
            cancer_type=str(row["cancer_type"]),
            mean_tumor_expression=float(row.get("mean_tumor_expression", 0)),
            mean_normal_expression=float(row.get("mean_normal_expression", 0)),
            stability_score=float(row.get("stability_score", 0.5)),
            literature_support=float(row.get("literature_support", 0.3)),
            immunogenicity_score=float(row.get("immunogenicity_score", 0.5)),
            surface_accessibility=float(row.get("surface_accessibility", 0.5)),
            clinical_trials_count=int(row.get("clinical_trials_count", 0)),
            data_source=str(row.get("data_source", "synthetic")),
            source_database=str(row.get("source_database", "Synthetic")),
            evidence_level=str(row.get("evidence_level", "predicted")),
            viability_label=str(row.get("viability_label", "")),
        ))

        if len(records) >= BATCH_SIZE:
            session.bulk_save_objects(records)
            session.flush()
            records = []

    if records:
        session.bulk_save_objects(records)
        session.flush()

    total = session.query(Biomarker).count()
    print(f"  [OK] Inserted {total:,} biomarker records")
    return total


def seed_api_keys(session) -> int:
    """Load API keys from environment variables into database."""
    key_configs = [
        ("CARVANTA_API_KEY_DEV", "Development Key", "free", 60),
        ("CARVANTA_API_KEY_PRO", "Pro Access Key", "pro", 300),
        ("CARVANTA_API_KEY_ENTERPRISE", "Enterprise Key", "enterprise", 1000),
    ]

    count = 0
    for env_var, name, tier, rate_limit in key_configs:
        raw_key = os.getenv(env_var, "")
        if raw_key:
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            # Upsert: check if exists
            existing = session.query(APIKey).filter_by(key_hash=key_hash).first()
            if existing:
                existing.name = name
                existing.tier = tier
                existing.rate_limit = rate_limit
                existing.active = True
            else:
                session.add(APIKey(
                    key_hash=key_hash,
                    name=name,
                    tier=tier,
                    rate_limit=rate_limit,
                    active=True,
                ))
            count += 1

    session.flush()
    print(f"  [OK] Configured {count} API keys from environment")
    return count


def main():
    print("=" * 60)
    print("CARVanta Database Seed")
    print("=" * 60)

    # Create all tables
    print("\n[1/3] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print(f"  [OK] Tables created: {', '.join(Base.metadata.tables.keys())}")

    session = SessionLocal()
    try:
        # Seed biomarkers
        print("\n[2/3] Seeding biomarker data...")
        csv_path = os.path.join(_PROJECT_ROOT, "data", "biomarker_database.csv")
        bio_count = seed_biomarkers(session, csv_path)

        # Seed API keys
        print("\n[3/3] Configuring API keys...")
        key_count = seed_api_keys(session)

        # Commit all
        session.commit()

        # Print summary
        print("\n" + "=" * 60)
        print("SEED COMPLETE")
        print("=" * 60)
        print(f"  Biomarker records:  {bio_count:>8,}")
        print(f"  Unique antigens:    {session.query(Biomarker.antigen_name).distinct().count():>8,}")
        print(f"  Cancer types:       {session.query(Biomarker.cancer_type).distinct().count():>8,}")
        print(f"  API keys:           {key_count:>8}")

        # Classification breakdown
        if bio_count > 0:
            print("\n  Classification breakdown:")
            for src in ["real", "validated", "synthetic"]:
                count = session.query(Biomarker).filter_by(data_source=src).count()
                unique = session.query(Biomarker.antigen_name).filter_by(data_source=src).distinct().count()
                print(f"    {src:>12}: {count:>8,} rows  |  {unique:>5,} unique")

    except Exception as e:
        session.rollback()
        print(f"\n  ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
