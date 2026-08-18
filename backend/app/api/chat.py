"""
The live demo flow: a student sends a message to the AI chatbot, it's stored
and classified immediately, the risk score is recomputed, and the result is
visible to a counsellor on the admin dashboard/review queue on their next
poll -- no separate "run analysis" step.

This endpoint always uses Gemini (services/gemini_client.py, Google AI
Studio's free tier), not the Hugging Face fallback -- it's the "natural
language, not template" path requested for the interactive demo. Requires
GEMINI_API_KEY. (The on-demand profile explanation in api/students.py is a
separate feature that still uses Claude -- see that file's docstring.)
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Conversation, RiskAssessment, Student, WeeklySignal
from app.schemas import ChatMessageIn, ChatMessageOut, RiskAssessmentOut
from app.services import evidence_fusion, gemini_client, safeguarding

router = APIRouter(prefix="/students", tags=["chat"])


@router.post("/{student_id}/messages", response_model=ChatMessageOut)
def send_message(student_id: str, message: ChatMessageIn, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    signals = (
        db.query(WeeklySignal)
        .filter(WeeklySignal.student_id == student_id)
        .order_by(WeeklySignal.week)
        .all()
    )
    conversations = (
        db.query(Conversation)
        .filter(Conversation.student_id == student_id)
        .order_by(Conversation.week)
        .all()
    )
    if not signals:
        raise HTTPException(status_code=400, detail="Student has no school-signal history yet (run scripts/seed_db.py)")

    try:
        classification = gemini_client.classify_and_score(message.text)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))  # e.g. no GEMINI_API_KEY

    # Live messages extend the timeline forward by one week. No new school data
    # arrived, so carry the last known attendance/academic/behavior forward --
    # this keeps the trend chart continuous and lets the conversation signal
    # alone move the score, which is exactly what this demo is meant to show.
    next_week = signals[-1].week + 1
    last = signals[-1]
    new_signal = WeeklySignal(
        student_id=student_id,
        week=next_week,
        attendance_pct=last.attendance_pct,
        academic_score=last.academic_score,
        behavior_incidents=0,
    )
    db.add(new_signal)

    new_conversation = Conversation(
        student_id=student_id,
        week=next_week,
        text=message.text,
        predicted_category=classification["category"],
        category_confidence=classification["confidence"],
        distress_score=classification["distress_score"],
    )
    db.add(new_conversation)

    attendance_series = [s.attendance_pct for s in signals] + [new_signal.attendance_pct]
    academic_series = [s.academic_score for s in signals] + [new_signal.academic_score]
    behavior_series = [s.behavior_incidents for s in signals] + [new_signal.behavior_incidents]
    distress_scores = [c.distress_score or 0.0 for c in conversations] + [new_conversation.distress_score]
    categories = [c.predicted_category or "none" for c in conversations] + [new_conversation.predicted_category]

    result = evidence_fusion.fuse(
        attendance_series=attendance_series,
        academic_series=academic_series,
        behavior_series=behavior_series,
        conversation_distress_scores=distress_scores,
        conversation_categories=categories,
    )
    routing = safeguarding.route(result.top_context, result.risk_state)

    recent_texts = [c.text for c in conversations[-4:]] + [message.text]
    explanation_is_ai = True
    try:
        explanation = gemini_client.generate_explanation(
            risk_state=result.risk_state,
            breakdown=result.breakdown,
            top_context=result.top_context,
            recent_snippets=recent_texts,
        )
    except Exception:
        explanation = f"Risk state: {result.risk_state} (score {result.risk_score})."
        explanation_is_ai = False

    new_assessment = RiskAssessment(
        student_id=student_id,
        week=next_week,
        risk_score=result.risk_score,
        risk_state=result.risk_state,
        top_context=result.top_context,
        breakdown_json=json.dumps(result.breakdown),
        explanation=explanation,
        explanation_ai_generated=1 if explanation_is_ai else 0,
        routing=routing,
        reviewed=0,
    )
    db.add(new_assessment)

    try:
        reply = gemini_client.chat_reply(message.text)
    except Exception:
        reply = "(chat reply unavailable -- check GEMINI_API_KEY)"

    db.commit()

    return ChatMessageOut(
        reply=reply,
        risk_assessment=RiskAssessmentOut(
            week=new_assessment.week,
            risk_score=new_assessment.risk_score,
            risk_state=new_assessment.risk_state,
            top_context=new_assessment.top_context,
            breakdown=result.breakdown,
            explanation=explanation,
            routing=routing,
            reviewed=False,
        ),
    )
