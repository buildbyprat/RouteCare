# RouteCare — AI Emergency Response System
### Powered by Google Gemini · Flask · Google Cloud Run

RouteCare continuously monitors patient vitals during ambulance transit, detects clinical deterioration using WHO/AHA guardrails, dynamically ranks hospitals by GPS and ICU capacity, and uses **Google Gemini AI** for real-time paramedic action plans, SBAR triage handoffs, and patient family explanations.

---

##  Problem

Emergency routing today is mostly manual — dependent on phone calls, incomplete data, and human judgment under pressure.

This often leads to:
- Delays in critical care  
- Incorrect hospital selection  
- Poor ICU and resource utilization  

---

##  Solution

RouteCare introduces a real-time AI-assisted decision system that:
- Continuously analyzes patient vitals  
- Applies clinical safety guardrails  
- Recommends the best hospital with clear reasoning  

The goal is simple:  
**faster, safer, and more reliable emergency decisions.**

---

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get a free Gemini API key at: https://aistudio.google.com/app/apikey
cp .env.example .env
# Edit .env → set GEMINI_API_KEY=your-key-here

# 3. Run
python app.py
# Open: http://localhost:5000
```

---

## Deploy to Google Cloud Run

```bash
# 1. Install Google Cloud SDK and authenticate
gcloud auth login

# 2. Set your project ID and Gemini key in deploy.sh
nano deploy.sh   # Edit PROJECT_ID and GEMINI_API_KEY

# 3. One-command deploy
chmod +x deploy.sh && ./deploy.sh
```

The script: enables APIs → stores key in Secret Manager → builds via Cloud Build → deploys to Cloud Run → prints live URL.

---

## Demo Credentials

| Role      | User ID | Password |
|-----------|---------|----------|
| Ambulance | AMB001  | pass123  |
| Ambulance | AMB002  | pass456  |
| Hospital  | HSP001  | hosp123  |
| Hospital  | HSP002  | hosp456  |

---

## Google Gemini Features

| Feature | Location | Description |
|---------|----------|-------------|
| Counterfactual Action Plan | Emergency page | Step-by-step "do this RIGHT NOW" paramedic guide |
| SBAR Triage Handoff | Emergency + Hospital dashboard | Structured clinical handoff (Situation·Background·Assessment·Recommendation) |
| Family Explanation | Both dashboards | Jargon-free update for the patient's family |
| Gemini Status Badge | Emergency page header | Live indicator: "Gemini Live" vs "Rule-Based Fallback" |
| /api/gemini_status | API endpoint | Health check — returns available:true/false |
| /api/gemini_counterfactual | API endpoint | On-demand refresh via "Refresh Gemini" button |

All Gemini features **degrade gracefully** — if the API key is missing or unavailable, rule-based fallbacks activate automatically. The core clinical workflow is never blocked.

---

## Project Structure

```
routecare/
├── app.py                      # Flask backend — all routes
├── gemini_service.py           # Google Gemini AI integration (3 functions + health check)
├── db.py                       # SQLite database layer
├── requirements.txt            # All Python dependencies
├── Dockerfile                  # Cloud Run container (Gunicorn)
├── deploy.sh                   # One-command GCP deployment script
├── .env.example                # Environment variable template
├── .gitignore
├── ai/
│   └── ai_logic.py             # Rule-based engine + Gemini calls (Step 7)
├── data/
│   ├── hospitals.json
│   └── routecare.db            # SQLite DB (auto-created on first run)
├── static/css/style.css
└── templates/
    ├── index.html              # Landing page — Google tech badges added
    ├── emergency.html          # Paramedic dashboard — Gemini panel added
    ├── hospital_dashboard.html # Hospital view — SBAR + family note added
    ├── audit_log.html          # Audit trail — Gemini source column added
    ├── login.html
    ├── patient_form.html
    └── signup.html
```

---
## AI Architecture

```
Patient Vitals (every 3 seconds)
          │
          ▼
┌─────────────────────────────┐
│  Rule-Based Engine          │  ← Always runs, always reliable
│  ai_logic.py — Steps 1–6   │
│  • 9 WHO/AHA Guardrails     │
│  • Stability Score 0–100    │
│  • Hospital Ranking         │
│  • Edge Case Detection      │
└──────────────┬──────────────┘
               │ Step 7
               ▼
┌─────────────────────────────┐
│  Google Gemini 1.5 Flash    │  ← Enhances with natural language
│  gemini_service.py          │
│  • Counterfactual Plan      │  "1. Give 15L O₂. 2. Start IV..."
│  • SBAR Triage Note         │  Hospital handoff format
│  • Family Explanation       │  "Your loved one is..."
│                             │
│  Graceful fallback if       │  Rule-based responses if Gemini
│  API unavailable            │  is down — system never blocks
└─────────────────────────────┘
               │
               ▼
      emergency.html + hospital_dashboard.html
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vitals` | Live vitals + full AI + Gemini decision |
| GET | `/api/gemini_status` | Gemini health check |
| POST | `/api/gemini_counterfactual` | On-demand Gemini action plan |
| GET | `/api/hospitals` | All hospitals |
| GET | `/api/hospital/<id>` | Hospital detail + doctors |
| GET | `/api/emergency_status` | Live emergency for hospital |
| POST | `/api/accept_emergency` | Hospital accepts patient |
| POST | `/api/update_equipment` | Update hospital equipment |
| POST | `/api/toggle_doctor` | Toggle doctor duty status |
| POST | `/api/add_doctor` | Add doctor to roster |
| GET | `/audit` | Audit log view |


##  Key Features

- **Live Vitals Monitoring**  
  Real-time tracking with auto-refresh every 15 seconds  

- **AI Stability Scoring**  
  Instant condition assessment with visual indicators  

- **Smart Hospital Matching**  
  Ranked by ICU beds, ventilators, ETA, and specialty  

- **Hospital Dashboard**  
  Incoming alerts with AI summary and preparation checklist  

- **One-Click Auto Reroute**  
  Quickly redirect ambulance based on updated conditions  

- **Explainable Decisions**  
  Clear reasoning behind every recommendation  

- **Audit Logging (Architecture-level feature)**  
  Every decision can be recorded for compliance and review  

---

##  Architecture Overview

RouteCare follows a multi-agent system design:

- **Ambulance Agent** → captures and sends patient data  
- **AI Decision Core** → processes vitals and generates decisions  
- **Hospital Agent** → receives alerts and updates capacity  
- **Compliance Layer** → enforces clinical guardrails  
- **Audit System** → logs decisions for traceability  

---

##  Impact (Estimated)

- ~8–9 hours saved per day in decision-making  
- ~10% reduction in ICU misallocation  
- Faster response → improved patient outcomes  

---

##  Compliance & Safety

- Guardrails aligned with clinical standards (ICD-10 inspired)  
- Critical conditions trigger strict routing constraints  
- Sensitive patient data shared only after hospital acceptance  
- Designed for transparency and auditability  

---

##  Future Scope

- Integration with real hospital systems  
- Multi-patient scaling  
- AI model improvements with real data  
- Voice input for paramedics  
- Regional language support  

---

##  Authors

- **Pratiksha Chakraborty**  
- **Suryansh Dev** 
- **Mohammad Shahwaz Alam** 

---

##  Final Note

RouteCare is not designed to replace medical professionals.  
It is built to support them by making critical decisions faster, clearer, and more reliable when it matters most.
