import asyncio
import shlex
import tempfile
from functools import lru_cache
from pathlib import Path

from app.config import Settings


class TranscriptionError(RuntimeError):
    pass


async def transcribe_audio_bytes(settings: Settings, filename: str, content: bytes) -> dict[str, str]:
    """Transcribe an uploaded audio file with the configured local backend."""
    backend = settings.whisper_backend.strip().lower()
    if backend == "faster_whisper":
        return await asyncio.to_thread(_transcribe_with_faster_whisper, settings, filename, content)
    if backend == "command":
        return await _transcribe_with_command(settings, filename, content)
    raise TranscriptionError(
        "Whisper transcription is not configured. Set WHISPER_BACKEND=faster_whisper or WHISPER_BACKEND=command."
    )


@lru_cache(maxsize=2)
def _load_faster_whisper_model(model_name: str, device: str, compute_type: str, local_files_only: bool):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise TranscriptionError("faster-whisper is not installed. Run pip install -r requirements.txt.") from exc

    return WhisperModel(model_name, device=device, compute_type=compute_type, local_files_only=local_files_only)


def _transcribe_with_faster_whisper(settings: Settings, filename: str, content: bytes) -> dict[str, str]:
    suffix = Path(filename or "audio.webm").suffix or ".webm"
    with tempfile.TemporaryDirectory(prefix="flw-audio-") as tempdir:
        audio_path = Path(tempdir) / f"input{suffix}"
        audio_path.write_bytes(content)

        model = _load_faster_whisper_model(
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
            settings.whisper_local_files_only,
        )

        try:
            segments, info = model.transcribe(str(audio_path), beam_size=5)
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            raise TranscriptionError(str(exc)) from exc

        if not transcript:
            raise TranscriptionError(
                "No speech was detected. Please record again, speak clearly, and make the recording at least 3 seconds long."
            )

        return {
            "transcript": transcript,
            "filename": filename,
            "backend": "faster_whisper",
            "model": settings.whisper_model,
            "local_files_only": str(settings.whisper_local_files_only).lower(),
            "language": info.language or "",
        }


async def _transcribe_with_command(settings: Settings, filename: str, content: bytes) -> dict[str, str]:
    """Transcribe an uploaded audio file with a configured local command."""
    if not settings.whisper_command.strip():
        raise TranscriptionError(
            "Whisper transcription is not configured. Set WHISPER_COMMAND in .env."
        )

    suffix = Path(filename or "audio.webm").suffix or ".webm"
    with tempfile.TemporaryDirectory(prefix="flw-audio-") as tempdir:
        audio_path = Path(tempdir) / f"input{suffix}"
        output_path = Path(tempdir) / "transcript.txt"
        audio_path.write_bytes(content)

        command = [
            part.format(input=str(audio_path), output=str(output_path))
            for part in shlex.split(settings.whisper_command)
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=settings.request_timeout_seconds,
        )

        if process.returncode != 0:
            message = stderr.decode("utf-8", errors="replace") or stdout.decode("utf-8", errors="replace")
            raise TranscriptionError(message.strip() or "Whisper command failed.")

        if output_path.exists():
            transcript = output_path.read_text(encoding="utf-8", errors="replace").strip()
        else:
            transcript = stdout.decode("utf-8", errors="replace").strip()

        if not transcript:
            raise TranscriptionError(
                "No speech was detected. Please record again, speak clearly, and make the recording at least 3 seconds long."
            )

        return {
            "transcript": transcript,
            "filename": filename,
            "backend": "command",
        }
