"""
Individual/school baselines and trend calculation (Report Section 9).

Deliberately NOT "attendance < 90% -> alert". Instead we ask: how far is the
student's *recent* window from their *own earlier* baseline, in standard
deviations, and is that gap widening over time?

This module has no ML in it on purpose — it's plain statistics so it stays
auditable, which matters a lot for a government deployment (Section 16).
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass
class SignalStats:
    baseline_mean: float
    baseline_std: float
    current_mean: float
    z_score: float          # how far current window is from this student's own baseline
    trend_slope: float      # recent linear trend, normalized by baseline_std (std-devs/week)


def _slope(values: list[float]) -> float:
    """Least-squares slope of values against their index (0, 1, 2, ...)."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    return numerator / denominator if denominator else 0.0


# Below this many total data points, a "baseline vs recent" split is just
# comparing noise against noise -- z-scores from that are not meaningful and
# were empirically found (via scripts/evaluate.py) to flag almost every
# student within the first 2-3 weeks purely from random jitter. Report Section
# 4 principle 3 says missing info isn't "healthy" -- symmetrically, it also
# isn't grounds for a confident z-score. We stay neutral (z=0) until there's
# enough history, and rely on the insufficient_evidence gate in the meantime.
MIN_BASELINE_POINTS = 6


def compute_signal_stats(all_weeks: list[float], baseline_window: int = 8, recent_window: int = 4) -> SignalStats:
    """
    Splits a student's weekly series into an early "baseline" window and a
    "recent" window, and reports how far recent behaviour has drifted.

    A HIGHER z_score should always mean "more concerning" — callers are
    responsible for sign-flipping metrics where a rise is bad (e.g. behaviour
    incidents) vs where a fall is bad (e.g. attendance, grades).
    """
    if len(all_weeks) < MIN_BASELINE_POINTS:
        current_mean = mean(all_weeks) if all_weeks else 0.0
        return SignalStats(
            baseline_mean=round(current_mean, 2),
            baseline_std=0.0,
            current_mean=round(current_mean, 2),
            z_score=0.0,
            trend_slope=0.0,
        )

    if len(all_weeks) < baseline_window + recent_window:
        split = len(all_weeks) // 2
        baseline = all_weeks[:split]
        recent = all_weeks[split:]
    else:
        baseline = all_weeks[:baseline_window]
        recent = all_weeks[-recent_window:]

    baseline_mean = mean(baseline)
    # Floor the std so a couple of coincidentally-close baseline points can't
    # produce a near-zero denominator and an exploding z-score.
    baseline_std = max(pstdev(baseline) if len(baseline) > 1 else 0.0, 1.5)

    current_mean = mean(recent) if recent else baseline_mean
    z = (baseline_mean - current_mean) / baseline_std

    # Normalize slope by this student's own noise level (baseline_std), not
    # raw units-per-week. A steep-looking 4-point wiggle in a naturally noisy
    # student's data is expected and shouldn't score the same as an equally
    # steep slope in a normally-stable student's data.
    normalized_slope = _slope(recent) / baseline_std

    return SignalStats(
        baseline_mean=round(baseline_mean, 2),
        baseline_std=round(baseline_std, 2),
        current_mean=round(current_mean, 2),
        z_score=round(z, 2),
        trend_slope=round(normalized_slope, 3),
    )


def compute_incident_stats(all_weeks: list[int], baseline_window: int = 8, recent_window: int = 4) -> SignalStats:
    """Same idea as compute_signal_stats but sign-flipped: MORE incidents = worse."""
    stats = compute_signal_stats([float(w) for w in all_weeks], baseline_window, recent_window)
    return SignalStats(
        baseline_mean=stats.baseline_mean,
        baseline_std=stats.baseline_std,
        current_mean=stats.current_mean,
        z_score=round(-stats.z_score, 2),
        trend_slope=stats.trend_slope,
    )
