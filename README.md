# SENTINEL (hackathon prototype)

An AI Wellbeing Safety Net prototype, per `AI_Wellbeing_Safety_Net_Report (1).docx`: a
longitudinal evidence-fusion layer that combines synthetic AI-conversation signals with
synthetic school data (attendance, grades, behaviour) to flag students who may benefit
from human wellbeing support — without diagnosing, and always with a human counsellor
making the final call.

The bulk synthetic dataset (1700+ fake conversations, 60 fake students) is classified
for free using **open-source Hugging Face models** — no API key needed for that part.
Claude is used only for the two places where natural language actually matters to a
human reader: the **live chat demo** (below) and the **on-demand "why flagged"
explanation** shown when a counsellor opens a student's profile — both cheap, low-volume
paths, per the hybrid-architecture reasoning in the project's design notes.

## Architecture

```
scripts/generate_students.py       -> data/generated/students.json       (fake longitudinal school data)
scripts/generate_conversations.py  -> data/generated/conversations.json  (fake AI chat snippets)
scripts/seed_db.py                 -> runs HF classifiers + evidence_fusion.py -> data/generated/wellbeing.db
scripts/evaluate.py                -> proves the scoring engine separates deteriorating vs stable students

backend/  (FastAPI, reads from wellbeing.db)
frontend/ (React + Vite, counsellor dashboard + live student chat demo)
```

### The three pipeline stages, and where each lives

1. **AI Conversation Analysis** — `backend/app/services/context_classifier.py` +
   `emotion.py` (free, offline, used for bulk synthetic data) or
   `backend/app/services/claude_client.py` (natural-language, used for the live chat
   demo and on-demand explanations).
2. **Longitudinal Evidence Fusion** — `backend/app/services/evidence_fusion.py`. Read
   this file first, it's the actual idea of the project.
3. **Human-in-the-Loop Review & Safeguarding** — `backend/app/services/safeguarding.py`
   + the Review Queue page in the frontend.

### Live demo flow

`frontend/src/pages/StudentChat.jsx` simulates the "government AI account" chatbot: a
student picks their ID, sends a message, and:

```
message text
  -> POST /students/{id}/messages         (backend/app/api/chat.py)
  -> stored in the database immediately   (Conversation row)
  -> classified by Claude in real time    (services/claude_client.py)
  -> risk re-fused                        (services/evidence_fusion.py)
  -> new RiskAssessment row written, with a Claude-generated explanation
  -> Dashboard / Review Queue pick it up on their next 5-second poll
```

This requires `ANTHROPIC_API_KEY` — see Setup below. Without a key, the chat page
returns a clear error but the rest of the app (seeded from the free HF pipeline) still
works.

The core scoring logic lives in `backend/app/services/evidence_fusion.py` — read that
file first, it's the actual idea of the project. Everything else is plumbing around it.

## Setup

### 1. Generate synthetic data
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd ..
python scripts/generate_students.py
python scripts/generate_conversations.py
```

### 2. Seed the database (runs the Hugging Face models once, offline)
```bash
cd backend
python ../scripts/seed_db.py
```
First run downloads ~700MB of models (cached afterwards by `transformers`). This is the
slow step; everything after it is instant.

### 3. Check the scoring engine actually works
```bash
python ../scripts/evaluate.py
```
Prints precision/recall of the fused risk score against the synthetic ground truth
(which students were scripted to deteriorate) — this is your evidence for Section 22
of the report ("how you prove your system is better").

### 4. (Optional but recommended) Enable the live Claude demo

Without this, everything still works — the dashboard, review queue, and per-student
detail all run off the pre-seeded free HF pipeline. With it, the Student Chat page
(live demo) and the on-demand explanation on each profile switch to Claude.

**Getting an API key (first time, step by step):**
1. Go to **[console.anthropic.com](https://console.anthropic.com)** and sign up / log in.
   This is the *developer* console — different from a claude.ai chat subscription; the
   two aren't linked and a claude.ai Pro plan does **not** give you API access.
2. You'll need to add billing — click **Billing** in the left sidebar and add a payment
   method + a small amount of credit (a few dollars easily covers a hackathon demo; this
   project defaults to Sonnet 5, not the pricier Opus model, and only calls the API for
   live chat messages + on-demand explanations, not the bulk synthetic dataset).
3. Click **API Keys** in the left sidebar → **Create Key**. Give it any name (e.g.
   `hackathon-demo`) → copy the key immediately (it starts `sk-ant-...` and is only
   shown once).
4. In the project folder:
   ```bash
   cp .env.example .env
   ```
   Open `.env` in any text editor and paste your key:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
5. Save the file. That's it — the backend reads it automatically on startup
   (`backend/app/config.py`). Never commit `.env` or share the key (`.gitignore` already
   excludes it).

The model used defaults to **Sonnet 5** (`ANTHROPIC_MODEL` in `.env.example`) — cheap
and fast, plenty for classification and short explanations. Change it to
`claude-haiku-4-5` for even lower cost, or `claude-opus-5` for higher quality.

### 5. Run the backend
```bash
cd backend
uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

### 6. Run the frontend
```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:5173
```

## What's real vs simplified for the hackathon

| Piece | This prototype | What a real deployment needs |
|---|---|---|
| Data | Fully synthetic, generated locally | Real (consented, minimised) data under formal legal/DPIA review — Section 16 |
| Auth | None | Government SSO, role-based access, audit logs |
| Conversation source | Templated fake chat | Real "government AI account" conversations |
| Scoring weights | Hand-picked, visible in `config.py` | Same principle (explainable), but tuned against real longitudinal outcomes |
| Chat history | Single-turn (each live message is classified independently) | Real conversations, multi-turn, with the assistant's own replies also considered |
| Live demo week bucketing | Each chat message = a new synthetic "week" appended to the timeline | Real system would use actual calendar time, not a message counter |

## Next things to build, in order
1. `scripts/evaluate.py` output looks off? Tune `RISK_THRESHOLDS` in `backend/app/config.py`.
2. Multi-turn chat history in `StudentChat.jsx` / `api/chat.py` (currently each message is scored independently, no assistant-turn memory).
3. Student-count/timeliness charts on the dashboard for the pitch deck (aggregate, not per-student).
