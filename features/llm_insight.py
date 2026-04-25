"""
CARVanta – LLM-Powered AI Insight Generator
=============================================
Calls an LLM (Grok / Groq / Gemini / OpenAI / DeepSeek) to produce
unique, natural-language insights for every module.

Priority: Grok (xAI) → Groq → DeepSeek → Gemini → OpenAI

Set one of these in your .env:
    XAI_API_KEY=your-grok-key       (xAI Grok)
    GROQ_API_KEY=your-groq-key      (Groq — free tier)
    DEEPSEEK_API_KEY=your-key
    GEMINI_API_KEY=your-key
    OPENAI_API_KEY=your-key
"""

import os
import json
import time
import hashlib
from typing import Optional

# Load .env so API keys are available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import httpx/requests for API calls
try:
    import httpx
    _HTTP = "httpx"
except ImportError:
    try:
        import requests as _requests_lib
        _HTTP = "requests"
    except ImportError:
        _HTTP = None

# ─── Config ──────────────────────────────────────────────────────────────────
XAI_KEY = os.getenv("XAI_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

XAI_URL = "https://api.x.ai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ─── Cache to avoid duplicate calls within same session ──────────────────────
_cache: dict = {}
_CACHE_TTL = 300  # 5 min


def _cache_key(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()


# ─── System prompt ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are CARVanta's AI advisor — an expert in CAR-T cell therapy, 
immuno-oncology, and antigen target discovery. You analyze scoring data from 
CARVanta's computational pipeline and provide clinically-relevant insights.

Rules:
- Be concise (3-5 sentences max)
- Always reference specific numbers from the data
- Provide actionable clinical recommendations
- Use bold (**text**) for key findings
- Sound like a knowledgeable scientist, not a template
- Each response should feel unique and thoughtful
- Mention specific biological mechanisms when relevant
- If scores are contradictory, explain why that might happen
"""


# ═════════════════════════════════════════════════════════════════════════════
# LLM Provider Callers
# ═════════════════════════════════════════════════════════════════════════════

def _call_openai_compatible(url: str, key: str, model: str, prompt: str,
                            system: str = SYSTEM_PROMPT, max_tokens: int = 400,
                            temperature: float = 0.8, timeout: int = 15) -> Optional[str]:
    """Generic caller for OpenAI-compatible APIs (Grok, Groq, DeepSeek, OpenAI)."""
    if not key or not _HTTP:
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    try:
        if _HTTP == "httpx":
            r = httpx.post(url, json=payload, headers=headers, timeout=timeout)
            data = r.json()
        else:
            r = _requests_lib.post(url, json=payload, headers=headers, timeout=timeout)
            data = r.json()

        if "error" in data:
            print(f"[CARVanta] API error ({model}): {data['error']}")
            return None

        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[CARVanta] API error ({model}): {e}")
        return None


def _call_grok(prompt: str, system: str = SYSTEM_PROMPT) -> Optional[str]:
    """Call xAI Grok API."""
    return _call_openai_compatible(XAI_URL, XAI_KEY, "grok-3-mini", prompt, system)


def _call_groq(prompt: str, system: str = SYSTEM_PROMPT) -> Optional[str]:
    """Call Groq API (free tier, uses Llama 3.3 70B)."""
    return _call_openai_compatible(GROQ_URL, GROQ_KEY, "llama-3.3-70b-versatile", prompt, system)


def _call_deepseek(prompt: str, system: str = SYSTEM_PROMPT) -> Optional[str]:
    """Call DeepSeek API."""
    return _call_openai_compatible(DEEPSEEK_URL, DEEPSEEK_KEY, "deepseek-chat", prompt, system)


def _call_openai(prompt: str, system: str = SYSTEM_PROMPT) -> Optional[str]:
    """Call OpenAI API."""
    return _call_openai_compatible(OPENAI_URL, OPENAI_KEY, "gpt-4o-mini", prompt, system)


def _call_gemini(prompt: str, system: str = SYSTEM_PROMPT) -> Optional[str]:
    """Call Gemini API."""
    if not GEMINI_KEY or not _HTTP:
        return None

    url = f"{GEMINI_URL}?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"{system}\n\n{prompt}"}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 400},
    }

    try:
        if _HTTP == "httpx":
            r = httpx.post(url, json=payload, timeout=10)
            data = r.json()
        else:
            r = _requests_lib.post(url, json=payload, timeout=10)
            data = r.json()

        if "error" in data:
            print(f"[CARVanta] Gemini error: {data['error'].get('message', '')}")
            return None

        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"[CARVanta] Gemini error: {e}")
        return None


# ═════════════════════════════════════════════════════════════════════════════
# Main Dispatcher — Tries providers in priority order with caching
# ═════════════════════════════════════════════════════════════════════════════

def call_llm(prompt: str, system: str = SYSTEM_PROMPT,
             max_tokens: int = 400) -> Optional[str]:
    """Try Grok → Groq → DeepSeek → Gemini → OpenAI. Cached for 5 min."""
    key = _cache_key(prompt)
    cached = _cache.get(key)
    if cached and time.time() - cached["ts"] < _CACHE_TTL:
        return cached["text"]

    result = None

    if XAI_KEY:
        result = _call_grok(prompt, system)

    if not result and GROQ_KEY:
        result = _call_groq(prompt, system)

    if not result and DEEPSEEK_KEY:
        result = _call_deepseek(prompt, system)

    if not result and GEMINI_KEY:
        result = _call_gemini(prompt, system)

    if not result and OPENAI_KEY:
        result = _call_openai(prompt, system)

    if result:
        _cache[key] = {"text": result, "ts": time.time()}

    return result


def is_llm_available() -> bool:
    """Check if any LLM API is configured."""
    return bool(XAI_KEY or GROQ_KEY or DEEPSEEK_KEY or GEMINI_KEY or OPENAI_KEY) and _HTTP is not None


# ═════════════════════════════════════════════════════════════════════════════
# Prompt Builders — Convert CARVanta data into LLM prompts
# ═════════════════════════════════════════════════════════════════════════════

def generate_scoring_insight(antigen: str, cvs: float, tier: str,
                              features: dict, ml_score: float = 0,
                              confidence: str = "") -> Optional[str]:
    """Generate AI insight for single antigen scoring."""
    prompt = f"""Analyze this CAR-T antigen target evaluation:

Antigen: {antigen}
CVS Score: {cvs:.3f} (CARVanta Viability Score, 0-1 scale)
Tier: {tier}
ML Score: {ml_score:.3f}
Confidence: {confidence}

Feature Breakdown:
- Tumor Specificity: {features.get('tumor_specificity', 'N/A')}
- Normal Tissue Risk: {features.get('normal_expression_risk', 'N/A')}
- Safety Margin: {features.get('safety_margin', 'N/A')}
- Expression Stability: {features.get('stability_score', 'N/A')}
- Literature Evidence: {features.get('literature_support', 'N/A')}
- Immunogenicity: {features.get('immunogenicity_score', 'N/A')}
- Surface Accessibility: {features.get('surface_accessibility', 'N/A')}

Provide a unique clinical insight about this antigen as a CAR-T target.
Focus on what makes this result interesting and what a researcher should do next."""

    return call_llm(prompt)


def generate_synergy_llm_insight(synergy_data: dict) -> Optional[str]:
    """Generate AI insight for multi-target synergy."""
    antigens = synergy_data.get("antigens", [])
    indiv = synergy_data.get("individual_scores", {})

    indiv_text = "\n".join([
        f"  - {name}: CVS={s.get('CVS', 0):.3f}, Tier={s.get('tier', '?')}"
        for name, s in indiv.items()
    ])

    prompt = f"""Analyze this multi-antigen CAR-T combination:

Combination: {' + '.join(antigens)}
Synergy Score: {synergy_data.get('synergy_score', 0):.3f}
Complementarity: {synergy_data.get('complementarity', 0):.3f}
Coverage: {synergy_data.get('combined_coverage', 0):.3f}
Escape Risk Reduction: {synergy_data.get('escape_risk_reduction', 0):.3f}

Individual Scores:
{indiv_text}

Provide a unique insight about this combination's therapeutic potential.
Should this be pursued as a dual-target or tandem CAR-T? What are the risks?"""

    return call_llm(prompt)


def generate_safety_llm_insight(toxicity_data: dict) -> Optional[str]:
    """Generate AI insight for tissue risk heatmap."""
    risk_map = toxicity_data.get("tissue_risk_map", {})
    alerts = toxicity_data.get("critical_organ_alerts", [])

    top_risks = sorted(
        [(organ, d["risk_score"]) for organ, d in risk_map.items()],
        key=lambda x: x[1], reverse=True
    )[:5]

    risk_text = "\n".join([f"  - {organ}: risk={score:.3f}" for organ, score in top_risks])
    alert_text = ", ".join([a.get("organ", "") for a in alerts]) if alerts else "None"

    prompt = f"""Analyze this CAR-T safety/toxicity profile:

Antigen: {toxicity_data.get('antigen', '?')}
Aggregate Toxicity: {toxicity_data.get('aggregate_toxicity_index', 0):.3f}
Critical Organ Alerts: {alert_text}

Top 5 Risk Organs:
{risk_text}

Provide a safety assessment. What off-tumor toxicity risks exist?
What safety engineering (kill switches, affinity tuning) would you recommend?"""

    return call_llm(prompt)


def generate_stratification_llm_insight(strat_data: dict) -> Optional[str]:
    """Generate AI insight for patient stratification."""
    subtypes = strat_data.get("subtype_analysis", [])
    subtype_text = "\n".join([
        f"  - {s['subtype']}: benefit={s.get('predicted_benefit', 0):.3f}, share={s.get('population_share', '?')}"
        for s in subtypes[:3]
    ]) if subtypes else "No subtype data"

    prompt = f"""Analyze this patient stratification for CAR-T therapy:

Antigen: {strat_data.get('antigen', '?')}
Cancer Type: {strat_data.get('cancer_type', '?')}
Estimated Eligibility: {strat_data.get('estimated_eligibility_pct', 0):.0f}%

Top Responding Subtypes:
{subtype_text}

Who should receive this therapy? Which patients benefit most?
What biomarkers should guide patient selection?"""

    return call_llm(prompt)


# ═════════════════════════════════════════════════════════════════════════════
# NEW: Extended Prompt Builders for All Modules
# ═════════════════════════════════════════════════════════════════════════════

def generate_digital_twin_insight(patient_data: dict, simulation: dict) -> Optional[str]:
    """Generate AI insight for Digital Twin simulation results."""
    prompt = f"""Analyze this CAR-T Digital Twin patient simulation:

Patient Profile:
- Age: {patient_data.get('age', '?')}, Weight: {patient_data.get('weight', '?')}kg
- Cancer: {patient_data.get('cancer_type', '?')}
- ECOG: {patient_data.get('ecog', '?')}, Prior Lines: {patient_data.get('prior_lines', '?')}
- Target Antigen: {patient_data.get('target_antigen', '?')}

Simulation Results:
- CRS Risk: {simulation.get('crs_risk', '?')}
- ICANS Risk: {simulation.get('icans_risk', '?')}
- Predicted Response: {simulation.get('predicted_response', '?')}
- Overall Survival (12m): {simulation.get('os_12m', '?')}
- CAR-T Expansion Peak: Day {simulation.get('expansion_peak_day', '?')}

Interpret these results for a clinician. What does this simulation suggest 
about treatment approach, monitoring schedule, and risk mitigation?"""

    return call_llm(prompt)


def generate_genomic_insight(genomic_data: dict) -> Optional[str]:
    """Generate AI insight for genomic profiler results."""
    mutations = genomic_data.get("mutations", [])
    mut_text = ", ".join([f"{m.get('gene', '?')} ({m.get('type', '?')})" for m in mutations[:5]]) if mutations else "None detected"

    prompt = f"""Analyze this genomic profiling result for CAR-T therapy planning:

Patient Genomic Profile:
- TMB: {genomic_data.get('tmb', '?')} mut/Mb
- MSI Status: {genomic_data.get('msi_status', '?')}
- Key Mutations: {mut_text}
- HLA Type: {genomic_data.get('hla_type', '?')}
- PD-L1 Expression: {genomic_data.get('pdl1', '?')}

How do these genomic features impact CAR-T therapy selection?
What resistance mechanisms should be monitored?
Suggest any combination strategies based on this profile."""

    return call_llm(prompt)


def generate_trial_insight(trial_data: dict) -> Optional[str]:
    """Generate AI insight for clinical trial matching."""
    prompt = f"""Analyze this clinical trial match for a CAR-T patient:

Trial: {trial_data.get('title', '?')}
Phase: {trial_data.get('phase', '?')}
Sponsor: {trial_data.get('sponsor', '?')}
Target: {trial_data.get('target_antigen', '?')}
Cancer Type: {trial_data.get('cancer_type', '?')}
Match Score: {trial_data.get('match_score', '?')}%
Location: {trial_data.get('location', '?')}
Status: {trial_data.get('status', '?')}

Eligibility Criteria Met: {trial_data.get('criteria_met', '?')}/{trial_data.get('criteria_total', '?')}

Provide clinical advice: Is this trial a good fit? What are the key considerations?
What questions should the patient/oncologist ask before enrolling?"""

    return call_llm(prompt)


def generate_drug_discovery_insight(pipeline_data: dict) -> Optional[str]:
    """Generate AI insight for drug discovery pipeline analysis."""
    prompt = f"""Analyze this CAR-T drug discovery pipeline result:

Target: {pipeline_data.get('target', '?')}
CAR Design: {pipeline_data.get('car_design', '?')}
ScFv Affinity (Kd): {pipeline_data.get('scfv_affinity', '?')} nM
Epitope: {pipeline_data.get('epitope', '?')}
Manufacturing Score: {pipeline_data.get('manufacturing_score', '?')}
Safety Switch: {pipeline_data.get('safety_switch', '?')}
Predicted Efficacy: {pipeline_data.get('efficacy_score', '?')}

Evaluate this CAR-T construct design. What are the strengths and weaknesses?
Suggest optimizations for the scFv, costimulatory domain, or safety features."""

    return call_llm(prompt)


def generate_disease_atlas_insight(disease_data: dict) -> Optional[str]:
    """Generate AI insight for disease atlas queries."""
    targets = disease_data.get("targets", [])
    target_text = ", ".join([f"{t.get('name', '?')} (CVS: {t.get('cvs', 0):.2f})" for t in targets[:5]]) if targets else "None"

    prompt = f"""Analyze this disease profile from CARVanta's Disease Atlas:

Disease: {disease_data.get('disease', '?')}
Category: {disease_data.get('category', '?')}
Incidence: {disease_data.get('incidence', '?')}/100k
Current Standard of Care: {disease_data.get('standard_of_care', '?')}
Top CAR-T Targets: {target_text}
Approved CAR-T Therapies: {disease_data.get('approved_therapies', 'None')}

Provide a comprehensive overview of the CAR-T therapy landscape for this disease.
What are the most promising targets and why? What challenges remain?"""

    return call_llm(prompt)


def generate_adverse_event_insight(ae_data: dict) -> Optional[str]:
    """Generate AI insight for adverse event analysis."""
    events = ae_data.get("events", [])
    event_text = "\n".join([
        f"  - {e.get('event', '?')}: Grade {e.get('grade', '?')}, Freq: {e.get('frequency', '?')}%"
        for e in events[:5]
    ]) if events else "No events"

    prompt = f"""Analyze this adverse event profile for CAR-T therapy:

Product: {ae_data.get('product', '?')}
Target: {ae_data.get('target', '?')}
Total Patients: {ae_data.get('total_patients', '?')}

Top Adverse Events:
{event_text}

CRS Rate (≥Grade 3): {ae_data.get('crs_severe_rate', '?')}%
ICANS Rate (≥Grade 3): {ae_data.get('icans_severe_rate', '?')}%

Provide a safety assessment. How does this compare to other CAR-T products?
What monitoring and management strategies should be implemented?"""

    return call_llm(prompt)


def generate_copilot_response(user_message: str, context: str = "") -> Optional[str]:
    """General-purpose research copilot chat response."""
    system = """You are CARVanta's AI Research Copilot — an expert in CAR-T cell therapy,
immuno-oncology, genomics, and drug discovery. You help researchers by:
- Answering scientific questions about CAR-T therapy
- Explaining biological mechanisms
- Interpreting experimental data
- Suggesting research directions
- Reviewing literature findings

Be thorough but concise. Use markdown formatting. Cite mechanisms and pathways.
If the question is outside your expertise, say so honestly."""

    prompt = user_message
    if context:
        prompt = f"Context:\n{context}\n\nUser Question:\n{user_message}"

    return call_llm(prompt, system=system, max_tokens=600)


def generate_ranking_insight(top_antigens: list) -> Optional[str]:
    """Generate AI insight for the global antigen ranking/leaderboard."""
    top5 = top_antigens[:5]
    ranking_text = "\n".join([
        f"  #{i+1} {a.get('antigen', '?')} ({a.get('cancer_type', '?')}): CVS={a.get('CVS', 0):.3f}, Tier={a.get('tier', '?')}"
        for i, a in enumerate(top5)
    ])

    prompt = f"""Analyze CARVanta's global CAR-T target leaderboard:

Top 5 Targets:
{ranking_text}

Total targets evaluated: {len(top_antigens)}

What patterns emerge from these rankings? Which targets should pharmaceutical
companies prioritize and why? Are there any surprising entries?"""

    return call_llm(prompt)


def generate_multi_omics_insight(omics_data: dict) -> Optional[str]:
    """Generate AI insight for multi-omics integration results."""
    prompt = f"""Analyze this multi-omics integration for CAR-T research:

Target: {omics_data.get('target', '?')}
Transcriptomics Score: {omics_data.get('transcriptomics_score', '?')}
Proteomics Score: {omics_data.get('proteomics_score', '?')}
Epigenomics Score: {omics_data.get('epigenomics_score', '?')}
Metabolomics Score: {omics_data.get('metabolomics_score', '?')}
Integration Confidence: {omics_data.get('confidence', '?')}

How do these multi-omics layers support or challenge target viability?
What additional experiments would strengthen the evidence?"""

    return call_llm(prompt)
