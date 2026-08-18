"""
Distress/emotion signal extraction (Report Section 6: "linguistic patterns" —
hopelessness-related expressions, negative language, etc).

Model: SamLowe/roberta-base-go_emotions (27 fine-grained emotions, ~125M params).
We collapse it down to a single 0-1 "distress_score" by summing the
probability mass on emotions associated with the report's risk language
(grief, nervousness, sadness, remorse, disappointment, fear).

Falls back to a tiny keyword heuristic if transformers/torch aren't
installed yet, same reasoning as context_classifier.py.
"""
from __future__ import annotations

from functools import lru_cache

DISTRESS_EMOTIONS = {"grief", "nervousness", "sadness", "remorse", "disappointment", "fear", "embarrassment"}

_DISTRESS_KEYWORDS = ["tired", "empty", "burden", "nothing matters", "alone", "don't feel", "hopeless", "worthless"]


def _keyword_fallback(text: str) -> float:
    text_lower = text.lower()
    hits = sum(1 for kw in _DISTRESS_KEYWORDS if kw in text_lower)
    return min(1.0, hits * 0.35)


@lru_cache(maxsize=1)
def _get_pipeline():
    from transformers import pipeline
    return pipeline(
        "text-classification",
        model="SamLowe/roberta-base-go_emotions",
        top_k=None,  # return scores for all 27 emotions
    )


def distress_score(text: str) -> float:
    """Returns a 0-1 distress score, higher = more concerning."""
    try:
        classifier = _get_pipeline()
    except Exception:
        return _keyword_fallback(text)

    predictions = classifier(text)[0]  # list of {"label": ..., "score": ...}
    score = sum(p["score"] for p in predictions if p["label"] in DISTRESS_EMOTIONS)
    return round(min(1.0, score), 3)
