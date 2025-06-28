@echo off
echo 🐳 Starting DocuMind AI Development Environment...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Copying from env.example...
    copy env.example .env
    echo ✅ Please edit .env file with your actual values before continuing.
    pause
)

echo 🔨 Building and starting containers...
docker-compose up --build -d

echo 📊 Container Status:
docker-compose ps

echo 🌐 Services will be available at:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo   Flower (Celery Monitor): http://localhost:5555
echo   Database: localhost:5432

echo 📋 Useful commands:
echo   View logs: docker-compose logs -f
echo   Stop all: docker-compose down
echo   Restart: docker-compose restart

pause 