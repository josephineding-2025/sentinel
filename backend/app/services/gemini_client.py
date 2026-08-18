"""
Gemini-powered version of claude_client.py, used for the live Student Chat
demo so it runs entirely on Google AI Studio's free tier instead of a paid
Claude API key.

Mirrors claude_client.py's three functions exactly (classify_and_score,
generate_explanation, chat_reply) so backend/app/api/chat.py can import
either module interchangeably. services/explain.py's
get_or_generate_explanation() -- used by both the student profile page and
the Review Queue -- also prefers this module first, falling back to
claude_client.py only if ANTHROPIC_API_KEY happens to be set too, and to a
free static template if neither key is configured.

Requires GEMINI_API_KEY (see .env.example) -- get one free at
https://aistudio.google.com/apikey. Every function raises if it's missing.

Uses the `google-genai` SDK's Interactions API (client.interactions.create),
which is Google's current (2026) Python interface for the Gemini API.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from app.config import GEMINI_API_KEY

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")  # generous free-tier quota

CATEGORIES = ["academic", "peer_social", "bullying", "family_conflict", "isolation_distress", "none"]

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "confidence": {"type": "number"},
        "distress_score": {"type": "number"},
    },
    "required": ["category", "confidence", "distress_score"],
}

CLASSIFY_SYSTEM = """You label a single message from a student's conversation with a government-provided AI study assistant, for a wellbeing early-detection system (Report Section 6, 13).

category: the single most relevant potential contributing context: academic | peer_social | bullying | family_conflict | isolation_distress | none. Use "none" for purely academic-task requests (e.g. "explain recursion") with no personal/emotional content.
confidence: 0-1, how confident you are in that category.
distress_score: 0-1, how much this message reflects hopelessness, withdrawal, or emotional distress (Section 6 "linguistic patterns") -- NOT how negative the topic is. A student calmly describing a conflict scores lower than a student expressing hopelessness about anything.

You are producing one weak signal among several the system fuses (Section 4: "no single signal is treated as truth"). You are not diagnosing."""


@lru_cache(maxsize=1)
def _client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set (see .env.example) -- get a free key at https://aistudio.google.com/apikey")
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def classify_and_score(text: str) -> dict:
    """Returns {"category": str, "confidence": float, "distress_score": float}."""
    interaction = _client().interactions.create(
        model=MODEL,
        system_instruction=CLASSIFY_SYSTEM,
        input=text,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": CLASSIFY_SCHEMA,
        },
    )
    return json.loads(interaction.output_text)


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
    interaction = _client().interactions.create(
        model=MODEL,
        system_instruction=EXPLAIN_SYSTEM,
        input=evidence,
    )
    return interaction.output_text


CHAT_SYSTEM = """You are the AI study assistant built into a student's government-issued education account. Help with schoolwork and chat naturally, like a friendly, low-key AI tutor. You are not a therapist and do not diagnose -- if a student shares something heavy, respond with brief, genuine warmth, then keep being helpful. Keep replies short (1-4 sentences) and conversational."""


def chat_reply(text: str) -> str:
    interaction = _client().interactions.create(
        model=MODEL,
        system_instruction=CHAT_SYSTEM,
        input=text,
    )
    return interaction.output_text
