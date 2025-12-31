@echo off
TITLE Medical ASR - Local Auto-Launcher

:: --- CONFIGURATION ---
set VENV_PATH=.\venv\Scripts\activate.bat
set FRONTEND_SCRIPT=2_asr_pipeline.py
set SETUP_SCRIPT=setup_models.py

:: 1. CHECK VENV
if not exist "%VENV_PATH%" (
    echo [ERROR] Virtual Environment not found! 
    echo Please run the installation commands first.
    pause
    exit /b
)

:: 2. AUTO-SETUP (Fixes the missing file error automatically)
if not exist "vibert_pipeline\gec_model.py" (
    echo [SETUP] Critical files missing. Running setup script first...
    echo -----------------------------------------------------------
    call %VENV_PATH%
    cd vibert_pipeline
    python %SETUP_SCRIPT%
    cd ..
    echo -----------------------------------------------------------
    echo [SETUP] Setup complete.
    echo.
)

:: 3. START BACKEND (API)
echo [1/4] Starting ASR Backend (Port 8000)...
:: We assume your api.py is inside medical_api folder
start "ASR API (Backend)" cmd /k "call %VENV_PATH% && cd medical_api && set MODEL_DIR=..\models && uvicorn api:app --host 0.0.0.0 --port 8000"

:: 4. START FRONTEND (Gradio)
echo [2/4] Starting Pipeline Interface (Port 7860)...
start "ASR Frontend" cmd /k "call %VENV_PATH% && cd vibert_pipeline && set ASR_PORT=8000 && python %FRONTEND_SCRIPT%"

:: 5. OPEN BROWSER
echo [3/4] Waiting 10 seconds for servers to boot...
timeout /t 10 /nobreak >nul

echo [4/4] Opening Web Browser...
start http://127.0.0.1:7860

echo.
echo ==================================================
echo   SYSTEM IS RUNNING
echo   You can close this window to stop everything.
echo ==================================================
pause