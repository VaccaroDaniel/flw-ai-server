# FLW Local AI Scoring Server

This is the offline scoring API used by Moodle plugin `local_flwaiassessment`.

It exposes:

- `GET /health`
- `POST /estimate/writing`
- `POST /estimate/speaking`

The server has two scoring modes:

- `mock`: returns simple test estimates so Moodle integration can be tested immediately.
- `ollama`: sends prompts to a local Ollama model and expects JSON scoring output.

## Setup

```powershell
cd D:\Dev\MoodleWindowsInstaller-latest-501\server\flw-ai-server
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

If `py` is not available, install Python 3.11+ or use the Python executable available on your machine.

## Moodle Settings

In Moodle, keep:

```text
Local scoring API URL: http://127.0.0.1:8000
Enable scheduled AI processing: enabled only after the server is running
```

## Ollama Mode

Install Ollama and pull a model:

```powershell
ollama pull qwen2.5:7b
```

Then edit `.env`:

```text
FLW_SCORING_MODE=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
```

Restart the server after changing `.env`.

Check model readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/ollama
```

## Example Test

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/estimate/writing `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"userid":1,"text":"My name is Sara. I am from Japan. I like music and English."}'
```

## Speaking Roadmap

The current speaking endpoint scores a transcript. The next step is to add:

- `POST /transcribe/audio`
- Whisper or Whisper.cpp integration
- speaking metrics such as words per minute, pause length, and hesitation count
