@echo off
setlocal
cd /d "%~dp0"

set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

if not exist ".venv\Scripts\python.exe" (
    echo Python virtual environment was not found.
    echo Expected: %cd%\.venv\Scripts\python.exe
    pause
    exit /b 1
)

echo Starting FLW Local AI Scoring Server...
echo API URL: http://127.0.0.1:8000
echo Whisper offline mode: enabled
echo.

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
