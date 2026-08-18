# SENTINEL

**An AI-powered early warning system that helps school counsellors notice when a student may need support — before it becomes a crisis, not after.**

🔗 **Live demo:** [sentinel-khaki-chi.vercel.app](https://sentinel-khaki-chi.vercel.app/) *(backend is free-tier hosted and may take ~30-60s to wake up on first load)*

---

## The problem

Most school mental-health screening is a once-a-year questionnaire. A student can be quietly struggling for months between screenings — or simply choose not to disclose how they're really doing. By the time a problem surfaces, it's often already a crisis.

## What SENTINEL does

SENTINEL is a prototype "wellbeing safety net" built into a student's AI study assistant. It combines two signals schools already have — longitudinal school data (attendance, grades, behaviour) and a student's natural conversations with the AI — into one explainable risk score, and routes the students who need attention to a human counsellor's review queue.

**It never diagnoses.** The AI detects and explains; a human always makes the final call.

**Three-stage pipeline:**
1. **Conversation analysis** — every message a student sends is classified for emotional context and distress signal
2. **Evidence fusion** — combined with the student's own attendance/academic baseline into one auditable score, weighted so no single message or signal decides the outcome alone
3. **Human review** — counsellors see *why* a student was flagged, in plain language, and decide what happens next

Try **Student Chat** in the live demo to see a message get classified and flagged in real time, then check the **Review Queue** to see it land in front of a counsellor.

## Tech stack

- **Backend** — FastAPI + SQLAlchemy (SQLite)
- **Frontend** — React + Vite + Tailwind CSS
- **AI** — Google Gemini (live chat + explanations, free tier) · Hugging Face models classify the offline demo dataset
- **Hosting** — Render (API) + Vercel (frontend)

## Run it locally

```bash
git clone https://github.com/josephineding-2025/sentinel.git
cd sentinel
```

**Backend**
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload
```

**Frontend** (new terminal)
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the dashboard, student profiles, and review queue all work immediately using the sample dataset (60 fictional students) already included in the repo.

### Enabling the live chat demo (optional, free)
Everything above works with no API key. To also try the live **Student Chat** page:
1. Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Add it to `.env` as `GEMINI_API_KEY=...`
3. Restart the backend

## A note on data

Everything here is **synthetic** — 60 fictional students, fictional conversations, generated locally. No real student data was used at any point. Full design rationale in `AI_Wellbeing_Safety_Net_Report (1).docx`.
