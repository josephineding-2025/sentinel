from pydantic import BaseModel


class WeeklySignalOut(BaseModel):
    week: int
    attendance_pct: float
    academic_score: float
    behavior_incidents: int

    class Config:
        from_attributes = True


class RiskAssessmentOut(BaseModel):
    week: int
    risk_score: float
    risk_state: str
    top_context: str | None
    breakdown: dict[str, float]
    explanation: str
    routing: str
    reviewed: bool

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    week: int
    text: str
    predicted_category: str | None
    category_confidence: float | None
    distress_score: float | None

    class Config:
        from_attributes = True


class StudentSummary(BaseModel):
    student_id: str
    latest_risk_state: str
    latest_risk_score: float
    latest_top_context: str | None


class StudentDetail(BaseModel):
    student_id: str
    weekly_signals: list[WeeklySignalOut]
    risk_assessments: list[RiskAssessmentOut]
    conversations: list[ConversationOut]


class ReviewAction(BaseModel):
    reviewed: bool


class ChatMessageIn(BaseModel):
    text: str


class ChatMessageOut(BaseModel):
    reply: str
    risk_assessment: RiskAssessmentOut
