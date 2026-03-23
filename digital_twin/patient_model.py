"""
CARVanta – Unified Patient State Model
==========================================
Central patient representation for the Digital Twin.
All engines read from / write to this model.

Features:
  - Complete patient demographics & clinical history
  - Disease state (diagnosis, staging, genomics)
  - Treatment history (prior lines, transplants)
  - Lab values with reference ranges & trending
  - Organ function assessment
  - Performance status tracking
  - CAR-T specific parameters (product, dose, manufacturing)
  - Serialization / deserialization (JSON)
  - Validation rules with clinical constraints
  - Snapshot history for longitudinal tracking
"""

import json
import math
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# Enumerations
# ═══════════════════════════════════════════════════════════════════════════════

class CancerType(str, Enum):
    DLBCL = "DLBCL"
    ALL = "ALL"
    MCL = "MCL"
    FL = "FL"
    CLL = "CLL"
    MULTIPLE_MYELOMA = "Multiple Myeloma"
    PMBCL = "PMBCL"
    HGBCL = "HGBCL"
    OTHER = "Other"


class Stage(str, Enum):
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"
    NOT_APPLICABLE = "N/A"


class ECOGStatus(int, Enum):
    FULLY_ACTIVE = 0
    RESTRICTED = 1
    AMBULATORY = 2
    LIMITED_SELF_CARE = 3
    DISABLED = 4


class MolecularSubtype(str, Enum):
    GCB = "GCB"
    ABC = "ABC"
    UNCLASSIFIED = "Unclassified"
    NOT_APPLICABLE = "N/A"


class CARTProduct(str, Enum):
    AXI_CEL = "axi-cel"
    TISA_CEL = "tisa-cel"
    LISO_CEL = "liso-cel"
    BREXU_CEL = "brexu-cel"
    IDE_CEL = "ide-cel"
    CILTA_CEL = "cilta-cel"
    INVESTIGATIONAL = "investigational"


class TreatmentPhase(str, Enum):
    PRE_SCREENING = "pre_screening"
    SCREENING = "screening"
    LEUKAPHERESIS = "leukapheresis"
    MANUFACTURING = "manufacturing"
    BRIDGING = "bridging"
    LYMPHODEPLETION = "lymphodepletion"
    INFUSION = "infusion"
    MONITORING = "monitoring"
    FOLLOW_UP = "follow_up"


# ═══════════════════════════════════════════════════════════════════════════════
# Lab Value Model
# ═══════════════════════════════════════════════════════════════════════════════

LAB_REFERENCE_RANGES = {
    "wbc": {"unit": "×10⁹/L", "low": 4.0, "high": 11.0, "critical_low": 1.0, "critical_high": 30.0},
    "anc": {"unit": "×10⁹/L", "low": 1.5, "high": 8.0, "critical_low": 0.5, "critical_high": None},
    "alc": {"unit": "×10⁹/L", "low": 1.0, "high": 4.8, "critical_low": 0.2, "critical_high": None},
    "hemoglobin": {"unit": "g/dL", "low": 12.0, "high": 17.5, "critical_low": 7.0, "critical_high": 20.0},
    "platelets": {"unit": "×10⁹/L", "low": 150, "high": 400, "critical_low": 20, "critical_high": 1000},
    "ldh": {"unit": "U/L", "low": 140, "high": 280, "critical_low": None, "critical_high": 1000},
    "crp": {"unit": "mg/L", "low": 0, "high": 10, "critical_low": None, "critical_high": 200},
    "ferritin": {"unit": "ng/mL", "low": 20, "high": 300, "critical_low": None, "critical_high": 10000},
    "il6": {"unit": "pg/mL", "low": 0, "high": 7, "critical_low": None, "critical_high": 1000},
    "creatinine": {"unit": "mg/dL", "low": 0.6, "high": 1.2, "critical_low": None, "critical_high": 4.0},
    "alt": {"unit": "U/L", "low": 7, "high": 56, "critical_low": None, "critical_high": 500},
    "ast": {"unit": "U/L", "low": 10, "high": 40, "critical_low": None, "critical_high": 500},
    "bilirubin": {"unit": "mg/dL", "low": 0.1, "high": 1.2, "critical_low": None, "critical_high": 5.0},
    "albumin": {"unit": "g/dL", "low": 3.5, "high": 5.0, "critical_low": 2.0, "critical_high": None},
    "igg": {"unit": "mg/dL", "low": 700, "high": 1600, "critical_low": 200, "critical_high": None},
    "fibrinogen": {"unit": "mg/dL", "low": 200, "high": 400, "critical_low": 100, "critical_high": 800},
    "d_dimer": {"unit": "ng/mL", "low": 0, "high": 500, "critical_low": None, "critical_high": 5000},
    "troponin": {"unit": "ng/mL", "low": 0, "high": 0.04, "critical_low": None, "critical_high": 0.4},
    "bnp": {"unit": "pg/mL", "low": 0, "high": 100, "critical_low": None, "critical_high": 900},
    "beta2_microglobulin": {"unit": "mg/L", "low": 0.8, "high": 2.2, "critical_low": None, "critical_high": 5.5},
}


@dataclass
class LabValue:
    """A single lab measurement with context."""
    name: str
    value: float
    unit: str = ""
    measured_at: str = ""
    status: str = "normal"  # normal, low, high, critical_low, critical_high

    def evaluate(self) -> str:
        """Evaluate lab value against reference ranges."""
        ref = LAB_REFERENCE_RANGES.get(self.name)
        if not ref:
            return "unknown"
        if ref.get("critical_low") and self.value <= ref["critical_low"]:
            self.status = "critical_low"
        elif ref.get("critical_high") and self.value >= ref["critical_high"]:
            self.status = "critical_high"
        elif self.value < ref["low"]:
            self.status = "low"
        elif self.value > ref["high"]:
            self.status = "high"
        else:
            self.status = "normal"
        self.unit = ref["unit"]
        return self.status


@dataclass
class LabPanel:
    """Collection of lab values at a timepoint."""
    panel_date: str = ""
    values: Dict[str, LabValue] = field(default_factory=dict)

    def set_lab(self, name: str, value: float, measured_at: str = "") -> LabValue:
        lab = LabValue(name=name, value=value, measured_at=measured_at or self.panel_date)
        lab.evaluate()
        self.values[name] = lab
        return lab

    def get_lab(self, name: str) -> Optional[LabValue]:
        return self.values.get(name)

    def get_value(self, name: str, default: float = 0) -> float:
        lab = self.values.get(name)
        return lab.value if lab else default

    def get_abnormal(self) -> List[LabValue]:
        return [v for v in self.values.values() if v.status != "normal"]

    def get_critical(self) -> List[LabValue]:
        return [v for v in self.values.values() if "critical" in v.status]

    def to_dict(self) -> Dict:
        return {
            "panel_date": self.panel_date,
            "values": {k: {"value": v.value, "unit": v.unit, "status": v.status} for k, v in self.values.items()},
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Genomic Profile
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GenomicMarker:
    """A single genomic finding."""
    gene: str
    alteration: str  # mutation, amplification, deletion, rearrangement
    variant: str = ""
    vaf: float = 0.0  # variant allele frequency
    pathogenic: bool = False
    car_t_impact: str = "neutral"  # favorable, unfavorable, neutral


@dataclass
class PatientGenomics:
    """Patient's genomic profile."""
    tp53_mutated: bool = False
    myc_rearranged: bool = False
    bcl2_rearranged: bool = False
    bcl6_rearranged: bool = False
    double_hit: bool = False
    triple_hit: bool = False
    molecular_subtype: str = "Unclassified"
    tmb: float = 0.0  # mutations per Mb
    msi_status: str = "MSS"
    pd_l1_expression: float = 0.0
    markers: List[GenomicMarker] = field(default_factory=list)

    def compute_double_hit(self):
        self.double_hit = self.myc_rearranged and (self.bcl2_rearranged or self.bcl6_rearranged)
        self.triple_hit = self.myc_rearranged and self.bcl2_rearranged and self.bcl6_rearranged

    def risk_category(self) -> str:
        if self.triple_hit or (self.double_hit and self.tp53_mutated):
            return "very_high"
        if self.double_hit or self.tp53_mutated:
            return "high"
        if self.tp53_mutated or self.tmb > 20:
            return "intermediate"
        return "standard"


# ═══════════════════════════════════════════════════════════════════════════════
# Treatment History
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PriorTherapy:
    """Record of a prior line of therapy."""
    line_number: int
    regimen: str
    start_date: str = ""
    end_date: str = ""
    best_response: str = "NE"  # CR, PR, SD, PD, NE
    duration_months: float = 0
    reason_discontinued: str = ""  # progression, toxicity, completed


@dataclass
class TreatmentHistory:
    """Complete treatment history."""
    prior_lines: int = 0
    therapies: List[PriorTherapy] = field(default_factory=list)
    prior_auto_sct: bool = False
    prior_allo_sct: bool = False
    prior_car_t: bool = False
    prior_bispecific: bool = False
    prior_radiation: bool = False
    refractory_to_last_line: bool = False

    def add_therapy(self, regimen: str, response: str = "NE", **kwargs) -> PriorTherapy:
        self.prior_lines += 1
        therapy = PriorTherapy(
            line_number=self.prior_lines, regimen=regimen,
            best_response=response, **kwargs,
        )
        self.therapies.append(therapy)
        return therapy


# ═══════════════════════════════════════════════════════════════════════════════
# Organ Function
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OrganFunction:
    """Organ function assessment for eligibility."""
    lvef: Optional[float] = None  # Left ventricular ejection fraction %
    creatinine_clearance: Optional[float] = None  # mL/min
    spo2: Optional[float] = None  # % on room air
    alt_uln_ratio: Optional[float] = None
    ast_uln_ratio: Optional[float] = None
    bilirubin_uln_ratio: Optional[float] = None
    pulmonary_function: Optional[str] = None  # normal, mild, moderate, severe

    def cardiac_eligible(self, threshold: float = 40) -> bool:
        if self.lvef is None:
            return True  # not assessed
        return self.lvef >= threshold

    def renal_eligible(self, threshold: float = 40) -> bool:
        if self.creatinine_clearance is None:
            return True
        return self.creatinine_clearance >= threshold

    def hepatic_eligible(self) -> bool:
        if self.alt_uln_ratio and self.alt_uln_ratio > 3:
            return False
        if self.bilirubin_uln_ratio and self.bilirubin_uln_ratio > 2:
            return False
        return True

    def pulmonary_eligible(self) -> bool:
        if self.spo2 is not None and self.spo2 < 92:
            return False
        return True

    def all_eligible(self) -> Tuple[bool, List[str]]:
        failures = []
        if not self.cardiac_eligible():
            failures.append(f"LVEF {self.lvef}% below threshold")
        if not self.renal_eligible():
            failures.append(f"CrCl {self.creatinine_clearance} mL/min below threshold")
        if not self.hepatic_eligible():
            failures.append("Hepatic function abnormal")
        if not self.pulmonary_eligible():
            failures.append(f"SpO2 {self.spo2}% below threshold")
        return len(failures) == 0, failures


# ═══════════════════════════════════════════════════════════════════════════════
# CAR-T Treatment Parameters
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CARTParameters:
    """CAR-T specific treatment parameters."""
    product: str = "axi-cel"
    target_antigen: str = "CD19"
    costimulatory_domain: str = "CD28"
    dose_cells: float = 1e8
    manufacturing_start: str = ""
    manufacturing_complete: str = ""
    manufacturing_days: int = 0
    manufacturing_success: bool = True
    manufacturing_failure_reason: str = ""
    lymphodepletion_regimen: str = "flu_cy"
    lymphodepletion_start: str = ""
    infusion_date: str = ""
    bridging_therapy: str = ""
    bridging_response: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Core Patient Model
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PatientState:
    """
    Complete patient state representation for the Digital Twin.
    This is the single source of truth that all engines read from.
    """
    # Demographics
    patient_id: str = ""
    first_name: str = ""
    last_name: str = ""
    age: int = 55
    sex: str = "M"
    weight_kg: float = 70.0
    height_cm: float = 170.0
    bsa: float = 1.8  # body surface area m²

    # Disease
    cancer_type: str = "DLBCL"
    cancer_stage: str = "III"
    date_of_diagnosis: str = ""
    molecular_subtype: str = "Unclassified"
    primary_site: str = ""
    tumor_burden_mm: float = 50.0
    extranodal_sites: int = 0
    bone_marrow_involved: bool = False
    cns_involved: bool = False

    # Performance
    ecog: int = 1
    karnofsky: int = 80

    # Genomics
    genomics: PatientGenomics = field(default_factory=PatientGenomics)

    # Labs
    baseline_labs: LabPanel = field(default_factory=LabPanel)
    current_labs: LabPanel = field(default_factory=LabPanel)
    lab_history: List[LabPanel] = field(default_factory=list)

    # Treatment
    treatment_history: TreatmentHistory = field(default_factory=TreatmentHistory)
    organ_function: OrganFunction = field(default_factory=OrganFunction)
    cart_parameters: CARTParameters = field(default_factory=CARTParameters)
    current_phase: str = "pre_screening"

    # Comorbidities
    comorbidities: List[str] = field(default_factory=list)
    active_infections: bool = False
    hiv_positive: bool = False
    hepatitis_b: bool = False
    hepatitis_c: bool = False

    # Insurance / access
    insurance_type: str = "private"
    country: str = "India"
    treating_center: str = ""

    # Snapshots
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.bsa = self._calculate_bsa()

    def _calculate_bsa(self) -> float:
        """Mosteller formula for BSA."""
        if self.weight_kg > 0 and self.height_cm > 0:
            return round(math.sqrt(self.weight_kg * self.height_cm / 3600), 2)
        return 1.8

    def update_labs(self, labs: Dict[str, float], date: str = "") -> LabPanel:
        """Update current labs and archive previous."""
        if self.current_labs.values:
            self.lab_history.append(self.current_labs)
        panel = LabPanel(panel_date=date or datetime.now(timezone.utc).isoformat())
        for name, value in labs.items():
            panel.set_lab(name, value)
        self.current_labs = panel
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return panel

    def get_risk_factors(self) -> Dict[str, Any]:
        """Aggregate risk factors from all data sources."""
        factors = []
        risk_score = 0

        if self.age > 65:
            factors.append({"factor": "Age >65", "impact": "moderate", "score": 1})
            risk_score += 1
        if self.ecog >= 2:
            factors.append({"factor": f"ECOG {self.ecog}", "impact": "high", "score": 2})
            risk_score += 2
        if self.tumor_burden_mm > 80:
            factors.append({"factor": "High tumor burden (>80mm)", "impact": "high", "score": 2})
            risk_score += 2
        if self.genomics.double_hit:
            factors.append({"factor": "Double-hit biology", "impact": "high", "score": 2})
            risk_score += 2
        if self.genomics.tp53_mutated:
            factors.append({"factor": "TP53 mutation", "impact": "high", "score": 2})
            risk_score += 2
        if self.treatment_history.prior_lines >= 4:
            factors.append({"factor": f"{self.treatment_history.prior_lines} prior lines", "impact": "moderate", "score": 1})
            risk_score += 1
        if self.treatment_history.prior_car_t:
            factors.append({"factor": "Prior CAR-T", "impact": "high", "score": 2})
            risk_score += 2

        ldh_val = self.current_labs.get_value("ldh")
        if ldh_val > 400:
            factors.append({"factor": f"Elevated LDH ({ldh_val})", "impact": "moderate", "score": 1})
            risk_score += 1

        risk_level = "low" if risk_score <= 2 else "moderate" if risk_score <= 5 else "high" if risk_score <= 8 else "very_high"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": factors,
            "max_possible_score": 15,
        }

    def check_eligibility_summary(self) -> Dict[str, Any]:
        """Quick eligibility check."""
        issues = []
        if self.ecog > 1:
            issues.append(f"ECOG {self.ecog} (requires 0-1)")
        if self.active_infections:
            issues.append("Active infection")
        if self.hiv_positive:
            issues.append("HIV positive")

        organ_ok, organ_issues = self.organ_function.all_eligible()
        issues.extend(organ_issues)

        return {
            "likely_eligible": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues),
        }

    def generate_id(self) -> str:
        """Generate deterministic patient ID from demographics."""
        raw = f"{self.first_name}_{self.last_name}_{self.age}_{self.cancer_type}"
        self.patient_id = f"PT-{hashlib.md5(raw.encode()).hexdigest()[:8].upper()}"
        return self.patient_id

    def to_dict(self) -> Dict[str, Any]:
        """Serialize patient state to dictionary."""
        return {
            "patient_id": self.patient_id,
            "demographics": {
                "age": self.age, "sex": self.sex,
                "weight_kg": self.weight_kg, "height_cm": self.height_cm,
                "bsa": self.bsa,
            },
            "disease": {
                "cancer_type": self.cancer_type, "stage": self.cancer_stage,
                "molecular_subtype": self.molecular_subtype,
                "tumor_burden_mm": self.tumor_burden_mm,
                "bone_marrow_involved": self.bone_marrow_involved,
                "cns_involved": self.cns_involved,
            },
            "performance": {"ecog": self.ecog, "karnofsky": self.karnofsky},
            "genomics": {
                "tp53": self.genomics.tp53_mutated,
                "double_hit": self.genomics.double_hit,
                "risk_category": self.genomics.risk_category(),
                "tmb": self.genomics.tmb,
            },
            "treatment_history": {
                "prior_lines": self.treatment_history.prior_lines,
                "prior_car_t": self.treatment_history.prior_car_t,
                "prior_sct": self.treatment_history.prior_auto_sct or self.treatment_history.prior_allo_sct,
                "refractory": self.treatment_history.refractory_to_last_line,
            },
            "current_labs": self.current_labs.to_dict(),
            "risk_factors": self.get_risk_factors(),
            "eligibility": self.check_eligibility_summary(),
            "cart": {
                "product": self.cart_parameters.product,
                "phase": self.current_phase,
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_form_data(cls, data: Dict[str, Any]) -> "PatientState":
        """Create patient from intake form data."""
        patient = cls(
            age=data.get("age", 55),
            sex=data.get("sex", "M"),
            weight_kg=data.get("weight_kg", 70),
            height_cm=data.get("height_cm", 170),
            cancer_type=data.get("cancer_type", "DLBCL"),
            cancer_stage=data.get("cancer_stage", "III"),
            tumor_burden_mm=data.get("tumor_burden_mm", 50),
            ecog=data.get("ecog", 1),
        )

        # Genomics
        if data.get("tp53_mutated"):
            patient.genomics.tp53_mutated = True
        if data.get("double_hit"):
            patient.genomics.double_hit = True

        # Treatment history
        patient.treatment_history.prior_lines = data.get("prior_lines", 0)
        patient.treatment_history.prior_car_t = data.get("prior_car_t", False)

        # Labs
        labs = {}
        for lab_name in ["ldh", "crp", "ferritin", "alc", "platelets", "hemoglobin", "il6"]:
            if data.get(lab_name) is not None:
                labs[lab_name] = data[lab_name]
        if labs:
            patient.update_labs(labs)

        # CAR-T
        patient.cart_parameters.product = data.get("product", "axi-cel")

        patient.generate_id()
        return patient


# ═══════════════════════════════════════════════════════════════════════════════
# Clinical Scoring Systems
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_ipi(
    age: int,
    cancer_stage: str,
    ecog: int,
    ldh_ratio: float = 1.0,
    extranodal_sites: int = 0,
) -> Dict[str, Any]:
    """
    Calculate International Prognostic Index (IPI) for DLBCL.
    Each factor scores 1 point:
      - Age > 60
      - Stage III or IV
      - ECOG ≥ 2
      - LDH > ULN (ratio > 1)
      - Extranodal sites ≥ 2
    """
    score = 0
    factors = []

    if age > 60:
        score += 1
        factors.append("Age >60")
    if cancer_stage in ("III", "IV"):
        score += 1
        factors.append(f"Stage {cancer_stage}")
    if ecog >= 2:
        score += 1
        factors.append(f"ECOG {ecog}")
    if ldh_ratio > 1.0:
        score += 1
        factors.append(f"Elevated LDH ({ldh_ratio:.1f}× ULN)")
    if extranodal_sites >= 2:
        score += 1
        factors.append(f"{extranodal_sites} extranodal sites")

    # Risk group
    if score <= 1:
        risk_group = "Low"
        five_yr_os = 73
    elif score == 2:
        risk_group = "Low-Intermediate"
        five_yr_os = 51
    elif score == 3:
        risk_group = "High-Intermediate"
        five_yr_os = 43
    else:
        risk_group = "High"
        five_yr_os = 26

    return {
        "scoring_system": "IPI",
        "score": score,
        "max_score": 5,
        "risk_group": risk_group,
        "five_year_os_pct": five_yr_os,
        "factors_present": factors,
        "factors_absent": [f for f in ["Age >60", "Stage III/IV", "ECOG ≥2", "LDH elevated", "≥2 EN sites"] if f not in factors],
    }


def calculate_ripi(
    age: int,
    cancer_stage: str,
    ecog: int,
    ldh_ratio: float = 1.0,
    extranodal_sites: int = 0,
) -> Dict[str, Any]:
    """
    Revised IPI (R-IPI) — redistributes IPI into 3 groups.
    """
    ipi = calculate_ipi(age, cancer_stage, ecog, ldh_ratio, extranodal_sites)
    score = ipi["score"]

    if score == 0:
        r_group = "Very Good"
        four_yr_os = 94
        four_yr_pfs = 94
    elif score <= 2:
        r_group = "Good"
        four_yr_os = 79
        four_yr_pfs = 80
    else:
        r_group = "Poor"
        four_yr_os = 55
        four_yr_pfs = 53

    return {
        "scoring_system": "R-IPI",
        "ipi_score": score,
        "risk_group": r_group,
        "four_year_os_pct": four_yr_os,
        "four_year_pfs_pct": four_yr_pfs,
        "ipi_detail": ipi,
    }


def calculate_nccn_ipi(
    age: int,
    cancer_stage: str,
    ecog: int,
    ldh_ratio: float = 1.0,
    extranodal_sites: int = 0,
    bone_marrow: bool = False,
    cns: bool = False,
    liver: bool = False,
    lung: bool = False,
    gi: bool = False,
) -> Dict[str, Any]:
    """
    NCCN-IPI — enhanced IPI with refined age/LDH and specific EN sites.
    """
    score = 0
    factors = []

    # Age (0-3 points)
    if 41 <= age <= 60:
        score += 1
        factors.append("Age 41-60 (+1)")
    elif 61 <= age <= 75:
        score += 2
        factors.append("Age 61-75 (+2)")
    elif age > 75:
        score += 3
        factors.append("Age >75 (+3)")

    # LDH (0-2 points)
    if 1.0 < ldh_ratio <= 3.0:
        score += 1
        factors.append(f"LDH 1-3x ULN (+1)")
    elif ldh_ratio > 3.0:
        score += 2
        factors.append(f"LDH >3x ULN (+2)")

    # Stage III/IV
    if cancer_stage in ("III", "IV"):
        score += 1
        factors.append(f"Stage {cancer_stage} (+1)")

    # ECOG ≥ 2
    if ecog >= 2:
        score += 1
        factors.append(f"ECOG {ecog} (+1)")

    # Specific extranodal sites (0-1 point)
    high_risk_sites = []
    if bone_marrow:
        high_risk_sites.append("Bone Marrow")
    if cns:
        high_risk_sites.append("CNS")
    if liver:
        high_risk_sites.append("Liver")
    if lung:
        high_risk_sites.append("Lung")
    if gi:
        high_risk_sites.append("GI")
    if high_risk_sites:
        score += 1
        factors.append(f"High-risk EN: {', '.join(high_risk_sites)} (+1)")

    # Risk group
    if score <= 1:
        risk_group = "Low"
        five_yr_os = 96
    elif score <= 3:
        risk_group = "Low-Intermediate"
        five_yr_os = 82
    elif score <= 5:
        risk_group = "High-Intermediate"
        five_yr_os = 64
    else:
        risk_group = "High"
        five_yr_os = 33

    return {
        "scoring_system": "NCCN-IPI",
        "score": score,
        "max_score": 8,
        "risk_group": risk_group,
        "five_year_os_pct": five_yr_os,
        "factors_present": factors,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Body Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_bmi(weight_kg: float, height_cm: float) -> Dict[str, Any]:
    """Calculate BMI and classify."""
    if height_cm <= 0 or weight_kg <= 0:
        return {"bmi": 0, "category": "Invalid", "car_t_impact": "unknown"}

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        category = "Underweight"
        impact = "May affect T-cell yield during apheresis; nutritional support recommended"
    elif bmi < 25:
        category = "Normal"
        impact = "No BMI-related concerns for CAR-T"
    elif bmi < 30:
        category = "Overweight"
        impact = "Minimal impact; monitor drug distribution"
    elif bmi < 35:
        category = "Obese Class I"
        impact = "Increased tocilizumab dose may be needed (8mg/kg); consider CRS risk"
    elif bmi < 40:
        category = "Obese Class II"
        impact = "Higher CRS risk, consider prophylactic measures; ICU may be needed"
    else:
        category = "Obese Class III"
        impact = "Significantly higher CRS/toxicity risk; careful dose adjustments required"

    return {
        "bmi": round(bmi, 1),
        "category": category,
        "height_m": round(height_m, 2),
        "car_t_impact": impact,
    }


def cockcroft_gault(
    age: int,
    weight_kg: float,
    creatinine: float,
    sex: str = "M",
) -> Dict[str, Any]:
    """
    Cockcroft-Gault formula for creatinine clearance.
    CrCl = [(140 - age) × weight] / (72 × SCr)  ×  0.85 for females
    """
    if creatinine <= 0:
        return {"crcl": 0, "eligible": False, "note": "Invalid creatinine"}

    crcl = ((140 - age) * weight_kg) / (72 * creatinine)
    if sex.upper() == "F":
        crcl *= 0.85

    eligible = crcl >= 40  # Most CAR-T protocols require CrCl ≥ 40
    if crcl >= 90:
        stage = "Normal (G1)"
    elif crcl >= 60:
        stage = "Mild (G2)"
    elif crcl >= 30:
        stage = "Moderate (G3a/b)"
    elif crcl >= 15:
        stage = "Severe (G4)"
    else:
        stage = "Kidney Failure (G5)"

    return {
        "crcl_ml_min": round(crcl, 1),
        "ckd_stage": stage,
        "eligible_for_cart": eligible,
        "threshold": "≥40 mL/min",
        "note": "Consider dose adjustments for lymphodepletion if moderate impairment" if 30 <= crcl < 60 else "",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Lymphodepletion Dose Calculator
# ═══════════════════════════════════════════════════════════════════════════════

LYMPHODEPLETION_REGIMENS = {
    "flu_cy": {
        "name": "Fludarabine / Cyclophosphamide",
        "description": "Standard LD: Flu 30mg/m² + Cy 500mg/m², days -5 to -3",
        "drugs": [
            {"drug": "Fludarabine", "dose_per_m2": 30, "unit": "mg/m²", "days": 3, "route": "IV"},
            {"drug": "Cyclophosphamide", "dose_per_m2": 500, "unit": "mg/m²", "days": 3, "route": "IV"},
        ],
        "products": ["axi-cel", "liso-cel", "brexu-cel"],
    },
    "flu_cy_reduced": {
        "name": "Reduced Flu/Cy",
        "description": "Reduced-intensity LD: Flu 25mg/m² + Cy 250mg/m², days -5 to -3",
        "drugs": [
            {"drug": "Fludarabine", "dose_per_m2": 25, "unit": "mg/m²", "days": 3, "route": "IV"},
            {"drug": "Cyclophosphamide", "dose_per_m2": 250, "unit": "mg/m²", "days": 3, "route": "IV"},
        ],
        "products": ["tisa-cel"],
    },
    "bendamustine": {
        "name": "Bendamustine",
        "description": "Alternative LD: Benda 90mg/m², days -5 to -3",
        "drugs": [
            {"drug": "Bendamustine", "dose_per_m2": 90, "unit": "mg/m²", "days": 3, "route": "IV"},
        ],
        "products": ["tisa-cel"],
    },
}


def calculate_ld_doses(
    bsa: float,
    regimen: str = "flu_cy",
    renal_adjustment: bool = False,
    crcl: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate lymphodepletion drug doses based on BSA."""
    reg = LYMPHODEPLETION_REGIMENS.get(regimen, LYMPHODEPLETION_REGIMENS["flu_cy"])

    doses = []
    for drug in reg["drugs"]:
        dose = drug["dose_per_m2"] * bsa
        total_course = dose * drug["days"]

        # Renal adjustment for fludarabine
        if renal_adjustment and drug["drug"] == "Fludarabine" and crcl:
            if crcl < 50:
                dose *= 0.8  # 20% reduction
                total_course = dose * drug["days"]
                adjustment = "20% reduction for CrCl <50"
            elif crcl < 30:
                dose *= 0.5
                total_course = dose * drug["days"]
                adjustment = "50% reduction for CrCl <30"
            else:
                adjustment = "No adjustment needed"
        else:
            adjustment = "N/A"

        doses.append({
            "drug": drug["drug"],
            "dose_per_day": f"{dose:.0f} mg",
            "days": drug["days"],
            "total_course": f"{total_course:.0f} mg",
            "route": drug["route"],
            "renal_adjustment": adjustment,
        })

    return {
        "regimen": reg["name"],
        "description": reg["description"],
        "bsa_used": round(bsa, 2),
        "doses": doses,
        "supported_products": reg["products"],
        "pre_medications": [
            "Ondansetron 8mg IV (antiemetic)",
            "IV hydration — 1L NS pre and post",
            "Allopurinol 300mg PO daily (TLS prophylaxis)",
        ],
        "monitoring": [
            "CBC daily during LD and for 7 days post",
            "BMP daily, including tumor lysis labs",
            "ALC target: <500/μL before infusion",
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Comprehensive Validation
# ═══════════════════════════════════════════════════════════════════════════════

def validate_patient_for_cart(patient: PatientState) -> Dict[str, Any]:
    """
    Comprehensive CAR-T eligibility validation.
    Returns structured pass/fail for each criterion.
    """
    checks = []
    critical_failures = 0
    warnings = 0

    # 1. ECOG
    ecog_pass = patient.ecog <= 1
    checks.append({
        "criterion": "Performance Status",
        "requirement": "ECOG 0-1",
        "value": f"ECOG {patient.ecog}",
        "status": "pass" if ecog_pass else "fail",
        "category": "functional",
    })
    if not ecog_pass:
        critical_failures += 1

    # 2. Age
    checks.append({
        "criterion": "Age",
        "requirement": "No strict cutoff; assess on case-by-case",
        "value": f"{patient.age} years",
        "status": "pass" if patient.age < 75 else "warning",
        "category": "demographic",
    })
    if patient.age >= 75:
        warnings += 1

    # 3. Active infections
    infection_pass = not patient.active_infections
    checks.append({
        "criterion": "Infections",
        "requirement": "No active uncontrolled infections",
        "value": "Active infection" if patient.active_infections else "None",
        "status": "pass" if infection_pass else "fail",
        "category": "infection",
    })
    if not infection_pass:
        critical_failures += 1

    # 4. HIV
    hiv_pass = not patient.hiv_positive
    checks.append({
        "criterion": "HIV Status",
        "requirement": "Negative",
        "value": "Positive" if patient.hiv_positive else "Negative",
        "status": "pass" if hiv_pass else "fail",
        "category": "infection",
    })
    if not hiv_pass:
        critical_failures += 1

    # 5. Cardiac
    cardiac_pass, cardiac_msg = True, "Not assessed"
    if patient.organ_function.lvef is not None:
        cardiac_pass = patient.organ_function.lvef >= 40
        cardiac_msg = f"LVEF {patient.organ_function.lvef}%"
    checks.append({
        "criterion": "Cardiac Function",
        "requirement": "LVEF ≥ 40%",
        "value": cardiac_msg,
        "status": "pass" if cardiac_pass else "fail",
        "category": "organ_function",
    })
    if not cardiac_pass:
        critical_failures += 1

    # 6. Renal
    renal_pass, renal_msg = True, "Not assessed"
    if patient.organ_function.creatinine_clearance is not None:
        renal_pass = patient.organ_function.creatinine_clearance >= 40
        renal_msg = f"CrCl {patient.organ_function.creatinine_clearance} mL/min"
    checks.append({
        "criterion": "Renal Function",
        "requirement": "CrCl ≥ 40 mL/min",
        "value": renal_msg,
        "status": "pass" if renal_pass else "fail",
        "category": "organ_function",
    })
    if not renal_pass:
        critical_failures += 1

    # 7. Hepatic
    hepatic_pass = patient.organ_function.hepatic_eligible()
    checks.append({
        "criterion": "Hepatic Function",
        "requirement": "ALT ≤3× ULN, Bilirubin ≤2× ULN",
        "value": "Within limits" if hepatic_pass else "Abnormal",
        "status": "pass" if hepatic_pass else "fail",
        "category": "organ_function",
    })
    if not hepatic_pass:
        critical_failures += 1

    # 8. Pulmonary
    pulm_pass = patient.organ_function.pulmonary_eligible()
    checks.append({
        "criterion": "Pulmonary Function",
        "requirement": "SpO2 ≥ 92% on room air",
        "value": f"SpO2 {patient.organ_function.spo2}%" if patient.organ_function.spo2 else "Not assessed",
        "status": "pass" if pulm_pass else "fail",
        "category": "organ_function",
    })
    if not pulm_pass:
        critical_failures += 1

    # 9. CNS disease
    cns_check = not patient.cns_involved
    checks.append({
        "criterion": "CNS Disease",
        "requirement": "No active CNS involvement (most protocols)",
        "value": "Present" if patient.cns_involved else "Absent",
        "status": "pass" if cns_check else "warning",
        "category": "disease",
    })
    if not cns_check:
        warnings += 1

    # 10. Prior lines
    checks.append({
        "criterion": "Prior Therapy",
        "requirement": "≥2 prior lines (for most indications)",
        "value": f"{patient.treatment_history.prior_lines} prior lines",
        "status": "pass" if patient.treatment_history.prior_lines >= 2 else "warning",
        "category": "treatment",
    })
    if patient.treatment_history.prior_lines < 2:
        warnings += 1

    # Overall
    total_checks = len(checks)
    passed = sum(1 for c in checks if c["status"] == "pass")
    overall = "eligible" if critical_failures == 0 else "ineligible"

    return {
        "overall_status": overall,
        "total_checks": total_checks,
        "passed": passed,
        "critical_failures": critical_failures,
        "warnings": warnings,
        "checks": checks,
        "recommendation": (
            "Patient meets all eligibility criteria for CAR-T therapy"
            if overall == "eligible" and warnings == 0
            else "Patient meets core eligibility — review warnings before proceeding"
            if overall == "eligible"
            else f"Patient has {critical_failures} critical eligibility failure(s) — CAR-T therapy not recommended without resolution"
        ),
    }
