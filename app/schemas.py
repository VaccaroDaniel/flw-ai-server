from typing import Any
from pydantic import BaseModel, Field


class WritingEstimateRequest(BaseModel):
    userid: int = 0
    courseid: int = 0
    cmid: int = 0
    submissionid: int = 0
    model: str | None = None
    prompt: str | None = None
    text: str = ""


class SpeakingEstimateRequest(BaseModel):
    userid: int = 0
    courseid: int = 0
    cmid: int = 0
    submissionid: int = 0
    model: str | None = None
    prompt: str | None = None
    transcript: str = ""
    audio_path: str | None = None


class EstimateResponse(BaseModel):
    cefr_level: str
    total_score: float
    rubric: dict[str, float | int | str] = Field(default_factory=dict)
    weak_kps: list[str] = Field(default_factory=list)
    recommended_lessons: list[str] = Field(default_factory=list)
    teacher_note: str = ""
    scoring_mode: str = "mock"
    raw_model_response: dict[str, Any] | None = None


class RoleWaiterRequest(BaseModel):
    userid: int = 0
    courseid: int = 0
    cmid: int = 0
    model: str | None = None
    character: str = "Waiter"
    role: str = "Cafe waiter"
    scenario: str = ""
    cefr_level: str = "A1"
    current_line: str = ""
    learner_reply: str = ""
    history: str = ""


class RoleWaiterResponse(BaseModel):
    line: str
    intent: str = ""
    raw_model_response: dict[str, Any] | None = None
