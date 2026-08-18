from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, unique=True, index=True, nullable=False)

    weekly_signals = relationship("WeeklySignal", back_populates="student", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="student", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="student", cascade="all, delete-orphan")


class WeeklySignal(Base):
    """School-side longitudinal data: attendance, academic score, behaviour incidents (Section 5)."""
    __tablename__ = "weekly_signals"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey("students.student_id"), index=True, nullable=False)
    week = Column(Integer, nullable=False)
    attendance_pct = Column(Float, nullable=False)
    academic_score = Column(Float, nullable=False)
    behavior_incidents = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="weekly_signals")


class Conversation(Base):
    """A single AI-conversation snippet, plus derived (not raw-exposed) signals (Section 16)."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey("students.student_id"), index=True, nullable=False)
    week = Column(Integer, nullable=False)
    text = Column(String, nullable=False)

    # Derived signals filled in by services/context_classifier.py + services/emotion.py
    predicted_category = Column(String, nullable=True)
    category_confidence = Column(Float, nullable=True)
    distress_score = Column(Float, nullable=True)

    student = relationship("Student", back_populates="conversations")


class RiskAssessment(Base):
    """One fused risk assessment per student per week (Section 10, 14)."""
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey("students.student_id"), index=True, nullable=False)
    week = Column(Integer, nullable=False)

    risk_score = Column(Float, nullable=False)
    risk_state = Column(String, nullable=False)  # no_concern | insufficient_evidence | potential_concern | high_priority
    top_context = Column(String, nullable=True)  # e.g. "academic", "peer_social", "family_conflict"

    # JSON-encoded per-signal contribution dict from evidence_fusion.fuse() --
    # the "reason for the score" the counsellor-facing detail view explains.
    breakdown_json = Column(String, nullable=True)
    # Plain-language version of breakdown_json. Starts as the free template
    # from services/explain.py, then gets upgraded to a real Gemini/Claude
    # explanation (and cached here, see get_or_generate_explanation below)
    # the first time anyone actually looks at this assessment.
    explanation = Column(String, nullable=True)
    explanation_ai_generated = Column(Integer, default=0)  # 0 = template, 1 = real LLM call
    # Who should review, from services/safeguarding.py (Section 15).
    routing = Column(String, nullable=True)

    reviewed = Column(Integer, default=0)  # 0/1 — human-in-the-loop flag (Section 18)

    student = relationship("Student", back_populates="risk_assessments")
