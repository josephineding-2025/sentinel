"""
Turns evidence_fusion's numeric breakdown into a short, plain-language
explanation for the counsellor-facing detail view (the "reason" behind a
score, not just the number).

explain() is the offline template fallback -- free, deterministic, no API
key needed. get_or_generate_explanation() is what actually runs in the app:
it upgrades a stored assessment to a real Gemini/Claude explanation the
FIRST time anyone looks at it, then caches that in the database
(RiskAssessment.explanation_ai_generated) so repeated views -- including the
Review Queue's 5-second polling -- don't re-call the API for the same
already-generated explanation.
"""
from __future__ import annotations

import json

from app.config import ANTHROPIC_API_KEY, GEMINI_API_KEY

CONTEXT_LABELS = {
    "academic": "academic pressure",
    "peer_social": "peer/social conflict",
    "bullying": "bullying",
    "family_conflict": "family conflict",
    "isolation_distress": "social isolation",
}

SIGNAL_LABELS = {
    "attendance": "a decline in attendance relative to this student's own baseline",
    "academic": "a drop in academic performance relative to this student's own baseline",
    "behavior": "an increase in behavioural incidents relative to this student's own baseline",
    "conversation_distress": "distress-related language in recent AI conversations",
    "trend_acceleration": "a worsening (accelerating) trend in school-side signals",
}

MIN_CONTRIBUTION = 0.15  # ignore near-zero contributions when explaining


def explain(risk_state: str, breakdown: dict, top_context: str | None) -> str:
    if risk_state == "insufficient_evidence":
        return (
            "Not enough conversational evidence yet to make a meaningful inference, and "
            "school-side signals are not independently indicating concern. This is expected "
            "for students who mostly use the AI for academic tasks -- it is NOT treated as "
            "'healthy', just unresolved."
        )

    if risk_state == "no_concern":
        return "Current signals do not indicate meaningful deterioration from this student's own baseline."

    ranked = sorted(
        ((k, v) for k, v in breakdown.items() if v >= MIN_CONTRIBUTION),
        key=lambda kv: kv[1],
        reverse=True,
    )
    top_signals = [SIGNAL_LABELS[k] for k, _ in ranked[:2] if k in SIGNAL_LABELS]

    if not top_signals:
        reason = "a combination of several weak signals, none individually large, crossing the review threshold together"
    elif len(top_signals) == 1:
        reason = top_signals[0]
    else:
        reason = f"{top_signals[0]} together with {top_signals[1]}"

    sentence = f"Flagged primarily due to {reason}."

    if top_context and top_context in CONTEXT_LABELS:
        sentence += f" The most frequent potential contributing context in conversations was {CONTEXT_LABELS[top_context]}."

    if risk_state == "high_priority":
        sentence += " Multiple strong signals warrant prompt review."

    return sentence


def get_or_generate_explanation(db, assessment, conversations: list) -> str:
    """
    Returns a genuinely AI-generated explanation for this assessment,
    generating and caching one (Gemini first, Claude as a fallback) the
    first time it's requested. Returns the stored template text only if
    neither is configured or both calls fail -- so the app still works with
    no key at all.
    """
    if assessment.explanation_ai_generated:
        return assessment.explanation or ""

    breakdown = json.loads(assessment.breakdown_json) if assessment.breakdown_json else {}
    recent_texts = [c.text for c in conversations[-5:]]

    text = None
    if GEMINI_API_KEY:
        try:
            from app.services import gemini_client
            text = gemini_client.generate_explanation(
                risk_state=assessment.risk_state,
                breakdown=breakdown,
                top_context=assessment.top_context,
                recent_snippets=recent_texts,
            )
        except Exception:
            text = None

    if text is None and ANTHROPIC_API_KEY:
        try:
            from app.services import claude_client
            text = claude_client.generate_explanation(
                risk_state=assessment.risk_state,
                breakdown=breakdown,
                top_context=assessment.top_context,
                recent_snippets=recent_texts,
            )
        except Exception:
            text = None

    if text:
        assessment.explanation = text
        assessment.explanation_ai_generated = 1
        db.commit()
        return text

    return assessment.explanation or ""
