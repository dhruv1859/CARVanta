"""
CARVanta – LLM-Powered AI Insight Generator
=============================================
Calls an LLM (Gemini / OpenAI) to produce unique, natural-language
insights for every antigen evaluation. Falls back to rule-based
reasoning if no API key is configured.

Set one of these in your .env:
    GEMINI_API_KEY=your-key-here
    OPENAI_API_KEY=your-key-here
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
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

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


def _call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini API."""
    if not GEMINI_KEY or not _HTTP:
        return None
    
    url = f"{GEMINI_URL}?key={GEMINI_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]
        }],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 300,
        }
    }
    
    try:
        if _HTTP == "httpx":
            r = httpx.post(url, json=payload, timeout=10)
            data = r.json()
        else:
            r = _requests_lib.post(url, json=payload, timeout=10)
            data = r.json()
        
        if "error" in data:
            print(f"[CARVanta] Gemini API error: {data['error'].get('message', '')}")
            return None
        
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"[CARVanta] Gemini API error: {e}")
        return None


def _call_openai(prompt: str) -> Optional[str]:
    """Call OpenAI API."""
    if not OPENAI_KEY or not _HTTP:
        return None
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 300,
    }
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    
    try:
        if _HTTP == "httpx":
            r = httpx.post(OPENAI_URL, json=payload, headers=headers, timeout=10)
            data = r.json()
        else:
            r = _requests_lib.post(OPENAI_URL, json=payload, headers=headers, timeout=10)
            data = r.json()
        
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[CARVanta] OpenAI API error: {e}")
        return None


def _call_deepseek(prompt: str) -> Optional[str]:
    """Call DeepSeek API (OpenAI-compatible)."""
    if not DEEPSEEK_KEY or not _HTTP:
        return None
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 300,
    }
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    
    try:
        if _HTTP == "httpx":
            r = httpx.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=15)
            data = r.json()
        else:
            r = _requests_lib.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=15)
            data = r.json()
        
        if "error" in data:
            print(f"[CARVanta] DeepSeek API error: {data['error'].get('message', data['error'])}")
            return None
        
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[CARVanta] DeepSeek API error: {e}")
        return None


def _call_groq(prompt: str) -> Optional[str]:
    """Call Groq API (free tier, OpenAI-compatible, uses Llama 3.3 70B)."""
    if not GROQ_KEY or not _HTTP:
        return None
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 300,
    }
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    try:
        if _HTTP == "httpx":
            r = httpx.post(GROQ_URL, json=payload, headers=headers, timeout=10)
            data = r.json()
        else:
            r = _requests_lib.post(GROQ_URL, json=payload, headers=headers, timeout=10)
            data = r.json()
        
        if "error" in data:
            print(f"[CARVanta] Groq API error: {data['error'].get('message', data['error'])}")
            return None
        
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[CARVanta] Groq API error: {e}")
        return None


def call_llm(prompt: str) -> Optional[str]:
    """Try Groq first (free+fast), then DeepSeek, Gemini, OpenAI."""
    result = None
    
    if GROQ_KEY:
        result = _call_groq(prompt)
    
    if not result and DEEPSEEK_KEY:
        result = _call_deepseek(prompt)
    
    if not result and GEMINI_KEY:
        result = _call_gemini(prompt)
    
    if not result and OPENAI_KEY:
        result = _call_openai(prompt)
    
    return result


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


def is_llm_available() -> bool:
    """Check if any LLM API is configured."""
    return bool(GROQ_KEY or DEEPSEEK_KEY or GEMINI_KEY or OPENAI_KEY) and _HTTP is not None
