from __future__ import annotations

from typing import Any

from app.config import Settings
from app.ollama_client import generate_json
from app.prompts import SPEAKING_SYSTEM_PROMPT, WRITING_SYSTEM_PROMPT
from app.schemas import EstimateResponse, SpeakingEstimateRequest, WritingEstimateRequest


def normalize_response(data: dict[str, Any], scoring_mode: str) -> EstimateResponse:
    weak_kps = data.get("weak_kps") or data.get("weak_knowledge_points") or []
    recommendations = data.get("recommended_lessons") or data.get("recommendations") or []

    if isinstance(weak_kps, str):
        weak_kps = [weak_kps]
    if isinstance(recommendations, str):
        recommendations = [recommendations]

    return EstimateResponse(
        cefr_level=str(data.get("cefr_level") or data.get("cefrlevel") or "A1"),
        total_score=float(data.get("total_score") or data.get("totalscore") or 0),
        rubric=data.get("rubric") if isinstance(data.get("rubric"), dict) else {},
        weak_kps=[str(item) for item in weak_kps],
        recommended_lessons=[str(item) for item in recommendations],
        teacher_note=str(data.get("teacher_note") or ""),
        scoring_mode=scoring_mode,
        raw_model_response=data,
    )


def mock_writing_score(text: str) -> EstimateResponse:
    words = [word for word in text.replace("\n", " ").split(" ") if word.strip()]
    word_count = len(words)

    if word_count < 20:
        level = "A1"
        score = 7
    elif word_count < 60:
        level = "A2"
        score = 11
    elif word_count < 120:
        level = "B1"
        score = 15
    else:
        level = "B2"
        score = 18

    return EstimateResponse(
        cefr_level=level,
        total_score=score,
        rubric={
            "task_achievement": min(4, max(1, word_count // 30 + 1)),
            "grammar": 2,
            "vocabulary": 2,
            "coherence": 2,
            "mechanics": 2,
        },
        weak_kps=["sentence accuracy", "vocabulary range", "linking ideas"],
        recommended_lessons=[
            f"{level} Writing: sentence control",
            f"{level} Grammar: common verb forms",
        ],
        teacher_note="Mock estimate for Moodle integration testing. Use Ollama mode for real scoring.",
        scoring_mode="mock",
    )


def mock_speaking_score(transcript: str) -> EstimateResponse:
    words = [word for word in transcript.replace("\n", " ").split(" ") if word.strip()]
    word_count = len(words)

    if word_count < 15:
        level = "A1"
        score = 6
    elif word_count < 50:
        level = "A2"
        score = 10
    elif word_count < 100:
        level = "B1"
        score = 14
    else:
        level = "B2"
        score = 17

    return EstimateResponse(
        cefr_level=level,
        total_score=score,
        rubric={
            "task_completion": min(4, max(1, word_count // 25 + 1)),
            "fluency": 2,
            "grammar": 2,
            "vocabulary": 2,
            "pronunciation_proxy": 1,
        },
        weak_kps=["spoken sentence building", "fluency", "pronunciation evidence"],
        recommended_lessons=[
            f"{level} Speaking: guided answers",
            f"{level} Pronunciation: rhythm and stress",
        ],
        teacher_note="Mock estimate based on transcript length only. Add Whisper metrics for pronunciation and fluency.",
        scoring_mode="mock",
    )


def build_writing_prompt(request: WritingEstimateRequest) -> str:
    return f"""{WRITING_SYSTEM_PROMPT}

Moodle context:
- userid: {request.userid}
- courseid: {request.courseid}
- cmid: {request.cmid}
- submissionid: {request.submissionid}

Teacher prompt:
{request.prompt or ""}

Learner writing:
{request.text}
"""


def build_speaking_prompt(request: SpeakingEstimateRequest) -> str:
    return f"""{SPEAKING_SYSTEM_PROMPT}

Moodle context:
- userid: {request.userid}
- courseid: {request.courseid}
- cmid: {request.cmid}
- submissionid: {request.submissionid}

Teacher prompt:
{request.prompt or ""}

Learner transcript:
{request.transcript}
"""


async def score_writing(request: WritingEstimateRequest, settings: Settings) -> EstimateResponse:
    if settings.scoring_mode.lower() == "ollama":
        raw = await generate_json(settings, build_writing_prompt(request), request.model)
        return normalize_response(raw, "ollama")
    return mock_writing_score(request.text)


async def score_speaking(request: SpeakingEstimateRequest, settings: Settings) -> EstimateResponse:
    if settings.scoring_mode.lower() == "ollama":
        raw = await generate_json(settings, build_speaking_prompt(request), request.model)
        return normalize_response(raw, "ollama")
    return mock_speaking_score(request.transcript)
