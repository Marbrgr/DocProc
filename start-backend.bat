@echo off
echo Starting DocuMind AI Backend...
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
echo Virtual environment activated
echo Starting Uvicorn server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause 