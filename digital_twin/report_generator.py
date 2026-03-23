"""
CARVanta – Clinical Report Generator
========================================
Generates downloadable clinical simulation reports for patients.
Features:
  - Comprehensive patient summary
  - Treatment simulation results
  - Risk assessment with visual indicators
  - Genomic findings
  - Adverse event predictions
  - Treatment recommendations
  - Follow-up schedule
  - HTML-based report for download
"""

import math
import random
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# Report Data Builders
# ═══════════════════════════════════════════════════════════════════════════════

def generate_patient_report(
    patient_age: int = 55,
    sex: str = "M",
    cancer_type: str = "DLBCL",
    cancer_stage: str = "III",
    tumor_burden_mm: float = 50,
    ecog: int = 1,
    product: str = "axi-cel",
    prior_lines: int = 3,
    ldh: Optional[float] = None,
    ferritin: Optional[float] = None,
    tp53_mutated: bool = False,
    double_hit: bool = False,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate a comprehensive clinical simulation report."""
    rng = random.Random(seed or 42)

    report_id = hashlib.md5(f"{patient_age}{cancer_type}{product}{rng.random()}".encode()).hexdigest()[:10].upper()
    generated_at = datetime.now(timezone.utc)

    # Simulate lab values if not provided
    ldh = ldh or rng.gauss(250, 80)
    ferritin = ferritin or rng.gauss(400, 150)
    crp = rng.gauss(15, 8)
    il6 = rng.gauss(8, 5)
    alc = rng.gauss(1.2, 0.5)
    platelets = rng.gauss(180, 50)
    hemoglobin = rng.gauss(11.5, 1.5)
    wbc = rng.gauss(6.5, 2)
    creatinine = rng.gauss(0.9, 0.2)
    albumin = rng.gauss(3.8, 0.5)

    # ─── Risk Assessment ────────────────────────────────────────────────────
    risk_score = 0
    risk_factors = []

    if patient_age > 65:
        risk_score += 1
        risk_factors.append({"factor": "Age >65", "score": 1, "impact": "moderate"})
    if ecog >= 2:
        risk_score += 2
        risk_factors.append({"factor": f"ECOG {ecog}", "score": 2, "impact": "high"})
    if tumor_burden_mm > 80:
        risk_score += 2
        risk_factors.append({"factor": "High tumor burden", "score": 2, "impact": "high"})
    if ldh > 400:
        risk_score += 1
        risk_factors.append({"factor": "Elevated LDH", "score": 1, "impact": "moderate"})
    if tp53_mutated:
        risk_score += 2
        risk_factors.append({"factor": "TP53 mutation", "score": 2, "impact": "high"})
    if double_hit:
        risk_score += 2
        risk_factors.append({"factor": "Double-hit biology", "score": 2, "impact": "high"})
    if prior_lines >= 4:
        risk_score += 1
        risk_factors.append({"factor": f"≥4 prior lines ({prior_lines})", "score": 1, "impact": "moderate"})
    if ferritin > 700:
        risk_score += 1
        risk_factors.append({"factor": "Elevated ferritin", "score": 1, "impact": "moderate"})

    risk_level = "low" if risk_score <= 2 else "moderate" if risk_score <= 5 else "high" if risk_score <= 8 else "very_high"

    # ─── Treatment Simulation ───────────────────────────────────────────────
    base_orr = {"axi-cel": 0.83, "tisa-cel": 0.52, "liso-cel": 0.73, "brexu-cel": 0.87, "ide-cel": 0.73, "cilta-cel": 0.98}
    base_cr = {"axi-cel": 0.58, "tisa-cel": 0.40, "liso-cel": 0.53, "brexu-cel": 0.62, "ide-cel": 0.33, "cilta-cel": 0.83}

    orr = base_orr.get(product, 0.70)
    cr_rate = base_cr.get(product, 0.45)

    # Adjust for risk
    if tp53_mutated:
        orr *= 0.85; cr_rate *= 0.80
    if double_hit:
        orr *= 0.88; cr_rate *= 0.82
    if patient_age > 70:
        orr *= 0.92; cr_rate *= 0.88
    if ecog >= 2:
        orr *= 0.85; cr_rate *= 0.80
    if prior_lines > 4:
        orr *= 0.90; cr_rate *= 0.85

    # Patient-specific outcome
    r = rng.random()
    if r < cr_rate:
        predicted_response = "CR"
    elif r < orr:
        predicted_response = "PR"
    elif r < orr + 0.10:
        predicted_response = "SD"
    else:
        predicted_response = "PD"

    # PFS simulation
    base_pfs = {"CR": 18, "PR": 8, "SD": 4, "PD": 1.5}
    pfs_months = rng.gauss(base_pfs[predicted_response], base_pfs[predicted_response] * 0.3)
    pfs_months = max(0.5, pfs_months)

    # ─── Tumor Trajectory (12 months) ──────────────────────────────────────
    tumor_trajectory = []
    current_size = tumor_burden_mm
    for month in range(13):
        if month == 0:
            tumor_trajectory.append({"month": 0, "size_mm": round(current_size, 1), "change_pct": 0})
            continue

        if predicted_response == "CR":
            rate = -0.25 - rng.random() * 0.1
            if month > 3:
                rate = -0.05 * max(0, 1 - month / 8)
        elif predicted_response == "PR":
            rate = -0.15 - rng.random() * 0.05
            if month > 6:
                rate = 0.02 + rng.random() * 0.03
        elif predicted_response == "SD":
            rate = rng.gauss(0, 0.05)
        else:
            rate = 0.08 + rng.random() * 0.06

        current_size = max(0, current_size * (1 + rate))
        change = ((current_size - tumor_burden_mm) / tumor_burden_mm) * 100
        tumor_trajectory.append({
            "month": month,
            "size_mm": round(current_size, 1),
            "change_pct": round(change, 1),
        })

    # ─── CRS Kinetics Prediction ───────────────────────────────────────────
    crs_base = 0.08 if product in ("liso-cel",) else 0.17
    if tumor_burden_mm > 80:
        crs_base *= 1.4
    if patient_age > 65:
        crs_base *= 1.2

    crs_risk = min(0.95, crs_base + risk_score * 0.02)
    crs_grade = 0
    if rng.random() < crs_risk:
        if rng.random() < 0.25:
            crs_grade = 3 if rng.random() < 0.5 else 4
        elif rng.random() < 0.5:
            crs_grade = 2
        else:
            crs_grade = 1

    icans_base = 0.15 if product == "axi-cel" else 0.08
    icans_grade = 0
    if rng.random() < icans_base:
        icans_grade = rng.choices([1, 2, 3, 4], weights=[40, 30, 20, 10])[0]

    # CRS timeline (daily for 14 days)
    crs_timeline = []
    for day in range(15):
        if crs_grade == 0:
            temp = 37.0 + rng.random() * 0.3
            il6_level = max(0, rng.gauss(5, 2))
            grade = 0
        else:
            onset = 2 if product == "axi-cel" else 4
            peak = onset + 2
            if day < onset:
                temp = 37.0 + rng.random() * 0.3
                il6_level = max(0, rng.gauss(5, 3))
                grade = 0
            elif day <= peak + 1:
                severity = min(1, (day - onset) / max(1, peak - onset))
                temp = 37.0 + severity * (crs_grade * 0.5 + rng.random())
                il6_level = max(0, severity * crs_grade * 200 + rng.gauss(0, 30))
                grade = min(crs_grade, max(1, int(severity * crs_grade + 0.5)))
            else:
                recovery = max(0, 1 - (day - peak - 1) / 4)
                temp = 37.0 + recovery * rng.random() * 1.5
                il6_level = max(0, recovery * 50 + rng.gauss(0, 10))
                grade = max(0, int(recovery * crs_grade))

        crs_timeline.append({
            "day": day,
            "temperature_c": round(temp, 1),
            "il6_pg_ml": round(max(0, il6_level), 1),
            "crs_grade": grade,
        })

    # ─── Adverse Events ────────────────────────────────────────────────────
    adverse_events = {
        "crs": {"max_grade": crs_grade, "risk_pct": round(crs_risk * 100, 1), "onset_day": 2 if product == "axi-cel" else 4, "management": _crs_management(crs_grade)},
        "icans": {"max_grade": icans_grade, "risk_pct": round(icans_base * 100, 1), "onset_day": 5, "management": _icans_management(icans_grade)},
        "cytopenia": {"risk_pct": 85, "neutropenia_grade": rng.choices([2, 3, 4], weights=[20, 50, 30])[0], "recovery_day": rng.randint(21, 60)},
        "infections": {"risk_pct": round(min(50, 15 + risk_score * 3), 1), "prophylaxis": ["Acyclovir", "Fluconazole", "Sulfamethoxazole/Trimethoprim"]},
    }

    # ─── 12-month Timeline ─────────────────────────────────────────────────
    treatment_timeline = [
        {"day": -30, "event": "Screening & eligibility assessment", "type": "milestone"},
        {"day": -21, "event": "Leukapheresis", "type": "procedure"},
        {"day": -21, "event": "CAR-T manufacturing begins", "type": "milestone"},
    ]

    if prior_lines >= 3:
        treatment_timeline.append({"day": -14, "event": "Bridging therapy initiated", "type": "treatment"})

    treatment_timeline.extend([
        {"day": -5, "event": f"Lymphodepletion: Flu/Cy x3 days", "type": "treatment"},
        {"day": 0, "event": f"{product.upper()} infusion — Day 0", "type": "milestone"},
    ])

    if crs_grade >= 1:
        treatment_timeline.append({"day": crs_timeline[0]["day"] if crs_timeline else 2, "event": f"CRS onset (Grade {crs_grade})", "type": "adverse_event"})
    if crs_grade >= 2:
        treatment_timeline.append({"day": 3, "event": "Tocilizumab administered", "type": "treatment"})
    if crs_grade >= 3:
        treatment_timeline.append({"day": 4, "event": "ICU transfer", "type": "adverse_event"})
    if icans_grade >= 2:
        treatment_timeline.append({"day": 5, "event": f"ICANS Grade {icans_grade} — dexamethasone", "type": "adverse_event"})

    treatment_timeline.extend([
        {"day": 14, "event": "CRS resolved", "type": "resolution"},
        {"day": 28, "event": "Day 28 response assessment", "type": "assessment"},
        {"day": 90, "event": "Day 90 PET/CT", "type": "assessment"},
        {"day": 180, "event": "6-month follow-up", "type": "assessment"},
        {"day": 365, "event": "12-month follow-up", "type": "assessment"},
    ])

    treatment_timeline.sort(key=lambda x: x["day"])

    # ─── Estimated Cost (INR) ──────────────────────────────────────────────
    product_costs = {"axi-cel": 30000000, "tisa-cel": 28000000, "liso-cel": 32000000, "brexu-cel": 29000000, "ide-cel": 35000000, "cilta-cel": 38000000}
    drug_cost = product_costs.get(product, 30000000)
    hospital_cost = 1500000
    if crs_grade >= 3:
        hospital_cost += 1000000
    lab_cost = 500000
    supportive_cost = 300000
    total_cost = drug_cost + hospital_cost + lab_cost + supportive_cost

    cost_breakdown = {
        "car_t_product": {"amount": drug_cost, "formatted": f"₹{drug_cost / 10000000:.1f} Cr"},
        "hospitalization": {"amount": hospital_cost, "formatted": f"₹{hospital_cost / 100000:.1f} L"},
        "laboratory": {"amount": lab_cost, "formatted": f"₹{lab_cost / 100000:.1f} L"},
        "supportive_care": {"amount": supportive_cost, "formatted": f"₹{supportive_cost / 100000:.1f} L"},
        "total": {"amount": total_cost, "formatted": f"₹{total_cost / 10000000:.2f} Cr"},
    }

    # ─── Follow-up Schedule ────────────────────────────────────────────────
    followup_schedule = [
        {"timepoint": "Day 7", "assessments": ["CBC with differential", "CMP", "CRS biomarkers (IL-6, ferritin, CRP)", "Neurological assessment"]},
        {"timepoint": "Day 14", "assessments": ["CBC", "CMP", "B-cell aplasia check", "Flow cytometry for CAR-T persistence"]},
        {"timepoint": "Day 28", "assessments": ["PET/CT restaging", "Bone marrow biopsy (if applicable)", "Response assessment", "IgG levels"]},
        {"timepoint": "Day 90", "assessments": ["PET/CT", "Bone marrow biopsy", "MRD assessment", "IgG replacement if <400 mg/dL"]},
        {"timepoint": "Day 180", "assessments": ["PET/CT", "IgG levels", "Infection surveillance", "Neurocognitive evaluation"]},
        {"timepoint": "Month 12", "assessments": ["PET/CT", "Comprehensive labs", "IVIG assessment", "Late effects screening"]},
        {"timepoint": "Month 18", "assessments": ["PET/CT or CT", "Labs", "Vaccination readiness assessment"]},
        {"timepoint": "Month 24", "assessments": ["PET/CT", "Comprehensive review", "Secondary malignancy screening"]},
    ]

    # ─── Recommendations ───────────────────────────────────────────────────
    recommendations = []
    recommendations.append(f"Recommended product: {product.upper()} based on {cancer_type} disease characteristics")
    if risk_level in ("high", "very_high"):
        recommendations.append("High-risk patient — consider enhanced monitoring protocol")
        recommendations.append("Pre-emptive tocilizumab may be considered given CRS risk profile")
    if tp53_mutated:
        recommendations.append("TP53-mutated disease — discuss combination strategies and clinical trials")
    if double_hit:
        recommendations.append("Double-hit biology — consider bridging with R-EPOCH or polatuzumab-based regimen")
    if patient_age > 70:
        recommendations.append("Elderly patient — dose adjustment and close monitoring recommended")
    recommendations.append(f"Predicted response: {predicted_response} — estimated PFS: {pfs_months:.1f} months")

    return {
        "report_id": report_id,
        "report_type": "Clinical Simulation Report",
        "generated_at": generated_at.isoformat(),
        "patient_summary": {
            "age": patient_age,
            "sex": sex,
            "cancer_type": cancer_type,
            "stage": cancer_stage,
            "ecog": ecog,
            "prior_lines": prior_lines,
            "tumor_burden_mm": tumor_burden_mm,
            "tp53_mutated": tp53_mutated,
            "double_hit": double_hit,
        },
        "baseline_labs": {
            "ldh": round(ldh, 1), "ferritin": round(ferritin, 1),
            "crp": round(crp, 1), "il6": round(max(0, il6), 1),
            "alc": round(max(0.1, alc), 2), "platelets": round(max(10, platelets)),
            "hemoglobin": round(max(5, hemoglobin), 1), "wbc": round(max(0.5, wbc), 1),
            "creatinine": round(max(0.3, creatinine), 2), "albumin": round(max(2, albumin), 1),
        },
        "risk_assessment": {
            "overall_risk_score": risk_score,
            "risk_level": risk_level,
            "factors": risk_factors,
        },
        "treatment_simulation": {
            "product": product,
            "predicted_response": predicted_response,
            "orr_probability": round(orr * 100, 1),
            "cr_probability": round(cr_rate * 100, 1),
            "predicted_pfs_months": round(pfs_months, 1),
            "tumor_trajectory": tumor_trajectory,
        },
        "adverse_events": adverse_events,
        "crs_kinetics": crs_timeline,
        "treatment_timeline": treatment_timeline,
        "cost_estimate": cost_breakdown,
        "followup_schedule": followup_schedule,
        "recommendations": recommendations,
    }


def render_report_html(report_data: Dict[str, Any]) -> str:
    """Render a downloadable HTML report from report data."""
    ps = report_data["patient_summary"]
    ra = report_data["risk_assessment"]
    ts = report_data["treatment_simulation"]
    ae = report_data["adverse_events"]
    cost = report_data["cost_estimate"]

    risk_color = {"low": "#2ed573", "moderate": "#ffa502", "high": "#ff4757", "very_high": "#ff0000"}
    rc = risk_color.get(ra["risk_level"], "#aaa")

    # Tumor trajectory SVG
    traj = ts["tumor_trajectory"]
    max_size = max(t["size_mm"] for t in traj)
    svg_w, svg_h = 600, 200
    pad = 40
    traj_points = []
    for t in traj:
        x = pad + (t["month"] / 12) * (svg_w - 2 * pad)
        y = svg_h - pad - (t["size_mm"] / max(1, max_size)) * (svg_h - 2 * pad)
        traj_points.append(f"{x:.1f},{y:.1f}")
    traj_polyline = " ".join(traj_points)

    # Risk factors HTML
    rf_html = ""
    for f in ra["factors"]:
        ic = "#ff4757" if f["impact"] == "high" else "#ffa502"
        rf_html += f'<div style="display:flex;justify-content:space-between;padding:6px 10px;margin:4px 0;background:rgba(0,0,0,0.15);border-radius:6px;border-left:3px solid {ic}"><span>{f["factor"]}</span><span style="font-weight:700">+{f["score"]}</span></div>'

    # Timeline HTML
    tl_html = ""
    for ev in report_data["treatment_timeline"]:
        ec = {"milestone": "#6366f1", "procedure": "#3b82f6", "treatment": "#2ed573", "adverse_event": "#ff4757", "resolution": "#ffa502", "assessment": "#00d2ff"}.get(ev["type"], "#aaa")
        tl_html += f'<div style="display:flex;gap:12px;padding:6px 10px;border-left:3px solid {ec};margin:3px 0;border-radius:0 6px 6px 0;background:rgba(0,0,0,0.1)"><span style="min-width:60px;font-size:11px;font-weight:700;color:#94a3b8">Day {ev["day"]}</span><span>{ev["event"]}</span></div>'

    # Follow-up table
    fu_html = ""
    for fu in report_data["followup_schedule"]:
        assessments = "<br>".join(f"• {a}" for a in fu["assessments"])
        fu_html += f'<tr><td style="padding:8px;border-bottom:1px solid #333;font-weight:700;white-space:nowrap">{fu["timepoint"]}</td><td style="padding:8px;border-bottom:1px solid #333;font-size:12px">{assessments}</td></tr>'

    # Recommendations
    rec_html = "".join(f'<li style="margin:6px 0;line-height:1.5">{r}</li>' for r in report_data["recommendations"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CARVanta Clinical Report — {report_data['report_id']}</title>
<style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif; background:#0a0a1a; color:#e2e8f0; padding:20px; font-size:13px; }}
    .report {{ max-width:900px; margin:0 auto; }}
    .header {{ text-align:center; padding:30px 20px; border-bottom:2px solid #6366f1; margin-bottom:30px; }}
    .header h1 {{ font-size:28px; color:#f1f5f9; letter-spacing:-0.01em; }}
    .header .subtitle {{ color:#94a3b8; font-size:13px; margin-top:6px; }}
    .header .report-id {{ font-family:monospace; color:#6366f1; font-size:11px; margin-top:8px; }}
    .section {{ margin-bottom:28px; }}
    .section h2 {{ font-size:17px; color:#a5b4fc; margin-bottom:14px; padding-bottom:8px; border-bottom:1px solid rgba(148,163,184,0.1); }}
    .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
    .grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; }}
    .metric {{ background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.1); border-radius:10px; padding:14px; text-align:center; }}
    .metric .val {{ font-size:22px; font-weight:800; color:#f1f5f9; }}
    .metric .label {{ font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-top:4px; }}
    .risk-badge {{ display:inline-block; padding:4px 14px; border-radius:8px; font-weight:700; font-size:13px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th {{ text-align:left; padding:8px; font-size:11px; color:#94a3b8; text-transform:uppercase; border-bottom:1px solid #333; }}
    td {{ padding:8px; border-bottom:1px solid rgba(148,163,184,0.05); }}
    svg {{ width:100%; height:auto; }}
    .disclaimer {{ font-size:10px; color:#64748b; text-align:center; margin-top:30px; padding-top:16px; border-top:1px solid rgba(148,163,184,0.1); line-height:1.6; }}
    @media print {{ body {{ background:#fff; color:#111; }} .metric {{ border-color:#ddd; }} }}
</style>
</head>
<body>
<div class="report">
    <div class="header">
        <h1>🧬 CARVanta Clinical Simulation Report</h1>
        <div class="subtitle">Patient Digital Twin — CAR-T Therapy Simulation</div>
        <div class="report-id">Report ID: {report_data['report_id']} | Generated: {report_data['generated_at'][:10]}</div>
    </div>

    <div class="section">
        <h2>📋 Patient Summary</h2>
        <div class="grid-3">
            <div class="metric"><div class="val">{ps['age']}{ps['sex']}</div><div class="label">Age / Sex</div></div>
            <div class="metric"><div class="val">{ps['cancer_type']}</div><div class="label">Diagnosis</div></div>
            <div class="metric"><div class="val">Stage {ps['stage']}</div><div class="label">Stage</div></div>
            <div class="metric"><div class="val">ECOG {ps['ecog']}</div><div class="label">Performance</div></div>
            <div class="metric"><div class="val">{ps['prior_lines']}</div><div class="label">Prior Lines</div></div>
            <div class="metric"><div class="val">{ps['tumor_burden_mm']}mm</div><div class="label">Tumor Burden</div></div>
        </div>
    </div>

    <div class="section">
        <h2>⚠️ Risk Assessment</h2>
        <div style="text-align:center;margin-bottom:16px">
            <div class="metric" style="display:inline-block;min-width:200px">
                <div class="val" style="color:{rc}">{ra['risk_level'].upper()}</div>
                <div class="label">Overall Risk (Score: {ra['overall_risk_score']})</div>
            </div>
        </div>
        {rf_html}
    </div>

    <div class="section">
        <h2>📊 Treatment Simulation — {ts['product'].upper()}</h2>
        <div class="grid-3">
            <div class="metric"><div class="val" style="color:{'#2ed573' if ts['predicted_response'] in ('CR','PR') else '#ff4757'}">{ts['predicted_response']}</div><div class="label">Predicted Response</div></div>
            <div class="metric"><div class="val">{ts['orr_probability']}%</div><div class="label">ORR Probability</div></div>
            <div class="metric"><div class="val">{ts['predicted_pfs_months']}mo</div><div class="label">Est. PFS</div></div>
        </div>

        <h3 style="font-size:14px;color:#a5b4fc;margin:20px 0 10px">Tumor Regression Trajectory</h3>
        <svg viewBox="0 0 {svg_w} {svg_h}" style="background:rgba(15,23,42,0.3);border-radius:10px;padding:4px">
            <line x1="{pad}" y1="{pad}" x2="{pad}" y2="{svg_h-pad}" stroke="#555" stroke-width="1"/>
            <line x1="{pad}" y1="{svg_h-pad}" x2="{svg_w-pad}" y2="{svg_h-pad}" stroke="#555" stroke-width="1"/>
            <text x="{svg_w/2}" y="{svg_h-5}" text-anchor="middle" fill="#aaa" font-size="11">Months Post-Infusion</text>
            <text x="10" y="{svg_h/2}" text-anchor="middle" fill="#aaa" font-size="11" transform="rotate(-90 10 {svg_h/2})">Tumor Size (mm)</text>
            <polyline points="{traj_polyline}" fill="none" stroke="#00d2ff" stroke-width="2.5"/>
        </svg>
    </div>

    <div class="section">
        <h2>🌡️ Adverse Event Predictions</h2>
        <div class="grid-2">
            <div class="metric"><div class="val">Grade {ae['crs']['max_grade']}</div><div class="label">Max CRS Grade ({ae['crs']['risk_pct']}% risk)</div></div>
            <div class="metric"><div class="val">Grade {ae['icans']['max_grade']}</div><div class="label">Max ICANS Grade ({ae['icans']['risk_pct']}% risk)</div></div>
        </div>
        <p style="margin:10px 0;font-size:12px;color:#94a3b8"><strong>CRS Management:</strong> {ae['crs']['management']}</p>
        <p style="margin:4px 0;font-size:12px;color:#94a3b8"><strong>ICANS Management:</strong> {ae['icans']['management']}</p>
    </div>

    <div class="section">
        <h2>📅 Treatment Timeline</h2>
        {tl_html}
    </div>

    <div class="section">
        <h2>💰 Cost Estimate</h2>
        <div class="grid-2">
            <div class="metric"><div class="val">{cost['car_t_product']['formatted']}</div><div class="label">CAR-T Product</div></div>
            <div class="metric"><div class="val">{cost['hospitalization']['formatted']}</div><div class="label">Hospitalization</div></div>
        </div>
        <div class="metric" style="margin-top:12px"><div class="val" style="font-size:26px">{cost['total']['formatted']}</div><div class="label">Total Estimated Cost</div></div>
    </div>

    <div class="section">
        <h2>🏥 Follow-up Schedule</h2>
        <table>{fu_html}</table>
    </div>

    <div class="section">
        <h2>📌 Recommendations</h2>
        <ul style="padding-left:20px">{rec_html}</ul>
    </div>

    <div class="disclaimer">
        <strong>DISCLAIMER:</strong> This is a simulated report generated by CARVanta's Patient Digital Twin engine for educational and research purposes only.
        It is NOT a substitute for clinical judgment. All treatment decisions must be made by qualified healthcare professionals.
        <br>© CARVanta — AI-Augmented Biomarker Intelligence Platform v5
    </div>
</div>
</body>
</html>"""

    return html


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _crs_management(grade: int) -> str:
    """CRS management string by grade."""
    mgmt = {
        0: "No CRS expected — routine monitoring",
        1: "Grade 1 — supportive care, antipyretics, monitor vitals q4h",
        2: "Grade 2 — Tocilizumab 8mg/kg IV, consider ICU transfer if hypotension or hypoxia",
        3: "Grade 3 — Tocilizumab + dexamethasone 10mg IV q6h, ICU transfer, vasopressors PRN",
        4: "Grade 4 — Tocilizumab + methylprednisolone 2mg/kg, ICU with mechanical ventilation support",
    }
    return mgmt.get(min(grade, 4), mgmt[0])


def _icans_management(grade: int) -> str:
    """ICANS management string by grade."""
    mgmt = {
        0: "No ICANS expected — neuro checks q8h",
        1: "Grade 1 — neuro checks q4h, ICE assessment, consider thiamine",
        2: "Grade 2 — dexamethasone 10mg IV q6h, neuro checks q2h, seizure prophylaxis",
        3: "Grade 3 — dexamethasone 10mg IV q6h, ICU, methylprednisolone if refractory, EEG monitoring",
        4: "Grade 4 — methylprednisolone 1g/day x3d, ICU, intubation for airway protection if needed",
    }
    return mgmt.get(min(grade, 4), mgmt[0])
