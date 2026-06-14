from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import get_settings
from app.ollama_client import OllamaError, list_models
from app.schemas import EstimateResponse, SpeakingEstimateRequest, WritingEstimateRequest
from app.scoring import score_speaking, score_writing
from app.transcription import TranscriptionError, transcribe_audio_bytes

app = FastAPI(
    title="FLW Local AI Scoring Server",
    version="0.1.0",
    description="Offline scoring API for Moodle FLW speaking and writing estimation.",
)


@app.get("/health")
async def health() -> dict[str, str | int]:
    settings = get_settings()
    return {
        "status": "ok",
        "scoring_mode": settings.scoring_mode,
        "ollama_base_url": settings.ollama_base_url,
        "request_timeout_seconds": settings.request_timeout_seconds,
        "whisper_backend": settings.whisper_backend,
        "whisper_model": settings.whisper_model,
    }


@app.get("/health/ollama")
async def ollama_health() -> dict[str, str | list[str]]:
    settings = get_settings()
    try:
        models = await list_models(settings)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    selected = settings.ollama_model
    return {
        "status": "ok" if selected in models else "missing_model",
        "ollama_base_url": settings.ollama_base_url,
        "selected_model": selected,
        "available_models": models,
    }


@app.post("/estimate/writing", response_model=EstimateResponse)
async def estimate_writing(request: WritingEstimateRequest) -> EstimateResponse:
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Writing text is required.")

    try:
        return await score_writing(request, get_settings())
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/estimate/speaking", response_model=EstimateResponse)
async def estimate_speaking(request: SpeakingEstimateRequest) -> EstimateResponse:
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="Speaking transcript is required.")

    try:
        return await score_speaking(request, get_settings())
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/transcribe/audio")
async def transcribe_audio(file: UploadFile = File(...)) -> dict[str, str]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Audio file is required.")

    try:
        return await transcribe_audio_bytes(get_settings(), file.filename or "audio.webm", content)
    except TranscriptionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
