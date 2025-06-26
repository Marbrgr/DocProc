@echo off
echo Starting DocuMind AI - Full Stack Application
echo ==========================================
echo.
echo This will start:
echo 1. FastAPI Backend (Port 8000)
echo 2. Celery Worker
echo 3. React Frontend (Port 5173)
echo.
echo Press any key to continue...
pause >nul

echo Starting all services...

REM Start Backend in new window
start "DocuMind Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start Celery Worker in new window  
start "DocuMind Celery Worker" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && celery -A app.celery_config worker --loglevel=info --pool=solo"

REM Wait a moment for celery to start
timeout /t 3 /nobreak >nul

REM Start Frontend in new window
start "DocuMind Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo All services are starting in separate windows!
echo.
echo Services:
echo - Backend API: http://localhost:8000
echo - Frontend:    http://localhost:5173
echo - API Docs:    http://localhost:8000/docs
echo.
echo Close this window when you're done developing.
pause 