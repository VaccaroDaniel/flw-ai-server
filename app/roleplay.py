from __future__ import annotations

from app.config import Settings
from app.ollama_client import generate_json
from app.schemas import RoleWaiterRequest, RoleWaiterResponse


def build_role_waiter_prompt(request: RoleWaiterRequest) -> str:
    return f"""You are a friendly local AI role character for FLW language practice.

Return only JSON:
{{
  "line": "one short natural reply from the character",
  "intent": "short teaching intent"
}}

Rules:
- Stay in character as {request.character}, {request.role}.
- Scenario: {request.scenario}
- Learner CEFR level: {request.cefr_level}
- Keep the line short, practical, and speakable for the learner level.
- Ask one clear follow-up question or give one short natural response.
- Do not explain grammar.
- Do not mention that you are an AI.

Conversation history:
{request.history}

Current character line:
{request.current_line}

Learner reply:
{request.learner_reply}
"""


def mock_role_waiter(request: RoleWaiterRequest) -> RoleWaiterResponse:
    reply = request.learner_reply.lower()
    if "coffee" in reply or "tea" in reply:
        line = "Sure. Would you like anything else?"
    elif "yes" in reply:
        line = "Great. Anything to drink?"
    else:
        line = "Thank you. Can you say that one more time, please?"

    return RoleWaiterResponse(line=line, intent="mock follow-up")


async def generate_role_waiter(request: RoleWaiterRequest, settings: Settings) -> RoleWaiterResponse:
    if settings.scoring_mode.lower() != "ollama":
        return mock_role_waiter(request)

    raw = await generate_json(settings, build_role_waiter_prompt(request), request.model)
    line = str(raw.get("line") or raw.get("next_line") or "").strip()
    if not line:
        line = "Thank you. Would you like anything else?"

    return RoleWaiterResponse(
        line=line,
        intent=str(raw.get("intent") or ""),
        raw_model_response=raw,
    )
