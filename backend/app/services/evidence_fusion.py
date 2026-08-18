"""
The core idea of the whole project (Report Section 10, 14): turn several
weak, individually-inconclusive signals into one auditable risk score and a
human-legible risk state.

Risk_t = f(C_t, S_t, dC_t, dS_t, H_t) in the report is a placeholder, not a
formula. This module makes it concrete:

    risk_score = w1*z_attendance + w2*z_academic + w3*z_behavior
               + w4*conversation_distress + w5*trend_acceleration

- Weights are hand-picked and visible (not learned/hidden), on purpose --
  Section 4's "no single signal is treated as truth" principle means the
  scoring has to be explainable to a counsellor, not just accurate.
- The "insufficient evidence" state is a GATE, not part of the weighted sum
  (Section 14: an AI-only user with few conversations must never be silently
  scored as "healthy"). It overrides everything else below it.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import MIN_CONVERSATION_DATA_POINTS, RISK_THRESHOLDS
from app.services.baseline import compute_incident_stats, compute_signal_stats

WEIGHTS = {
    "attendance": 0.9,
    "academic": 0.9,
    "behavior": 1.0,
    "conversation_distress": 1.3,
    "trend_acceleration": 0.8,
}

# How many of the MOST RECENT conversations drive conversation_distress and
# top_context. Report Section 6: "the important question isn't did the
# student say something negative, it's has the pattern changed" -- averaging
# a new distressing message against months of routine "explain recursion"
# questions would dilute it into invisibility, and would make top_context
# permanently stuck on whatever the student talks about most OVERALL (in
# practice: academic homework help, for nearly every student) instead of
# what's going on lately.
RECENT_CONVERSATION_WINDOW = 8


@dataclass
class FusionResult:
    risk_score: float
    risk_state: str  # no_concern | insufficient_evidence | potential_concern | high_priority
    breakdown: dict  # per-signal contribution, for the "why flagged" explanation
    top_context: str | None


def fuse(
    attendance_series: list[float],
    academic_series: list[float],
    behavior_series: list[int],
    conversation_distress_scores: list[float],
    conversation_categories: list[str],
) -> FusionResult:
    attendance_stats = compute_signal_stats(attendance_series)
    academic_stats = compute_signal_stats(academic_series)
    behavior_stats = compute_incident_stats(behavior_series)

    total_conv_count = len(conversation_distress_scores)
    recent_distress = conversation_distress_scores[-RECENT_CONVERSATION_WINDOW:]
    recent_categories = conversation_categories[-RECENT_CONVERSATION_WINDOW:]

    # Blend of the recent average (rewards a sustained PATTERN, Section 6) and
    # the single worst recent message (a genuinely alarming disclosure should
    # not be diluted into invisibility by several calm messages around it --
    # closer to real safeguarding practice than pure averaging). Half and half.
    recent_mean = sum(recent_distress) / len(recent_distress) if recent_distress else 0.0
    recent_max = max(recent_distress) if recent_distress else 0.0
    conv_distress = 0.5 * recent_mean + 0.5 * recent_max

    # Trend acceleration: is the school-side decline getting steeper, not just present?
    # trend_slope is already normalized by the student's own noise level (baseline.py),
    # and we cap each leg so a single noisy 4-point regression can't dominate the score.
    trend_acceleration = min(1.2, max(0.0, -attendance_stats.trend_slope)) + min(1.2, max(0.0, -academic_stats.trend_slope))

    contributions = {
        "attendance": round(WEIGHTS["attendance"] * max(0.0, attendance_stats.z_score), 3),
        "academic": round(WEIGHTS["academic"] * max(0.0, academic_stats.z_score), 3),
        "behavior": round(WEIGHTS["behavior"] * max(0.0, behavior_stats.z_score), 3),
        "conversation_distress": round(WEIGHTS["conversation_distress"] * conv_distress * 3, 3),
        "trend_acceleration": round(WEIGHTS["trend_acceleration"] * trend_acceleration, 3),
    }
    risk_score = round(sum(contributions.values()), 3)

    # Confidence gate (Section 14): not enough conversational evidence AND
    # school signals aren't independently flagging concern -> don't guess.
    school_side_flagging = risk_score - contributions["conversation_distress"] >= RISK_THRESHOLDS["potential_concern"]
    if total_conv_count < MIN_CONVERSATION_DATA_POINTS and not school_side_flagging:
        return FusionResult(
            risk_score=risk_score,
            risk_state="insufficient_evidence",
            breakdown=contributions,
            top_context=None,
        )

    if risk_score >= RISK_THRESHOLDS["high_priority"]:
        state = "high_priority"
    elif risk_score >= RISK_THRESHOLDS["potential_concern"]:
        state = "potential_concern"
    else:
        state = "no_concern"

    top_context = _most_common_non_trivial(recent_categories)

    return FusionResult(risk_score=risk_score, risk_state=state, breakdown=contributions, top_context=top_context)


def _most_common_non_trivial(categories: list[str]) -> str | None:
    filtered = [c for c in categories if c and c != "none"]
    if not filtered:
        return None
    return max(set(filtered), key=filtered.count)
