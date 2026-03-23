"""
CARVanta – FHIR/HL7 Export Module v1
=======================================
Export antigen scoring results in FHIR R4 (Fast Healthcare Interoperability
Resources) format for interoperability with hospital EHR systems.

Generates FHIR DiagnosticReport and Observation resources.

CARVanta-Original: Hospital EHR interoperability layer.

Usage:
    from features.fhir_export import create_fhir_bundle
    bundle = create_fhir_bundle("CD19", score_data)
"""

import uuid
from datetime import datetime, timezone


def _generate_id() -> str:
    """Generate a FHIR-compliant resource ID."""
    return str(uuid.uuid4())


def create_observation(
    antigen: str,
    code: str,
    display: str,
    value: float,
    unit: str = "score",
    interpretation: str = "normal",
) -> dict:
    """Create a FHIR R4 Observation resource for a single metric."""
    interp_code = {
        "high": {"code": "H", "display": "High"},
        "low": {"code": "L", "display": "Low"},
        "normal": {"code": "N", "display": "Normal"},
        "critical": {"code": "HH", "display": "Critical high"},
    }.get(interpretation, {"code": "N", "display": "Normal"})

    return {
        "resourceType": "Observation",
        "id": _generate_id(),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "https://carvanta.ai/fhir/CodeSystem/cvs-metrics",
                    "code": code,
                    "display": display,
                }
            ],
            "text": f"CARVanta {display} for {antigen}",
        },
        "subject": {
            "display": f"Antigen Target: {antigen}",
        },
        "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
        "valueQuantity": {
            "value": round(value, 4),
            "unit": unit,
            "system": "https://carvanta.ai/fhir/units",
            "code": unit,
        },
        "interpretation": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": interp_code["code"],
                        "display": interp_code["display"],
                    }
                ]
            }
        ],
    }


def create_diagnostic_report(antigen: str, observations: list, tier: str, cvs_score: float) -> dict:
    """Create a FHIR R4 DiagnosticReport wrapping all observations."""
    return {
        "resourceType": "DiagnosticReport",
        "id": _generate_id(),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "GE",
                        "display": "Genetics",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "https://carvanta.ai/fhir/CodeSystem/reports",
                    "code": "car-t-viability",
                    "display": "CAR-T Target Viability Assessment",
                }
            ],
            "text": f"CARVanta CAR-T Viability Assessment for {antigen}",
        },
        "subject": {
            "display": f"Antigen Target: {antigen}",
        },
        "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
        "issued": datetime.now(timezone.utc).isoformat(),
        "result": [{"reference": f"Observation/{obs['id']}"} for obs in observations],
        "conclusion": (
            f"{antigen} scored {cvs_score:.3f} ({tier}). "
            f"{'Recommended for CAR-T development.' if 'Tier 1' in tier or 'Tier 2' in tier else 'Requires further investigation.'}"
        ),
        "conclusionCode": [
            {
                "coding": [
                    {
                        "system": "https://carvanta.ai/fhir/CodeSystem/tiers",
                        "code": tier.lower().replace(" ", "-").replace("---", "-"),
                        "display": tier,
                    }
                ]
            }
        ],
    }


def create_fhir_bundle(antigen: str, score_data: dict) -> dict:
    """
    Create a FHIR R4 Bundle containing a DiagnosticReport with Observations.

    Parameters
    ----------
    antigen : str
        Antigen name (e.g., 'CD19')
    score_data : dict
        Score response from the CARVanta API (/score endpoint)

    Returns
    -------
    FHIR R4 Bundle (JSON-serializable dict)
    """
    observations = []
    breakdown = score_data.get("breakdown", {})
    cvs_score = score_data.get("CVS", 0)
    tier = score_data.get("tier", "Unknown")

    # CVS Score observation
    cvs_interp = "high" if cvs_score >= 0.85 else "normal" if cvs_score >= 0.70 else "low"
    observations.append(create_observation(
        antigen, "cvs-score", "Clinical Viability Score",
        cvs_score, "score", cvs_interp,
    ))

    # Breakdown observations
    metric_map = {
        "tumor_expression": ("tumor-expr", "Tumor Expression Score"),
        "normal_expression_penalty": ("normal-penalty", "Normal Expression Penalty"),
        "specificity": ("specificity", "Tumor Specificity Ratio"),
        "stability": ("stability", "Expression Stability Score"),
        "literature": ("literature", "Literature Support Score"),
        "immunogenicity": ("immunogenicity", "Immunogenicity Score"),
        "surface_accessibility": ("surface-access", "Surface Accessibility Score"),
        "clinical_trials": ("clinical-trials", "Clinical Trial Evidence"),
    }

    for key, (code, display) in metric_map.items():
        val = breakdown.get(key, None)
        if val is not None:
            interp = "high" if val > 0.15 else "normal" if val > 0.05 else "low"
            observations.append(create_observation(
                antigen, code, display, val, "score", interp,
            ))

    # Confidence observation
    confidence = score_data.get("confidence", 0)
    observations.append(create_observation(
        antigen, "confidence", "Prediction Confidence",
        confidence, "percent", "high" if confidence > 80 else "normal",
    ))

    # Diagnostic report
    report = create_diagnostic_report(antigen, observations, tier, cvs_score)

    # Bundle
    entries = [{"fullUrl": f"urn:uuid:{report['id']}", "resource": report}]
    for obs in observations:
        entries.append({"fullUrl": f"urn:uuid:{obs['id']}", "resource": obs})

    return {
        "resourceType": "Bundle",
        "id": _generate_id(),
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": {
            "profile": ["https://carvanta.ai/fhir/StructureDefinition/cvs-bundle"],
            "source": "CARVanta AI Engine v5",
        },
        "entry": entries,
        "total": len(entries),
    }
