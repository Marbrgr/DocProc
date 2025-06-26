@echo off
echo Starting DocuMind AI Celery Worker...
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
echo Virtual environment activated
echo Starting Celery worker...
celery -A app.celery_config worker --loglevel=info --pool=solo
pause 