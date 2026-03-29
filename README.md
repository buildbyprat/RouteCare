#  RouteCare — AI Emergency Response System

An AI-powered emergency response system that monitors patient vitals in real-time and intelligently routes ambulances to the most suitable hospital based on medical urgency, resource availability, and distance.

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

## Quick Start

```bash
pip install flask
python app.py
```
Open: http://localhost:5000

---

##  Demo Login Credentials

| Role       | User ID | Password  |
|------------|---------|-----------|
| Ambulance  | AMB006  | 1234      |
| Hospital   | HSP006  | 1234      |

---

##  Project Structure

```
routecare/
├── app.py                  # Flask backend + routes
├── requirements.txt
├── ai/
│   └── ai_logic.py         # AI decision engine
├── data/
│   └── hospitals.json      # Hospital database
├── static/
│   └── css/style.css       # Full stylesheet
└── templates/
    ├── index.html           # Landing page
    ├── login.html           # Login (ambulance + hospital toggle)
    ├── patient_form.html    # Patient intake form
    ├── emergency.html       # Live monitoring + AI + hospital recommendation
    └── hospital_dashboard.html  # Hospital incoming alert view
```

---

##  AI Logic (`ai/ai_logic.py`)

**Function:** `get_ai_decision(vitals)`

**Input:**
- `hr` — Heart Rate (bpm)
- `bp_sys`, `bp_dia` — Blood Pressure (mmHg)
- `spo2` — Oxygen Saturation (%)
- `temp` — Temperature (°C)
- `emergency_type` — Type of emergency

**Output:**
- `stability_score` — 0–100
- `condition` — Stable / Moderate / Critical
- `explanation` — AI-generated clinical reasoning
- `hospitals_ranked` — Sorted list of hospitals by match score
- `hospital_alert` — Pre-generated alert for receiving hospital
- `prep_items` — Items hospital should prepare

##  Decision Logic

The system evaluates patient vitals and deducts points for abnormal values across:
- Heart Rate  
- Blood Pressure  
- Oxygen Saturation  
- Temperature  

Hospital ranking is computed using:
ICU beds × weight + ventilators × weight − distance penalty + specialty match bonus
This ensures a balance between **urgency, capability, and travel time**.

---

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

- **Pratiksha Chakraborty** — Frontend & Integration  
- **Suryansh Dev** — Backend & API Development  
- **Mohammad Shahwaz Alam** — AI Logic & Architecture  

---

##  Final Note

RouteCare is not designed to replace medical professionals.  
It is built to support them by making critical decisions faster, clearer, and more reliable when it matters most.
