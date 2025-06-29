@echo off
echo 🧪 Starting DocuMind AI Local Production Test Environment...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found. Please create it with production values.
    echo Copy from env.example and update with secure production values.
    pause
    exit /b 1
)

echo ⚠️  WARNING: This will test production-like setup locally:
echo   - Production environment variables
echo   - Redis password protection
echo   - Network isolation
echo   - Nginx reverse proxy
echo   - 4 Celery workers
echo   - BUT: HTTP only (no SSL) for local testing
echo.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo 🔨 Building and starting local production test containers...
docker-compose -f docker-compose.local-prod.yml up --build -d

echo 📊 Container Status:
docker-compose -f docker-compose.local-prod.yml ps

echo 🌐 Local Production Test services:
echo   Application: http://localhost:8080
echo   Backend API: http://localhost:8080/api/v1/
echo   Health Check: http://localhost:8080/health
echo   API Docs: http://localhost:8080/api/v1/docs (if enabled)

echo 📋 Local Production Test commands:
echo   View logs: docker-compose -f docker-compose.local-prod.yml logs -f
echo   Stop all: docker-compose -f docker-compose.local-prod.yml down
echo   Update: docker-compose -f docker-compose.local-prod.yml pull && docker-compose -f docker-compose.local-prod.yml up -d

echo.
echo ✅ Local production test environment started!
echo 🧪 Test all functionality before deploying to AWS.

pause 