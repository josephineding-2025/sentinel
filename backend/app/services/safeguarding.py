"""
Safeguarding routing (Report Section 15): if a potential concern's top
context is family-related, the system must NOT auto-notify the parent --
it has to route to a human reviewer who decides whether the caregiver may be
part of the concern.

This is intentionally a simple, visible rule, not a model. Who receives
sensitive information should never be an autonomous AI decision.
"""

FAMILY_RELATED_CONTEXTS = {"family_conflict"}


def route(top_context: str | None, risk_state: str) -> str:
    """Returns a routing label describing WHO should review, not an automatic action."""
    if risk_state not in ("potential_concern", "high_priority"):
        return "no_routing_needed"

    if top_context in FAMILY_RELATED_CONTEXTS:
        return "safeguarding_pathway"  # human must assess whether caregiver can safely be involved

    return "normal_pathway"  # counsellor reviews directly
