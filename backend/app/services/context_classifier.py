"""
Context classification (Report Section 13): given a conversation snippet,
which potential contributing factor does it most resemble?
    academic | peer_social | bullying | family_conflict | isolation_distress | none

Uses a zero-shot Hugging Face model (no training data required, no API key,
no ongoing cost) — see the "Zero-shot context classification" row in the
tech-stack discussion. Falls back to a simple keyword matcher if
transformers/torch aren't installed yet, so the rest of the app still runs
while you're setting things up.

Model: MoritzLaurer/deberta-v3-base-zeroshot-v2.0 (~184M params, CPU-friendly)
"""
from __future__ import annotations

from functools import lru_cache

LABELS = ["academic", "peer_social", "bullying", "family_conflict", "isolation_distress", "none"]

_KEYWORD_FALLBACK = {
    "academic": ["exam", "grade", "study", "fail", "test", "homework", "assignment"],
    "peer_social": ["friend", "group project", "left out", "lunch", "hang out"],
    "bullying": ["bully", "making fun", "laugh at me", "picking on"],
    "family_conflict": ["parents", "family", "home", "fighting"],
    "isolation_distress": ["alone", "empty", "tired", "burden", "nothing matters", "don't feel like"],
}


@lru_cache(maxsize=1)
def _get_pipeline():
    from transformers import pipeline
    return pipeline("zero-shot-classification", model="MoritzLaurer/deberta-v3-base-zeroshot-v2.0")


def _keyword_fallback(text: str) -> tuple[str, float]:
    text_lower = text.lower()
    for category, keywords in _KEYWORD_FALLBACK.items():
        if any(kw in text_lower for kw in keywords):
            return category, 0.6  # fixed, low-confidence score — this is a fallback, not the real model
    return "none", 0.5


def classify_context(text: str) -> tuple[str, float]:
    """Returns (predicted_category, confidence)."""
    try:
        classifier = _get_pipeline()
    except Exception:
        return _keyword_fallback(text)

    result = classifier(text, candidate_labels=LABELS, multi_label=False)
    top_label = result["labels"][0]
    top_score = float(result["scores"][0])
    return top_label, round(top_score, 3)
