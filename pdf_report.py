"""
CARVanta – PDF Report Generator v1
=====================================
CARVanta-Original: Professional PDF report generation for antigen analyses.

Generates a comprehensive PDF containing:
  - CVS score and breakdown
  - Safety profile and Tissue Risk Heatmap
  - ML prediction and feature importance
  - AI-generated insights and recommendations

Uses built-in HTML-to-text approach for maximum compatibility
(no heavy dependencies like reportlab required).

Usage:
    from api.pdf_report import generate_antigen_pdf
    pdf_bytes = generate_antigen_pdf("CD19")
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def _format_bar(value: float, width: int = 30) -> str:
    """Create a text-based bar chart segment."""
    filled = int(value * width)
    return "█" * filled + "░" * (width - filled)


def _format_risk_indicator(risk_class: str) -> str:
    """Format risk level indicator."""
    indicators = {
        "NEGLIGIBLE": "● LOW",
        "LOW":        "● LOW",
        "MODERATE":   "◐ MODERATE",
        "HIGH":       "◉ HIGH",
        "CRITICAL":   "◉ CRITICAL",
    }
    return indicators.get(risk_class, "○ UNKNOWN")


def generate_antigen_report_text(antigen_name: str) -> str:
    """
    Generate a comprehensive text report for an antigen.

    Returns a formatted string suitable for conversion to PDF or display.
    """
    from features.tumor_features import generate_features
    from scoring.cvs_engine import compute_cvs
    from features.safety_features import (
        compute_safety_profile,
        compute_therapeutic_index,
        predict_off_tumor_toxicity,
    )
    from models.predict import predict_viability, predict_ranking_score
    from features.ai_reasoning import generate_ai_insight, generate_deep_insight

    antigen = antigen_name.upper()
    features = generate_features(antigen)
    cvs_result = compute_cvs(features)
    safety = compute_safety_profile(features)
    ml = predict_viability(features)
    ml_ranking = predict_ranking_score(features)
    toxicity = predict_off_tumor_toxicity(antigen)

    # Therapeutic index
    tumor_expr = features.get("raw_tumor_expression", 5.0)
    normal_expr = features.get("raw_normal_expression", 3.0)
    ti = compute_therapeutic_index(tumor_expr, normal_expr)

    # AI insights
    ai_insight = generate_ai_insight(cvs_result["CVS"], ml["prediction"], ml["confidence"])
    deep_insight = generate_deep_insight(cvs_result["CVS"], ml["prediction"], ml.get("contributions", {}))

    # Adaptive score
    adaptive_score = round(0.60 * cvs_result["CVS"] + 0.40 * ml_ranking, 3)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    breakdown = cvs_result["breakdown"]

    # -- Build report --
    lines = []
    lines.append("=" * 70)
    lines.append(f"  CARVanta -- Antigen Viability Report")
    lines.append(f"  AI-Powered CAR-T Target Analysis")
    lines.append("=" * 70)
    lines.append(f"  Antigen:         {antigen}")
    lines.append(f"  Generated:       {now}")
    lines.append(f"  CVS Engine:      v4 (Adaptive ML-Driven Scoring)")
    lines.append(f"  Adaptive Score:  {adaptive_score}")
    lines.append(f"  ML Ranking:      {ml_ranking:.3f}")
    lines.append("")

    # ── Section 1: CVS Score ────────────────────────────────────────────────
    lines.append("─" * 70)
    lines.append("  1. CAR-T VIABILITY SCORE (CVS)")
    lines.append("─" * 70)
    lines.append(f"  CVS Score:     {cvs_result['CVS']:.3f}")
    lines.append(f"  Tier:          {cvs_result['tier']}")
    lines.append(f"  Confidence:    {cvs_result['confidence']:.3f}")
    lines.append("")
    lines.append("  Feature Breakdown:")
    for feature, value in breakdown.items():
        bar = _format_bar(value, 25)
        lines.append(f"    {feature:<25} {value:.3f}  {bar}")
    lines.append("")

    # ── Section 2: Safety Profile ───────────────────────────────────────────
    lines.append("─" * 70)
    lines.append("  2. SAFETY & TOXICITY PROFILE")
    lines.append("─" * 70)
    lines.append(f"  Risk Level:        {safety['risk_level']}")
    lines.append(f"  Safety Margin:     {safety['safety_margin']:.3f}")
    lines.append(f"  Therapeutic Index: {ti['therapeutic_index']:.2f} ({ti['window_label']})")
    lines.append(f"  Surface Access:    {'Yes' if safety['surface_accessible'] else 'No'}")
    lines.append(f"  Immunogenic:       {'Yes' if safety['immunogenic'] else 'No'}")
    lines.append("")
    if safety["toxicity_flags"]:
        lines.append("  Toxicity Flags:")
        for flag in safety["toxicity_flags"]:
            lines.append(f"    ⚠ {flag}")
    else:
        lines.append("  ✓ No toxicity flags identified")
    lines.append("")

    # ── Section 3: Tissue Risk Heatmap ──────────────────────────────────────
    lines.append("─" * 70)
    lines.append("  3. TISSUE RISK HEATMAP (Off-Tumor Toxicity)")
    lines.append("─" * 70)
    lines.append(f"  Aggregate Toxicity Index: {toxicity['aggregate_toxicity_index']:.3f}")
    lines.append(f"  Data Source: {toxicity['data_source']}")
    lines.append("")
    lines.append(f"  {'Organ':<20} {'TPM':>8} {'Risk':>8}  {'Level':<12}")
    lines.append(f"  {'─'*20} {'─'*8} {'─'*8}  {'─'*12}")
    for organ, data in toxicity["tissue_risk_map"].items():
        critical_marker = " ⚠" if data["is_critical"] and data["risk_class"] in ("HIGH", "MODERATE") else ""
        lines.append(
            f"  {organ:<20} {data['estimated_tpm']:>8.2f} {data['risk_score']:>8.3f}  "
            f"{_format_risk_indicator(data['risk_class'])}{critical_marker}"
        )
    lines.append("")

    if toxicity["critical_organ_alerts"]:
        lines.append("  ⚠ CRITICAL ORGAN ALERTS:")
        for alert in toxicity["critical_organ_alerts"]:
            lines.append(f"    {alert['severity']}: {alert['message']}")
        lines.append("")

    lines.append(f"  Safety Recommendation:")
    lines.append(f"    {toxicity['safety_recommendation']}")
    lines.append("")

    # ── Section 4: ML Prediction ────────────────────────────────────────────
    lines.append("─" * 70)
    lines.append("  4. ML MODEL PREDICTION")
    lines.append("─" * 70)
    lines.append(f"  Prediction:  {'VIABLE' if ml['prediction'] == 1 else 'NON-VIABLE'}")
    lines.append(f"  Confidence:  {ml['confidence']:.3f} ({ml['confidence_label']})")
    lines.append("")

    if ml.get("importance"):
        lines.append("  Feature Importance:")
        sorted_imp = sorted(ml["importance"].items(), key=lambda x: x[1], reverse=True)
        for feat, imp in sorted_imp:
            bar = _format_bar(imp / max(v for v in ml["importance"].values()), 20) if max(ml["importance"].values()) > 0 else ""
            lines.append(f"    {feat:<25} {imp:.4f}  {bar}")
    lines.append("")

    # ── Section 5: AI Insights ──────────────────────────────────────────────
    lines.append("─" * 70)
    lines.append("  5. AI-GENERATED INSIGHTS")
    lines.append("─" * 70)
    lines.append(f"  Quick Insight: {ai_insight}")
    lines.append(f"")
    lines.append(f"  Deep Analysis: {deep_insight}")
    lines.append("")

    # ── Footer ──────────────────────────────────────────────────────────────
    lines.append("=" * 70)
    lines.append("  Generated by CARVanta — AI-Powered CAR-T Target Discovery")
    lines.append("  This report is for research purposes only.")
    lines.append("  © CARVanta — carvanta.ai")
    lines.append("=" * 70)

    return "\n".join(lines)


def generate_antigen_pdf(antigen_name: str) -> bytes:
    """
    Generate a PDF report for an antigen.

    Uses reportlab to create a proper PDF document.
    Falls back to a minimal valid PDF if reportlab is unavailable.

    Returns
    -------
    bytes : valid PDF content
    """
    text_report = generate_antigen_report_text(antigen_name)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from io import BytesIO

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, height - 40, "CARVanta -- Antigen Viability Report")
        c.setFont("Helvetica", 10)
        c.drawString(30, height - 55, f"AI-Powered CAR-T Target Analysis  |  v4 Adaptive ML-Driven")

        # Body text
        y = height - 80
        c.setFont("Courier", 7)
        for line in text_report.split("\n"):
            if y < 40:
                c.showPage()
                y = height - 40
                c.setFont("Courier", 7)
            # Replace Unicode that Courier can't render
            safe_line = (
                line.replace("\u2588", "#")
                    .replace("\u2591", ".")
                    .replace("\u2500", "-")
                    .replace("\u25cf", "*")
                    .replace("\u25d0", "~")
                    .replace("\u25c9", "!")
                    .replace("\u25cb", "o")
                    .replace("\u2713", "[OK]")
                    .replace("\u26a0", "[!]")
                    .replace("\u2014", "--")
                    .replace("\u2022", "*")
                    .encode("ascii", "replace").decode("ascii")
            )
            c.drawString(30, y, safe_line[:110])
            y -= 10

        c.save()
        return buffer.getvalue()

    except ImportError:
        # Fallback: build a minimal valid PDF manually
        # This creates a proper PDF 1.4 document
        safe_text = (
            text_report
                .replace("\u2588", "#")
                .replace("\u2591", ".")
                .replace("\u2500", "-")
                .encode("ascii", "replace").decode("ascii")
        )
        # Use a very simple PDF structure
        pdf_lines = [
            "%PDF-1.4",
            "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
            "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj",
            "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj",
            "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Courier>>endobj",
        ]
        # Build content stream
        content_lines = ["BT", "/F1 7 Tf", "30 750 Td", "10 TL"]
        for line in safe_text.split("\n")[:90]:  # Fit first page
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:100]
            content_lines.append(f"({escaped}) '")
        content_lines.append("ET")
        content_stream = "\n".join(content_lines)

        pdf_lines.append(f"4 0 obj<</Length {len(content_stream)}>>stream\n{content_stream}\nendstream\nendobj")

        xref_offset = sum(len(l) + 1 for l in pdf_lines)
        pdf_lines.append(f"xref\n0 6\n0000000000 65535 f \n")
        offset = len("%PDF-1.4\n")
        for i in range(1, 6):
            pdf_lines.append(f"{offset:010d} 00000 n ")
            offset += len(pdf_lines[i]) + 1

        pdf_lines.append(f"trailer<</Size 6/Root 1 0 R>>")
        pdf_lines.append(f"startxref\n{xref_offset}")
        pdf_lines.append("%%EOF")

        return "\n".join(pdf_lines).encode("ascii")


if __name__ == "__main__":
    # Test report generation
    antigen = "CD19"
    if len(sys.argv) > 1:
        antigen = sys.argv[1]

    print(generate_antigen_report_text(antigen))
