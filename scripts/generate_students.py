"""
Generates fictional student longitudinal data: attendance, academic scores,
and behavioural incident counts over N weeks.

Three trajectory types are seeded on purpose so we have ground truth to
validate the scoring engine against later (see scripts/evaluate.py):
  - "stable"        : normal week-to-week noise, no real change
  - "deteriorating"  : a gradual decline starting at a random week (mirrors
                       Section 7 / Scenario B of the report)
  - "volatile_but_ok": noisy but not trending down (tests false-positive rate)

Output: data/generated/students.json
"""
import json
import random
from pathlib import Path

random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_STUDENTS = 60
N_WEEKS = 20
TRAJECTORY_MIX = {
    "stable": 0.55,
    "deteriorating": 0.25,
    "volatile_but_ok": 0.20,
}


def clamp(value, low, high):
    return max(low, min(high, value))


def build_series(base_value, noise, n_weeks, trajectory, decline_start=None, decline_rate=0.0):
    series = []
    value = base_value
    for week in range(n_weeks):
        if trajectory == "deteriorating" and decline_start is not None and week >= decline_start:
            value -= decline_rate
        value_this_week = clamp(value + random.gauss(0, noise), 0, 100)
        series.append(round(value_this_week, 1))
    return series


def generate_student(student_id: int):
    trajectory = random.choices(
        population=list(TRAJECTORY_MIX.keys()),
        weights=list(TRAJECTORY_MIX.values()),
        k=1,
    )[0]

    base_attendance = random.uniform(88, 98)
    base_academic = random.uniform(65, 92)
    base_behavior_incidents = 0  # incidents per week, baseline is usually 0

    decline_start = random.randint(6, 13) if trajectory == "deteriorating" else None
    decline_rate = random.uniform(0.8, 2.2) if trajectory == "deteriorating" else 0.0

    noise = 4.0 if trajectory == "volatile_but_ok" else 1.5

    attendance = build_series(base_attendance, noise, N_WEEKS, trajectory, decline_start, decline_rate * 0.6)
    academic = build_series(base_academic, noise, N_WEEKS, trajectory, decline_start, decline_rate * 0.9)

    behavior_incidents = []
    for week in range(N_WEEKS):
        rate = base_behavior_incidents
        if trajectory == "deteriorating" and decline_start is not None and week >= decline_start:
            rate += (week - decline_start) * 0.15
        incidents = max(0, round(random.gauss(rate, 0.5)))
        behavior_incidents.append(incidents)

    return {
        "student_id": f"S{student_id:03d}",
        "trajectory_label": trajectory,  # ground truth, NOT shown to the scoring engine
        "decline_start_week": decline_start,
        "weekly": {
            "attendance_pct": attendance,
            "academic_score": academic,
            "behavior_incidents": behavior_incidents,
        },
    }


def main():
    students = [generate_student(i + 1) for i in range(N_STUDENTS)]
    out_path = OUT_DIR / "students.json"
    out_path.write_text(json.dumps(students, indent=2), encoding="utf-8")
    print(f"Wrote {len(students)} students to {out_path}")
    counts = {}
    for s in students:
        counts[s["trajectory_label"]] = counts.get(s["trajectory_label"], 0) + 1
    print("Trajectory mix:", counts)


if __name__ == "__main__":
    main()
