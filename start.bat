@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [.venv] Python do ambiente virtual nao encontrado.
    echo Crie o ambiente: python -m venv .venv
    echo Depois: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Installing dependencies (if needed)...
".\.venv\Scripts\python.exe" -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo Failed to install requirements in .venv.
    pause
    exit /b 1
)

echo Starting filemanager.backend...
start "" cmd /c "timeout /t 4 /nobreak >nul 2>&1 & start http://127.0.0.1:8000/swagger"
".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
