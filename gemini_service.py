"""
gemini_service.py — Google Gemini AI Integration for RouteCare
==============================================================
Adds three Gemini-powered capabilities on top of the existing rule-based engine:

  1. gemini_counterfactual()   — "What should the paramedic do RIGHT NOW?"
                                  Prescriptive, step-by-step action plan.

  2. gemini_explain_decision() — Plain-English explanation for the family/patient.
                                  Warm tone, no medical jargon.

  3. gemini_triage_summary()   — Structured triage note for receiving hospital.
                                  SBAR format (Situation-Background-Assessment-Recommendation).

All three functions degrade gracefully: if Gemini is unavailable (no API key,
quota exceeded, network error), they return a sensible rule-based fallback
so the existing RouteCare system keeps working without interruption.

Setup:
  export GEMINI_API_KEY="your-key-here"
  OR set it in .env and load with python-dotenv

Cloud deployment note:
  On Cloud Run, set GEMINI_API_KEY as a Secret Manager secret mounted as env var.
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Try to import the Gemini SDK ────────────────────────────────────────────
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    logger.warning("[Gemini] google-generativeai not installed. Run: pip install google-generativeai")

# ── Configure API key ────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-1.5-flash"   # Fast, cheap, perfect for real-time use

_client = None

def _get_client():
    """Lazy-init Gemini client. Returns None if unavailable."""
    global _client
    if _client is not None:
        return _client
    if not _GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _client = genai.GenerativeModel(GEMINI_MODEL)
        logger.info(f"[Gemini] Client initialized — model: {GEMINI_MODEL}")
        return _client
    except Exception as e:
        logger.error(f"[Gemini] Init failed: {e}")
        return None


def _call_gemini(prompt: str, max_tokens: int = 400) -> str | None:
    """
    Core Gemini call with timeout and error handling.
    Returns response text or None on failure.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        response = client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,   # Low temp for clinical accuracy
            )
        )
        return response.text.strip() if response.text else None
    except Exception as e:
        logger.warning(f"[Gemini] API call failed: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# 1. COUNTERFACTUAL REASONING — CC-ACG
#    "What should I do RIGHT NOW?" — prescriptive paramedic action plan
# ════════════════════════════════════════════════════════════════════════════

def gemini_counterfactual(vitals: dict, condition: str, guardrails: list,
                           emergency_type: str, patient: dict) -> dict:
    """
    Returns a structured counterfactual action plan:
    {
        'immediate_actions': [list of step-by-step actions],
        'what_not_to_do':    [list of contraindications],
        'medications':       [relevant drugs/doses to consider],
        'monitoring':        [what to watch next],
        'source':            'gemini' or 'rule_based'
    }
    """
    # Build vitals summary for prompt
    vitals_str = (
        f"HR: {vitals.get('hr', '?')} bpm | "
        f"BP: {vitals.get('bp_sys', '?')}/{vitals.get('bp_dia', '?')} mmHg | "
        f"SpO2: {vitals.get('spo2', '?')}% | "
        f"Temp: {vitals.get('temp', '?')}°C"
    )
    guardrail_str = ", ".join(g['name'] for g in guardrails) if guardrails else "None"
    patient_age   = patient.get('age', 'unknown')
    patient_cond  = patient.get('conditions', 'none reported')

    prompt = f"""You are a senior emergency medicine physician advising a paramedic in real time.

PATIENT DATA:
- Emergency: {emergency_type}
- Age: {patient_age} | Pre-existing: {patient_cond}
- Current vitals: {vitals_str}
- Patient condition: {condition}
- Triggered clinical guardrails: {guardrail_str}

The ambulance is en route to hospital. Give a CONCISE, NUMBERED action plan the paramedic must follow RIGHT NOW.

Respond ONLY in this exact JSON format (no markdown, no extra text):
{{
  "immediate_actions": ["action 1", "action 2", "action 3", "action 4"],
  "what_not_to_do": ["contraindication 1", "contraindication 2"],
  "medications": ["drug/dose 1 if applicable"],
  "monitoring": ["vital to watch 1", "vital to watch 2"]
}}

Keep each item under 15 words. Be specific and clinical. Use standard paramedic protocols."""

    raw = _call_gemini(prompt, max_tokens=300)

    # Parse JSON response
    if raw:
        try:
            # Strip any accidental markdown fences
            clean = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)
            parsed['source'] = 'gemini'
            return parsed
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[Gemini] Counterfactual parse failed: {e}. Raw: {raw[:100]}")

    # ── Rule-based fallback ───────────────────────────────────────────────
    return _rule_based_counterfactual(vitals, condition, guardrails)


def _rule_based_counterfactual(vitals, condition, guardrails):
    """Fallback when Gemini is unavailable — uses hard clinical rules."""
    actions = []
    contraindications = []
    medications = []
    monitoring = []

    spo2   = vitals.get('spo2', 100)
    bp_sys = vitals.get('bp_sys', 120)
    hr     = vitals.get('hr', 80)
    temp   = vitals.get('temp', 37.0)

    # SpO2
    if spo2 < 85:
        actions.append("Apply 100% O₂ via non-rebreather mask at 15 L/min")
        actions.append("Prepare for bag-valve-mask ventilation")
        monitoring.append("SpO2 — recheck every 60 seconds")
    elif spo2 < 92:
        actions.append("Apply supplemental O₂ at 4–6 L/min via nasal cannula")

    # BP
    if bp_sys < 80:
        actions.append("Establish IV access — administer 500ml NS bolus")
        actions.append("Position patient supine with legs elevated 15°")
        contraindications.append("Do NOT give nitroglycerin — BP already low")
        monitoring.append("BP — recheck every 2 minutes")
        medications.append("Consider vasopressors (dopamine 5 mcg/kg/min) if no response")
    elif bp_sys > 180:
        actions.append("Calm patient, reduce stimulation")
        contraindications.append("Do NOT give fluids — may worsen hypertension")
        medications.append("Consider labetalol if protocol permits")

    # HR
    if hr > 140:
        actions.append("12-lead ECG — identify rhythm immediately")
        actions.append("Prepare defibrillator — set to 200J biphasic")
        monitoring.append("Cardiac rhythm — continuous")
    elif hr < 45:
        actions.append("Atropine 0.5mg IV — repeat every 3–5 min (max 3mg)")
        actions.append("Prepare transcutaneous pacing")
        monitoring.append("HR — continuous cardiac monitoring")

    # Temp
    if temp > 40.0:
        actions.append("Remove excess clothing, apply cool compresses to neck/axilla/groin")
        actions.append("Ensure IV access — cool fluids if available")
    elif temp < 35.0:
        actions.append("Apply warming blanket immediately")
        actions.append("Protect from further heat loss — warm IV fluids if available")

    if condition == 'Critical' and not actions:
        actions = ["Establish IV access", "Apply cardiac monitor", "Prepare resuscitation drugs", "Notify receiving hospital NOW"]

    if not monitoring:
        monitoring = ["HR", "BP", "SpO2", "Responsiveness"]

    return {
        'immediate_actions': actions or ["Monitor all vitals continuously", "Maintain airway patency"],
        'what_not_to_do':    contraindications or ["Do not leave patient unmonitored"],
        'medications':       medications or ["Per standing orders only"],
        'monitoring':        monitoring,
        'source':            'rule_based'
    }


# ════════════════════════════════════════════════════════════════════════════
# 2. PLAIN-ENGLISH EXPLANATION — for patient/family
#    Warm, jargon-free, reassuring but honest
# ════════════════════════════════════════════════════════════════════════════

def gemini_explain_for_family(vitals: dict, condition: str,
                               emergency_type: str, hospital_name: str,
                               eta_minutes: int) -> str:
    """
    Returns a 2–3 sentence plain English explanation suitable for a
    patient or their family member. No medical jargon.
    Falls back to a template string if Gemini unavailable.
    """
    vitals_str = (
        f"HR {vitals.get('hr')} bpm, BP {vitals.get('bp_sys')}/{vitals.get('bp_dia')} mmHg, "
        f"SpO2 {vitals.get('spo2')}%, Temp {vitals.get('temp')}°C"
    )

    prompt = f"""You are a compassionate emergency paramedic speaking directly to a patient's family member.

Situation:
- Patient emergency: {emergency_type}
- Current medical condition level: {condition}
- Vitals: {vitals_str}
- We are going to: {hospital_name}
- Estimated arrival: {eta_minutes} minutes

Write 2-3 sentences explaining the situation clearly, warmly, and honestly. 
Use NO medical jargon. Do NOT say "stability score" or mention specific vital numbers.
Be reassuring but truthful. Focus on what is being done and where they are going.
Write in second person ("Your loved one...").
Respond with ONLY the explanation text, no formatting."""

    result = _call_gemini(prompt, max_tokens=150)

    if result:
        return result

    # ── Fallback template ────────────────────────────────────────────────
    cond_map = {
        'Stable':   "is currently stable and being monitored closely",
        'Moderate': "needs prompt medical attention and is being stabilised",
        'Critical': "is in a serious condition and receiving emergency care"
    }
    cond_desc = cond_map.get(condition, "is receiving care")
    return (
        f"Your loved one {cond_desc} en route to {hospital_name}. "
        f"Our paramedic team is providing the best possible care during transit. "
        f"We expect to arrive at the hospital in approximately {eta_minutes} minutes, "
        f"where the medical team is being prepared for their arrival."
    )


# ════════════════════════════════════════════════════════════════════════════
# 3. SBAR TRIAGE SUMMARY — for receiving hospital
#    Situation-Background-Assessment-Recommendation format
# ════════════════════════════════════════════════════════════════════════════

def gemini_sbar_summary(vitals: dict, condition: str, guardrails: list,
                         patient: dict, hospital_name: str,
                         eta_minutes: int, prep_items: list) -> dict:
    """
    Returns an SBAR-format triage note:
    {
        'situation':      str,
        'background':     str,
        'assessment':     str,
        'recommendation': str,
        'source':         'gemini' or 'rule_based'
    }
    """
    vitals_str = (
        f"HR: {vitals.get('hr')} bpm | BP: {vitals.get('bp_sys')}/{vitals.get('bp_dia')} mmHg | "
        f"SpO2: {vitals.get('spo2')}% | Temp: {vitals.get('temp')}°C"
    )
    guardrail_str = "; ".join(
        f"{g['name']} [{g['icd10']}]" for g in guardrails
    ) if guardrails else "None"

    prompt = f"""You are a senior paramedic transmitting a pre-arrival SBAR handoff to the receiving hospital.

PATIENT INFO:
- Name: {patient.get('name', 'Unknown')} | Age: {patient.get('age', '?')} | Gender: {patient.get('gender', '?')}
- Blood Group: {patient.get('blood_group', 'Unknown')}
- Emergency: {patient.get('emergency', 'General')}
- Symptoms: {patient.get('symptoms', 'Not reported')}
- Pre-existing conditions: {patient.get('conditions', 'None reported')}

CURRENT STATUS:
- Vitals: {vitals_str}
- Condition: {condition}
- Active clinical guardrails: {guardrail_str}
- ETA to {hospital_name}: {eta_minutes} minutes
- Prep items requested: {', '.join(prep_items)}

Generate a concise SBAR handoff note. Each section max 2 sentences.
Respond ONLY in this exact JSON format (no markdown):
{{
  "situation": "...",
  "background": "...",
  "assessment": "...",
  "recommendation": "..."
}}"""

    raw = _call_gemini(prompt, max_tokens=350)

    if raw:
        try:
            clean  = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)
            parsed['source'] = 'gemini'
            return parsed
        except Exception as e:
            logger.warning(f"[Gemini] SBAR parse failed: {e}")

    # ── Rule-based SBAR fallback ─────────────────────────────────────────
    emergency_type = patient.get('emergency', 'General emergency')
    return {
        'situation':      (
            f"Incoming {condition.upper()} patient via ambulance. "
            f"ETA: {eta_minutes} minutes. Emergency: {emergency_type}."
        ),
        'background':     (
            f"Patient: {patient.get('name','Unknown')}, {patient.get('age','?')}yo "
            f"{patient.get('gender','')}, Blood group: {patient.get('blood_group','Unknown')}. "
            f"Pre-existing: {patient.get('conditions','None reported')}. "
            f"Symptoms: {patient.get('symptoms','Not reported')}."
        ),
        'assessment':     (
            f"Current vitals: {vitals_str}. "
            f"Active guardrails: {guardrail_str}."
        ),
        'recommendation': (
            f"Please prepare: {', '.join(prep_items)}. "
            f"{'ICU and resuscitation team on standby.' if condition == 'Critical' else 'Emergency bay and attending physician required.'}"
        ),
        'source': 'rule_based'
    }


# ════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK — used by /api/gemini_status endpoint
# ════════════════════════════════════════════════════════════════════════════

def gemini_health_check() -> dict:
    """Returns status dict for the /api/gemini_status endpoint."""
    client = _get_client()
    if client is None:
        return {
            'available':   False,
            'model':       GEMINI_MODEL,
            'reason':      'No API key' if not GEMINI_API_KEY else 'SDK not installed',
            'fallback':    'rule_based'
        }
    # Quick ping
    try:
        r = client.generate_content("Reply with the single word: OK",
            generation_config=genai.types.GenerationConfig(max_output_tokens=5))
        ok = 'OK' in (r.text or '')
        return {'available': ok, 'model': GEMINI_MODEL,
                'reason': 'Connected' if ok else 'Unexpected response', 'fallback': 'rule_based'}
    except Exception as e:
        return {'available': False, 'model': GEMINI_MODEL,
                'reason': str(e), 'fallback': 'rule_based'}
