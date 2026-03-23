"""
CARVanta – SQLAlchemy ORM Models
=================================
Enterprise-grade data models for the CARVanta platform.
Replaces flat CSV files with structured relational tables.
Includes: Biomarkers, Auth, Patient Profiles, Research Projects.
"""

from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime, Text,
    JSON, ForeignKey, Index, func, Enum,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


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


# ═══════════════════════════════════════════════════════════════════════════════
# Module 10: Enterprise Auth & User Management
# ═══════════════════════════════════════════════════════════════════════════════

class UserRole(enum.Enum):
    """RBAC roles for CARVanta users."""
    PATIENT = "patient"
    RESEARCHER = "researcher"
    CLINICIAN = "clinician"
    ADMIN = "admin"


class User(Base):
    """
    User accounts for CARVanta Universe.
    Supports email + password auth, OAuth2 SSO, and MFA.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Identity ──────────────────────────────────────────────────────────
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # ── Profile ───────────────────────────────────────────────────────────
    full_name = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.RESEARCHER.value)
    institution = Column(String(256), nullable=True)
    country = Column(String(64), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(512), nullable=True)
    orcid_id = Column(String(20), nullable=True)  # Researcher ORCID

    # ── Status ────────────────────────────────────────────────────────────
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret = Column(String(32), nullable=True)

    # ── Usage ─────────────────────────────────────────────────────────────
    api_calls_today = Column(Integer, nullable=False, default=0)
    total_analyses = Column(Integer, nullable=False, default=0)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, nullable=False, default=0)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # ── Relationships ─────────────────────────────────────────────────────
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    patient_profiles = relationship("PatientProfile", back_populates="creator", cascade="all, delete-orphan")
    projects = relationship("Collaboration", back_populates="user")

    __table_args__ = (
        Index("idx_user_role", "role"),
        Index("idx_user_active", "is_active"),
    )

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"


class UserSession(Base):
    """
    JWT session tracking — each login creates a session.
    Enables multi-device support and session revocation.
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    device_info = Column(String(256), nullable=True)
    ip_address = Column(String(45), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session user={self.user_id} active={self.is_active}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Module 2: Patient Digital Twin
# ═══════════════════════════════════════════════════════════════════════════════

class PatientProfile(Base):
    """
    Patient intake data for Digital Twin simulation.
    Stores demographics, genomic markers, treatment history.
    """
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # ── Demographics ──────────────────────────────────────────────────────
    patient_code = Column(String(32), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    sex = Column(String(10), nullable=True)
    ethnicity = Column(String(64), nullable=True)
    weight_kg = Column(Float, nullable=True)

    # ── Cancer Details ────────────────────────────────────────────────────
    cancer_type = Column(String(128), nullable=False)
    cancer_stage = Column(String(20), nullable=True)
    diagnosis_date = Column(DateTime, nullable=True)
    tumor_burden_mm = Column(Float, nullable=True)
    metastatic = Column(Boolean, nullable=False, default=False)

    # ── Genomic Markers ───────────────────────────────────────────────────
    hla_type = Column(String(128), nullable=True)
    tumor_mutational_burden = Column(Float, nullable=True)
    microsatellite_status = Column(String(20), nullable=True)  # MSS / MSI-H
    key_mutations = Column(JSON, nullable=True)  # e.g. ["TP53", "KRAS G12D"]

    # ── Treatment History ─────────────────────────────────────────────────
    prior_treatments = Column(JSON, nullable=True)  # list of treatment records
    prior_car_t = Column(Boolean, nullable=False, default=False)
    lymphodepletion_regimen = Column(String(128), nullable=True)

    # ── Lab Values ────────────────────────────────────────────────────────
    absolute_lymphocyte_count = Column(Float, nullable=True)
    ldh_level = Column(Float, nullable=True)
    crp_level = Column(Float, nullable=True)
    il6_level = Column(Float, nullable=True)
    ferritin_level = Column(Float, nullable=True)

    # ── Simulation Results (cached) ───────────────────────────────────────
    last_simulation = Column(JSON, nullable=True)
    simulation_date = Column(DateTime, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    creator = relationship("User", back_populates="patient_profiles")

    __table_args__ = (
        Index("idx_patient_cancer", "cancer_type"),
        Index("idx_patient_creator", "creator_id"),
    )

    def __repr__(self):
        return f"<PatientProfile {self.patient_code} [{self.cancer_type}]>"


# ═══════════════════════════════════════════════════════════════════════════════
# Module 6: Research Collaboration Hub
# ═══════════════════════════════════════════════════════════════════════════════

class ResearchProject(Base):
    """
    Shared research projects — like GitHub repos for biotech.
    """
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)
    target_antigens = Column(JSON, nullable=True)
    cancer_types = Column(JSON, nullable=True)
    is_public = Column(Boolean, nullable=False, default=True)
    stars = Column(Integer, nullable=False, default=0)
    forks = Column(Integer, nullable=False, default=0)

    # ── Status ────────────────────────────────────────────────────────────
    status = Column(String(32), nullable=False, default="active")

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    collaborators = relationship("Collaboration", back_populates="project")

    def __repr__(self):
        return f"<Project {self.slug}>"


class Collaboration(Base):
    """
    Many-to-many: Users ↔ Projects with roles.
    """
    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default="contributor")  # owner, contributor, viewer
    joined_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="projects")
    project = relationship("ResearchProject", back_populates="collaborators")

    __table_args__ = (
        Index("idx_collab_user_project", "user_id", "project_id", unique=True),
    )

    def __repr__(self):
        return f"<Collab user={self.user_id} project={self.project_id}>"


# ═══════════════════════════════════════════════════════════════════════════════
# Module 5: Genomic Analyzer (FASTA support)
# ═══════════════════════════════════════════════════════════════════════════════

class GenomicUpload(Base):
    """
    Uploaded genomic files (FASTA, FASTQ, VCF) and analysis results.
    """
    __tablename__ = "genomic_uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    filename = Column(String(256), nullable=False)
    file_format = Column(String(10), nullable=False)  # fasta, fastq, vcf
    file_size_bytes = Column(Integer, nullable=True)
    sequence_count = Column(Integer, nullable=True)
    total_bases = Column(Integer, nullable=True)

    # ── Analysis Results ──────────────────────────────────────────────────
    quality_score = Column(Float, nullable=True)
    errors_found = Column(JSON, nullable=True)
    variants = Column(JSON, nullable=True)
    neoantigens = Column(JSON, nullable=True)
    tmb_score = Column(Float, nullable=True)
    msi_status = Column(String(20), nullable=True)

    # ── Matched Targets ───────────────────────────────────────────────────
    matched_antigens = Column(JSON, nullable=True)

    status = Column(String(20), nullable=False, default="pending")  # pending, processing, complete, error
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<GenomicUpload {self.filename} [{self.status}]>"
