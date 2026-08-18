import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Conversation, RiskAssessment, Student, WeeklySignal
from app.schemas import ConversationOut, RiskAssessmentOut, StudentDetail, StudentSummary, WeeklySignalOut
from app.services import explain

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentSummary])
def list_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    summaries = []
    for student in students:
        latest = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.student_id == student.student_id)
            .order_by(RiskAssessment.week.desc())
            .first()
        )
        if not latest:
            continue
        summaries.append(StudentSummary(
            student_id=student.student_id,
            latest_risk_state=latest.risk_state,
            latest_risk_score=latest.risk_score,
            latest_top_context=latest.top_context,
        ))

    order = {"high_priority": 0, "potential_concern": 1, "insufficient_evidence": 2, "no_concern": 3}
    summaries.sort(key=lambda s: order.get(s.latest_risk_state, 9))
    return summaries


@router.get("/{student_id}", response_model=StudentDetail)
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    signals = (
        db.query(WeeklySignal)
        .filter(WeeklySignal.student_id == student_id)
        .order_by(WeeklySignal.week)
        .all()
    )
    assessments = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.student_id == student_id)
        .order_by(RiskAssessment.week)
        .all()
    )
    conversations = (
        db.query(Conversation)
        .filter(Conversation.student_id == student_id)
        .order_by(Conversation.week)
        .all()
    )

    # Upgrade the LATEST assessment to a real Gemini/Claude explanation, cached
    # on first view (see services/explain.py) -- only the latest week, since
    # that's the only one actually shown prominently in the UI, and only ever
    # a real API call once per assessment.
    if assessments:
        explain.get_or_generate_explanation(db, assessments[-1], conversations)

    return StudentDetail(
        student_id=student_id,
        weekly_signals=[WeeklySignalOut.model_validate(s) for s in signals],
        risk_assessments=[
            RiskAssessmentOut(
                week=a.week,
                risk_score=a.risk_score,
                risk_state=a.risk_state,
                top_context=a.top_context,
                breakdown=json.loads(a.breakdown_json) if a.breakdown_json else {},
                explanation=a.explanation or "",
                routing=a.routing or "no_routing_needed",
                reviewed=bool(a.reviewed),
            )
            for a in assessments
        ],
        conversations=[ConversationOut.model_validate(c) for c in conversations],
    )
