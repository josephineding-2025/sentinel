"""
Generates fictional weekly AI-conversation snippets per student, using
templates rather than a live LLM call so this script runs offline with no
API key (matches Section 23 Phase 1: "simulated dataset").

Each student gets 0-3 conversation snippets per week. Content is drawn from
category-tagged templates. Deteriorating students draw increasingly from
"distress" templates after their decline_start_week; stable students mostly
draw from "academic_only" and "neutral" templates. This mirrors the report's
Scenario A/B/C in Section 7.

Output: data/generated/conversations.json
Each record keeps a `_true_category` field for validation only -- the
classifier in the backend must NOT be given this field.
"""
import json
import random
from pathlib import Path

random.seed(7)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "generated"

TEMPLATES = {
    "academic_only": [
        "Can you explain how recursion works?",
        "What's the time complexity of this sorting algorithm?",
        "Help me check my answer for question {n}.",
        "Can you summarize this chapter on photosynthesis?",
        "How do I solve this quadratic equation?",
    ],
    "neutral": [
        "What's a good book to read this weekend?",
        "Can you recommend a study playlist?",
        "How long should I study before an exam?",
    ],
    "academic_stress": [
        "I have three exams this week and I don't think I can prepare in time.",
        "I keep failing practice tests no matter how much I study.",
        "My parents will be so disappointed if I don't get top grades again.",
    ],
    "peer_social": [
        "My friends stopped inviting me to hang out and I don't know why.",
        "I got into another argument with my group project members.",
        "Nobody sits with me at lunch anymore.",
    ],
    "bullying": [
        "Some seniors keep making fun of me in the group chat.",
        "A classmate keeps taking my things and laughing about it with others.",
    ],
    "family_conflict": [
        "My parents have been fighting a lot at home lately.",
        "Things at home have been really tense since last month.",
    ],
    "isolation_distress": [
        "I don't really feel like talking to anyone these days.",
        "I feel like nothing I do matters anymore.",
        "I've been feeling really tired and empty lately, even after sleeping.",
        "Is it normal to feel like a burden to everyone around you?",
    ],
}

STABLE_WEIGHTS = {"academic_only": 0.55, "neutral": 0.35, "academic_stress": 0.10}
DISTRESS_WEIGHTS = {
    "academic_only": 0.15,
    "academic_stress": 0.20,
    "peer_social": 0.15,
    "bullying": 0.10,
    "family_conflict": 0.15,
    "isolation_distress": 0.25,
}


def pick_category(weights):
    categories = list(weights.keys())
    probs = list(weights.values())
    return random.choices(categories, weights=probs, k=1)[0]


def render(template):
    return template.format(n=random.randint(1, 10))


def generate_for_student(student):
    convos = []
    decline_start = student["decline_start_week"]
    is_deteriorating = student["trajectory_label"] == "deteriorating"

    for week in range(20):
        n_messages = random.randint(0, 3)
        past_decline = is_deteriorating and decline_start is not None and week >= decline_start
        weights = DISTRESS_WEIGHTS if past_decline else STABLE_WEIGHTS

        for _ in range(n_messages):
            category = pick_category(weights)
            text = render(random.choice(TEMPLATES[category]))
            convos.append({
                "student_id": student["student_id"],
                "week": week,
                "text": text,
                "_true_category": category,  # validation only, hide from classifier
            })
    return convos


def main():
    students_path = DATA_DIR / "students.json"
    if not students_path.exists():
        raise SystemExit("Run scripts/generate_students.py first.")

    students = json.loads(students_path.read_text(encoding="utf-8"))
    all_convos = []
    for student in students:
        all_convos.extend(generate_for_student(student))

    out_path = DATA_DIR / "conversations.json"
    out_path.write_text(json.dumps(all_convos, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_convos)} conversation snippets to {out_path}")


if __name__ == "__main__":
    main()
