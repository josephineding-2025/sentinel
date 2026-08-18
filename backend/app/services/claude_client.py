"""
Claude-powered replacements for the free offline pipeline, used specifically
where "natural, not templated" language actually matters to a human reader:

- classify_and_score() -- context classification + distress score for ONE
  conversation message, used by the live chat demo (api/chat.py)
- generate_explanation() -- the "why was this flagged" paragraph shown to a
  counsellor, used on-demand when a student profile is opened
- chat_reply() -- the student-facing AI chatbot reply for the demo chat UI

scripts/seed_db.py still classifies the bulk synthetic dataset (1700+
messages) with the free Hugging Face / keyword pipeline in
services/context_classifier.py + services/emotion.py -- that's already
validated by scripts/evaluate.py and costs nothing to re-run. Claude is
reserved for the interactive paths above, where a handful of calls per
counsellor session is negligible cost but the natural-language quality
genuinely matters (see the tech-stack discussion: cheap bulk pipeline +
Claude only where a human reads the output).

Every function requires ANTHROPIC_API_KEY (see .env.example) and raises if
it's missing -- callers are expected to fall back to the free pipeline where
a fallback makes sense (api/students.py), or surface a clear error where it
doesn't (api/chat.py, which IS the "use Claude" demo path).
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from app.config import ANTHROPIC_API_KEY

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")  # cheaper than Opus, plenty for this task

CATEGORIES = ["academic", "peer_social", "bullying", "family_conflict", "isolation_distress", "none"]

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "confidence": {"type": "number"},
        "distress_score": {"type": "number"},
    },
    "required": ["category", "confidence", "distress_score"],
    "additionalProperties": False,
}

CLASSIFY_SYSTEM = """You label a single message from a student's conversation with a government-provided AI study assistant, for a wellbeing early-detection system (Report Section 6, 13).

category: the single most relevant potential contributing context: academic | peer_social | bullying | family_conflict | isolation_distress | none. Use "none" for purely academic-task requests (e.g. "explain recursion") with no personal/emotional content.
confidence: 0-1, how confident you are in that category.
distress_score: 0-1, how much this message reflects hopelessness, withdrawal, or emotional distress (Section 6 "linguistic patterns") -- NOT how negative the topic is. A student calmly describing a conflict scores lower than a student expressing hopelessness about anything.

You are producing one weak signal among several the system fuses (Section 4: "no single signal is treated as truth"). You are not diagnosing."""


@lru_cache(maxsize=1)
def _client():
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set (see .env.example)")
    import anthropic
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def classify_and_score(text: str) -> dict:
    """Returns {"category": str, "confidence": float, "distress_score": float}."""
    response = _client().messages.create(
        model=MODEL,
        max_tokens=300,
        system=CLASSIFY_SYSTEM,
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": CLASSIFY_SCHEMA},
        },
        messages=[{"role": "user", "content": text}],
    )
    block = next(b for b in response.content if b.type == "text")
    return json.loads(block.text)


EXPLAIN_SYSTEM = """You write a short, plain-language explanation for a school counsellor of why a student's wellbeing risk score is what it is (Report Section 4, 10). Ground every sentence in the evidence given -- do not invent details, do not diagnose, do not speculate beyond what the numbers and conversation snippets show. 2-4 sentences, no clinical/diagnostic language."""


def generate_explanation(
    risk_state: str,
    breakdown: dict,
    top_context: str | None,
    recent_snippets: list[str],
) -> str:
    evidence = (
        f"risk_state: {risk_state}\n"
        f"signal contributions (higher = more concerning): {breakdown}\n"
        f"most frequent recent context: {top_context or 'none'}\n"
        f"recent conversation snippets: {recent_snippets[-5:]}"
    )
    response = _client().messages.create(
        model=MODEL,
        max_tokens=300,
        system=EXPLAIN_SYSTEM,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": evidence}],
    )
    return next(b.text for b in response.content if b.type == "text")


CHAT_SYSTEM = """You are the AI study assistant built into a student's government-issued education account. Help with schoolwork and chat naturally, like a friendly, low-key AI tutor. You are not a therapist and do not diagnose -- if a student shares something heavy, respond with brief, genuine warmth, then keep being helpful. Keep replies short (1-4 sentences) and conversational."""


def chat_reply(text: str) -> str:
    response = _client().messages.create(
        model=MODEL,
        max_tokens=400,
        system=CHAT_SYSTEM,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": text}],
    )
    return next(b.text for b in response.content if b.type == "text")
