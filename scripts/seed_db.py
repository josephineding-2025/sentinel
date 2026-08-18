"""
Loads data/generated/students.json + conversations.json, runs the
Hugging Face classifiers over every conversation snippet, runs the evidence
fusion engine per student per week, and writes everything into SQLite.

This is where the "expensive" model inference happens -- once, offline --
so the FastAPI endpoints stay fast and just read pre-computed results.

Run from the backend/ directory (needs the app package on the path):
    cd backend
    python ../scripts/seed_db.py
"""
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Conversation, RiskAssessment, Student, WeeklySignal  # noqa: E402
from app.services import context_classifier, emotion, evidence_fusion, explain, safeguarding  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
N_WEEKS = 20


def load_json(name):
    path = DATA_DIR / name
    if not path.exists():
        raise SystemExit(f"Missing {path} -- run generate_students.py and generate_conversations.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    students_raw = load_json("students.json")
    conversations_raw = load_json("conversations.json")

    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print(f"Classifying {len(conversations_raw)} conversation snippets with Hugging Face models "
          f"(first run downloads the models, ~700MB total, then it's cached)...")
    convos_by_student_week = {}
    for i, convo in enumerate(conversations_raw):
        category, confidence = context_classifier.classify_context(convo["text"])
        distress = emotion.distress_score(convo["text"])

        key = (convo["student_id"], convo["week"])
        convos_by_student_week.setdefault(key, []).append({
            "text": convo["text"],
            "category": category,
            "confidence": confidence,
            "distress": distress,
        })

        db.add(Conversation(
            student_id=convo["student_id"],
            week=convo["week"],
            text=convo["text"],
            predicted_category=category,
            category_confidence=confidence,
            distress_score=distress,
        ))

        if (i + 1) % 25 == 0:
            print(f"  ...{i + 1}/{len(conversations_raw)}")

    print("Running evidence fusion per student per week...")
    for student in students_raw:
        sid = student["student_id"]
        db.add(Student(student_id=sid))

        attendance_full = student["weekly"]["attendance_pct"]
        academic_full = student["weekly"]["academic_score"]
        behavior_full = student["weekly"]["behavior_incidents"]

        for week in range(N_WEEKS):
            db.add(WeeklySignal(
                student_id=sid,
                week=week,
                attendance_pct=attendance_full[week],
                academic_score=academic_full[week],
                behavior_incidents=behavior_full[week],
            ))

            # Fuse using only data UP TO this week -- no peeking at the future,
            # matches "longitudinal" framing (Section 8), not a static snapshot.
            attendance_so_far = attendance_full[: week + 1]
            academic_so_far = academic_full[: week + 1]
            behavior_so_far = behavior_full[: week + 1]

            convos_so_far = []
            for w in range(week + 1):
                convos_so_far.extend(convos_by_student_week.get((sid, w), []))
            distress_scores = [c["distress"] for c in convos_so_far]
            categories = [c["category"] for c in convos_so_far]

            result = evidence_fusion.fuse(
                attendance_series=attendance_so_far,
                academic_series=academic_so_far,
                behavior_series=behavior_so_far,
                conversation_distress_scores=distress_scores,
                conversation_categories=categories,
            )
            routing = safeguarding.route(result.top_context, result.risk_state)
            reason = explain.explain(result.risk_state, result.breakdown, result.top_context)

            db.add(RiskAssessment(
                student_id=sid,
                week=week,
                risk_score=result.risk_score,
                risk_state=result.risk_state,
                top_context=result.top_context,
                breakdown_json=json.dumps(result.breakdown),
                explanation=reason,
                routing=routing,
                reviewed=0,
            ))

    db.commit()
    db.close()
    print("Done. Database seeded at data/generated/wellbeing.db")


if __name__ == "__main__":
    main()
