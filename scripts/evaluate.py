"""
Answers the question "does the scoring engine actually work?" (Report
Section 22: baseline vs proposed system, precision/recall/timeliness).

Ground truth comes from generate_students.py's trajectory_label, which the
scoring engine never sees. A student labelled "deteriorating" is a true
positive if the fused risk_state reaches potential_concern/high_priority at
any point; "stable"/"volatile_but_ok" students that get flagged are false
positives. Also reports how many weeks BEFORE the synthetic decline started
the system would have flagged the student, if at all (timeliness).

Run after seed_db.py:
    cd backend
    python ../scripts/evaluate.py
"""
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db import SessionLocal  # noqa: E402
from app.models import RiskAssessment  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
FLAGGED_STATES = {"potential_concern", "high_priority"}


def main():
    students = json.loads((DATA_DIR / "students.json").read_text(encoding="utf-8"))
    db = SessionLocal()

    tp = fp = tn = fn = 0
    detection_lags = []  # weeks between decline_start and first flag, for true positives

    for student in students:
        sid = student["student_id"]
        label = student["trajectory_label"]
        decline_start = student["decline_start_week"]

        assessments = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.student_id == sid)
            .order_by(RiskAssessment.week)
            .all()
        )
        first_flag_week = next((a.week for a in assessments if a.risk_state in FLAGGED_STATES), None)
        ever_flagged = first_flag_week is not None

        is_true_deteriorating = label == "deteriorating"

        if is_true_deteriorating and ever_flagged:
            tp += 1
            detection_lags.append(first_flag_week - decline_start)
        elif is_true_deteriorating and not ever_flagged:
            fn += 1
        elif not is_true_deteriorating and ever_flagged:
            fp += 1
        else:
            tn += 1

    db.close()

    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    fpr = fp / (fp + tn) if (fp + tn) else float("nan")

    print("=== Baseline vs proposed: detection performance (Report Section 22) ===")
    print(f"True positives (deteriorating, correctly flagged):  {tp}")
    print(f"False negatives (deteriorating, missed):             {fn}")
    print(f"False positives (stable/volatile, wrongly flagged):  {fp}")
    print(f"True negatives (stable/volatile, correctly ignored): {tn}")
    print()
    print(f"Precision: {precision:.2f}   Recall: {recall:.2f}   False-positive rate: {fpr:.2f}")
    print()

    if detection_lags:
        avg_lag = sum(detection_lags) / len(detection_lags)
        print(f"Avg weeks between synthetic decline start and first flag: {avg_lag:.1f}")
        print("(negative = flagged BEFORE the scripted decline began, i.e. caught by conversation signals alone)")
    else:
        print("No true positives were detected -- check RISK_THRESHOLDS in app/config.py, they may be too strict.")


if __name__ == "__main__":
    main()
