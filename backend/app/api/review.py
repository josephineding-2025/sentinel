from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Conversation, RiskAssessment
from app.schemas import ReviewAction
from app.services import explain

router = APIRouter(prefix="/review", tags=["review"])

# Cap how many generation ATTEMPTS happen per request -- not successes.
# The queue can hold a dozen+ flagged students the first time it's ever
# loaded; generating all of them in one request bursts past Gemini's free-tier
# rate limit (20 requests/minute) in a single HTTP call. Counting only
# successes (the original version of this cap) meant that during a rate-limit
# window every attempt failed, the counter never advanced, and EVERY item was
# retried on EVERY 5-second poll -- a retry storm that kept re-triggering the
# 429 and never let the window clear. Counting attempts means at most 1 new
# call goes out per poll regardless of outcome, so a rate-limited window
# actually gets a chance to recover.
MAX_ATTEMPTS_PER_REQUEST = 1


@router.get("/queue")
def review_queue(db: Session = Depends(get_db)):
    """Human-in-the-loop queue: unreviewed potential/high-priority cases, most urgent first."""
    items = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.risk_state.in_(["potential_concern", "high_priority"]))
        .filter(RiskAssessment.reviewed == 0)
        .order_by(RiskAssessment.risk_score.desc())
        .all()
    )
    # Only the latest week per student is actionable
    latest_by_student = {}
    for item in items:
        existing = latest_by_student.get(item.student_id)
        if not existing or item.week > existing.week:
            latest_by_student[item.student_id] = item

    result = []
    attempts_this_request = 0
    for a in sorted(latest_by_student.values(), key=lambda a: a.risk_score, reverse=True):
        if a.explanation_ai_generated:
            explanation = a.explanation or ""  # already cached, free to read every time
        elif attempts_this_request < MAX_ATTEMPTS_PER_REQUEST:
            conversations = (
                db.query(Conversation)
                .filter(Conversation.student_id == a.student_id)
                .order_by(Conversation.week)
                .all()
            )
            attempts_this_request += 1  # count the attempt regardless of outcome
            explanation = explain.get_or_generate_explanation(db, a, conversations)
        else:
            explanation = a.explanation or ""  # still template -- will try again on a later poll

        result.append({
            "student_id": a.student_id,
            "week": a.week,
            "risk_score": a.risk_score,
            "risk_state": a.risk_state,
            "top_context": a.top_context,
            "explanation": explanation,
            "routing": a.routing or "no_routing_needed",
        })
    return result


@router.post("/{student_id}/{week}")
def mark_reviewed(student_id: str, week: int, action: ReviewAction, db: Session = Depends(get_db)):
    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.student_id == student_id, RiskAssessment.week == week)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    assessment.reviewed = 1 if action.reviewed else 0
    db.commit()
    return {"ok": True}
