@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto :HaveVenv

call :FindPython
if defined PY_CMD goto :CreateVenv

echo Python was not found. Attempting to install Python 3.12 with winget...
where winget >nul 2>&1
if errorlevel 1 (
    echo winget is not available. Install Python 3.10+ from https://www.python.org/downloads/
    echo Enable the "Add python.exe to PATH" option, then run start.bat again.
    pause
    exit /b 1
)

winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo winget install failed or was cancelled. Install Python 3.10+ manually, then run start.bat again.
    pause
    exit /b 1
)

echo Waiting for the installer to finish registering files...
timeout /t 5 /nobreak >nul

call :FindPython
if not defined PY_CMD (
    echo Python is still not visible from this script. Close this window, open a new terminal, and run start.bat again.
    pause
    exit /b 1
)

:CreateVenv
echo Creating virtual environment .venv ...
"%PY_CMD%" -m venv .venv
if errorlevel 1 (
    echo Failed to create .venv. Try: "%PY_CMD%" -m venv .venv
    pause
    exit /b 1
)
echo .venv created.

:HaveVenv
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
exit /b 0

:FindPython
set "PY_CMD="
for /d %%d in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%d\python.exe" set "PY_CMD=%%d\python.exe"
)
if defined PY_CMD exit /b 0

for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PY_CMD=%%i"
if defined PY_CMD exit /b 0

for /f "delims=" %%i in ('where python 2^>nul') do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 if exist "%%i" (
        set "PY_CMD=%%i"
        exit /b 0
    )
)
exit /b 0
