"""
CARVanta – SQLAlchemy ORM Models
=================================
Enterprise-grade data models for the CARVanta platform.
Replaces flat CSV files with structured relational tables.
"""

from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime, Text,
    Index, func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all CARVanta ORM models."""
    pass


class Biomarker(Base):
    """
    Core biomarker/antigen data — replaces biomarker_database.csv.

    Each row represents one antigen × cancer_type association with
    expression data, scoring features, and classification metadata.
    """
    __tablename__ = "biomarkers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Identity ──────────────────────────────────────────────────────────
    antigen_name = Column(String(64), nullable=False, index=True)
    cancer_type = Column(String(128), nullable=False, index=True)

    # ── Expression Data ───────────────────────────────────────────────────
    mean_tumor_expression = Column(Float, nullable=False, default=0.0)
    mean_normal_expression = Column(Float, nullable=False, default=0.0)

    # ── Scoring Features ──────────────────────────────────────────────────
    stability_score = Column(Float, nullable=False, default=0.5)
    literature_support = Column(Float, nullable=False, default=0.3)
    immunogenicity_score = Column(Float, nullable=False, default=0.5)
    surface_accessibility = Column(Float, nullable=False, default=0.5)
    clinical_trials_count = Column(Integer, nullable=False, default=0)

    # ── Classification (v5) ───────────────────────────────────────────────
    data_source = Column(String(20), nullable=False, default="synthetic", index=True)
    source_database = Column(String(32), nullable=False, default="Synthetic")
    evidence_level = Column(String(20), nullable=False, default="predicted")

    # ── Viability Label (for ML training) ─────────────────────────────────
    viability_label = Column(String(20), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # ── Indexes for fast queries ──────────────────────────────────────────
    __table_args__ = (
        Index("idx_antigen_cancer", "antigen_name", "cancer_type"),
        Index("idx_data_source", "data_source"),
    )

    def __repr__(self):
        return f"<Biomarker {self.antigen_name} / {self.cancer_type} [{self.data_source}]>"


class APIKey(Base):
    """
    API key records — replaces in-memory _API_KEYS dict.
    Stores hashed keys with tier and rate limit info.
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    tier = Column(String(20), nullable=False, default="free")
    rate_limit = Column(Integer, nullable=False, default=60)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<APIKey {self.name} [{self.tier}]>"


class ScoringRun(Base):
    """
    Audit log for scoring requests (future use).
    Tracks what was scored, when, and by whom.
    """
    __tablename__ = "scoring_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    antigen_name = Column(String(64), nullable=False)
    cancer_type = Column(String(128), nullable=True)
    cvs_score = Column(Float, nullable=True)
    ml_score = Column(Float, nullable=True)
    adaptive_score = Column(Float, nullable=True)
    tier = Column(String(32), nullable=True)
    api_key_hash = Column(String(64), nullable=True)
    client_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<ScoringRun {self.antigen_name} @ {self.created_at}>"
