# Data dictionary — synthetic data only

All data under `data/generated/` is fictional, produced by `scripts/generate_students.py`
and `scripts/generate_conversations.py`. No real student data is used anywhere in this
prototype (see report Section 17/26).

## `students.json`
One record per fictional student.

| Field | Meaning |
|---|---|
| `student_id` | e.g. `S001` |
| `trajectory_label` | Ground truth used only by `scripts/evaluate.py` — `stable`, `deteriorating`, or `volatile_but_ok`. Never fed to the scoring engine. |
| `decline_start_week` | For `deteriorating` students, the week their scripted decline begins. `null` otherwise. |
| `weekly.attendance_pct` | 20-week attendance series (0-100). |
| `weekly.academic_score` | 20-week academic score series (0-100). |
| `weekly.behavior_incidents` | 20-week count of behavioural incidents per week. |

## `conversations.json`
One record per fictional AI-conversation snippet (0-3 per student per week).

| Field | Meaning |
|---|---|
| `student_id`, `week` | Links back to the student. |
| `text` | The synthetic conversation snippet. |
| `_true_category` | Ground truth template category, for validation only. The backend's classifier (`backend/app/services/context_classifier.py`) predicts its own category from `text` alone and never sees this field. |

## `wellbeing.db` (SQLite, created by `scripts/seed_db.py`)
See `backend/app/models.py` for the authoritative schema: `students`, `weekly_signals`,
`conversations` (now carrying `predicted_category` / `distress_score` from the HF models),
and `risk_assessments` (the fused output the frontend reads).
