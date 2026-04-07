@echo off
cd /d "%~dp0"

echo Installing dependencies (if needed)...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo Failed to install requirements. Check Python is on PATH.
    pause
    exit /b 1
)

echo Starting filemanager.backend...
start "" cmd /c "timeout /t 4 /nobreak >nul 2>&1 & start http://127.0.0.1:8000/swagger"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
