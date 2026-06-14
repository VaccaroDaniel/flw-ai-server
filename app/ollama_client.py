import json
import re
from typing import Any

import httpx

from app.config import Settings


class OllamaError(RuntimeError):
    pass


async def list_models(settings: Settings) -> list[str]:
    """Return locally available Ollama model names."""
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Could not connect to Ollama at {settings.ollama_base_url}: {exc}") from exc

    data = response.json()
    models = data.get("models", [])
    return [str(model.get("name", "")) for model in models if model.get("name")]


async def ensure_model_available(settings: Settings, model: str | None = None) -> str:
    """Validate that the selected Ollama model exists locally."""
    selected_model = model or settings.ollama_model
    models = await list_models(settings)
    if selected_model not in models:
        available = ", ".join(models) if models else "none"
        raise OllamaError(
            f"Ollama model '{selected_model}' is not installed. "
            f"Available models: {available}. Run: ollama pull {selected_model}"
        )
    return selected_model


def extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from an LLM response."""
    text = text.strip()
    if not text:
        raise OllamaError("Empty model response.")

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise OllamaError("Model response did not contain a JSON object.")

    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise OllamaError("Model response JSON was not an object.")
    return value


async def generate_json(settings: Settings, prompt: str, model: str | None = None) -> dict[str, Any]:
    selected_model = await ensure_model_available(settings, model)
    url = settings.ollama_base_url.rstrip("/") + "/api/generate"

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096,
        },
    }

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    data = response.json()
    model_text = data.get("response", "")
    parsed = extract_json(model_text)
    parsed["_ollama"] = {
        "model": selected_model,
        "done": data.get("done", False),
        "total_duration": data.get("total_duration"),
    }
    return parsed
