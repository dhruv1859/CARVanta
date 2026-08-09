"""
ImmunoGate PDAC — API Router
Provides 3 endpoints for the ImmunoGate PDAC frontend module:
  POST /api/immunogate/datasets/biomarkers  — store biomarker data
  POST /api/immunogate/truth-table          — generate truth table
  POST /api/immunogate/generate-conclusion  — AI-generated conclusion
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Any
import re
import os

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False

router = APIRouter(prefix="/api/immunogate", tags=["ImmunoGate PDAC"])

# ── In-memory store for biomarkers (session-level) ──────────────────────────
_biomarker_store: List[dict] = []


# ── Pydantic Models ──────────────────────────────────────────────────────────

class BiomarkerItem(BaseModel):
    name: str
    category: str
    indication: str


class BiomarkersPayload(BaseModel):
    data: List[BiomarkerItem]


class MultiGateLogic(BaseModel):
    bestLogic: str
    logicName: Optional[str] = None
    rawExpression: Optional[str] = None
    description: Optional[str] = None
    specificity: float
    selectivity: float
    tumorCount: Optional[int] = None
    healthyCount: Optional[int] = None


class TruthTableRequest(BaseModel):
    logic: MultiGateLogic


class TruthTableEntry(BaseModel):
    combination: str
    tumorState: List[bool]
    healthyState: List[bool]
    carTActive: bool
    status: str
    offTarget: int
    cytokineToxicity: float
    riskLevel: str


class ConclusionRequest(BaseModel):
    selectedTumor: List[str]
    selectedHealthy: List[str]
    logic: MultiGateLogic
    truthTable: List[Any]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/datasets/biomarkers")
async def store_biomarkers(payload: BiomarkersPayload):
    """Store uploaded biomarker data in memory for the current session."""
    global _biomarker_store
    _biomarker_store = [b.dict() for b in payload.data]
    return {"status": "ok", "count": len(_biomarker_store)}


@router.post("/truth-table", response_model=List[TruthTableEntry])
async def generate_truth_table(request: TruthTableRequest):
    """
    Generate the full truth table for a given CAR-T logic gate expression.
    Uses boolean evaluation of the raw expression.
    """
    logic = request.logic
    expr = logic.rawExpression or logic.bestLogic

    # Determine which T/H variables appear in the expression
    t_vars = sorted(set(re.findall(r'T[1-5]', expr)))
    h_vars = sorted(set(re.findall(r'H[1-5]', expr)))

    if not t_vars:
        t_count = logic.tumorCount or 1
        t_vars = [f"T{i+1}" for i in range(t_count)]
    if not h_vars:
        h_count = logic.healthyCount or 0
        h_vars = [f"H{i+1}" for i in range(h_count)]

    t_count = len(t_vars)
    h_count = len(h_vars)
    total = 2 ** (t_count + h_count)
    table = []

    for i in range(total):
        bits = format(i, f'0{t_count + h_count}b')
        tumor_state = [b == '1' for b in bits[:t_count]]
        healthy_state = [b == '1' for b in bits[t_count:]]

        car_t_active = _evaluate_expression(expr, tumor_state, healthy_state)

        any_healthy = any(healthy_state)
        off_target = 1 if (car_t_active and any_healthy) else 0
        active_tumors = sum(tumor_state)
        cytokine_tox = (active_tumors / t_count) if (car_t_active and t_count > 0) else 0.0

        if off_target == 1:
            risk = "High"
        elif cytokine_tox >= 0.6:
            risk = "Moderate"
        else:
            risk = "Safe"

        table.append(TruthTableEntry(
            combination=bits,
            tumorState=tumor_state,
            healthyState=healthy_state,
            carTActive=car_t_active,
            status="Active/KILL" if car_t_active else "Inactive/OFF",
            offTarget=off_target,
            cytokineToxicity=round(cytokine_tox, 4),
            riskLevel=risk,
        ))

    return table


@router.post("/generate-conclusion")
async def generate_conclusion(request: ConclusionRequest):
    """
    Generate an AI-powered research conclusion using OpenAI.
    Falls back to a structured template if no API key is available.
    """
    tumor_antigens = request.selectedTumor
    healthy_antigens = request.selectedHealthy
    logic = request.logic
    truth_table = request.truthTable

    active_states = sum(1 for e in truth_table if e.get("carTActive", False))
    total_states = len(truth_table)
    safe_states = sum(1 for e in truth_table if e.get("riskLevel") == "Safe")

    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if _openai_available and openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            prompt = f"""You are an expert CAR-T cell therapy researcher specializing in Pancreatic Ductal Adenocarcinoma (PDAC).

Analyze the following CAR-T therapy configuration and provide a comprehensive research-grade conclusion:

SELECTED TUMOR ANTIGENS: {', '.join(tumor_antigens)}
HEALTHY ANTIGENS (VETO): {', '.join(healthy_antigens) if healthy_antigens else 'None'}
RECOMMENDED LOGIC: {logic.bestLogic}
LOGIC CONFIGURATION: {logic.logicName}
SPECIFICITY SCORE: {logic.specificity}/5
SELECTIVITY SCORE: {logic.selectivity}/5

TRUTH TABLE SUMMARY:
- Total Input Combinations: {total_states}
- CAR-T Active States: {active_states} ({round(active_states/total_states*100, 1) if total_states else 0}%)
- Safe States: {safe_states}

Provide a structured conclusion covering:
1. Therapeutic Rationale (why this logic gate configuration is appropriate for PDAC)
2. Safety Assessment (analysis of off-target risks based on healthy antigen veto gates)
3. Efficacy Prediction (expected tumor specificity and CAR-T activation probability)
4. Clinical Considerations (potential challenges and recommendations)
5. Research Recommendations (next steps for preclinical validation)

Use evidence-based language appropriate for a research publication."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7,
            )
            conclusion = response.choices[0].message.content
            return {"conclusion": conclusion}
        except Exception as e:
            # Fall through to template
            pass

    # Fallback template conclusion
    act_pct = round(active_states / total_states * 100, 1) if total_states else 0
    conclusion = f"""CAR-T Therapy Analysis Report — ImmunoGate PDAC

THERAPEUTIC CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━
Logic Gate: {logic.bestLogic}
Configuration: {logic.logicName or 'Custom'}
Specificity: {logic.specificity}/5  |  Selectivity: {logic.selectivity}/5

SELECTED BIOMARKERS
━━━━━━━━━━━━━━━━━━
Tumor Antigens: {', '.join(tumor_antigens)}
Healthy Veto Antigens: {', '.join(healthy_antigens) if healthy_antigens else 'None (single-target mode)'}

ACTIVATION ANALYSIS
━━━━━━━━━━━━━━━━━━
Total Logic States Evaluated: {total_states}
CAR-T Active States: {active_states} ({act_pct}% activation rate)
Safe States: {safe_states} ({round(safe_states/total_states*100, 1) if total_states else 0}%)

THERAPEUTIC RATIONALE
━━━━━━━━━━━━━━━━━━━━
The selected {'multi-gate' if len(tumor_antigens) > 1 else 'single-target'} logic configuration targets 
{len(tumor_antigens)} tumor-associated antigen(s) expressed in PDAC: {', '.join(tumor_antigens)}.
{'The NOT-gate veto mechanism using ' + ', '.join(healthy_antigens) + ' protects healthy tissue from off-target CAR-T activation.' if healthy_antigens else 'No healthy antigen veto gates are applied, representing a single-target approach.'}

SAFETY PROFILE
━━━━━━━━━━━━━
{'With ' + str(len(healthy_antigens)) + ' veto antigen(s), the system enforces selective CAR-T inhibition when healthy markers are present, reducing off-target toxicity risk significantly.' if healthy_antigens else 'Without veto gates, off-target toxicity risk depends entirely on the tumor specificity of the selected antigen(s). Careful preclinical evaluation is recommended.'}

RECOMMENDATIONS
━━━━━━━━━━━━━━
1. Validate antigen co-expression patterns in patient-derived PDAC organoids
2. Confirm healthy tissue expression profiles using TCGA and GTEx datasets
3. Conduct in vitro CAR-T cytotoxicity assays with the identified logic gate
4. Assess cytokine release syndrome potential in humanized mouse models
5. Consider IND application preparation based on favorable safety profile

NOTE: This conclusion was generated using the ImmunoGate PDAC template engine.
For AI-powered analysis, please configure the OPENAI_API_KEY environment variable."""

    return {"conclusion": conclusion}


# ── Helper: Boolean expression evaluator ────────────────────────────────────

def _evaluate_expression(expr: str, tumor_state: List[bool], healthy_state: List[bool]) -> bool:
    """Evaluate a CAR-T boolean gate expression against given antigen states."""
    e = expr

    # Substitute T and H variables with their boolean values
    for i, val in enumerate(tumor_state):
        e = re.sub(rf'\bT{i+1}\b', '1' if val else '0', e)
    for i, val in enumerate(healthy_state):
        e = re.sub(rf'\bH{i+1}\b', '1' if val else '0', e)

    # Iteratively resolve NOT(), AND, OR until fully reduced
    max_iter = 20
    for _ in range(max_iter):
        prev = e
        # NOT(1) → 0, NOT(0) → 1
        e = re.sub(r'NOT\(1\)', '0', e)
        e = re.sub(r'NOT\(0\)', '1', e)
        # Remove redundant parentheses around single digits
        e = re.sub(r'\(([01])\)', r'\1', e)
        # AND gates
        e = re.sub(r'([01]) AND ([01])', lambda m: '1' if m.group(1) == '1' and m.group(2) == '1' else '0', e)
        # OR gates
        e = re.sub(r'([01]) OR ([01])', lambda m: '1' if m.group(1) == '1' or m.group(2) == '1' else '0', e)
        if e == prev:
            break

    return e.strip() == '1'
