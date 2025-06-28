@echo off
echo 🚀 Starting DocuMind AI Production Environment...

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

echo ⚠️  WARNING: This will start production containers with:
echo   - HTTPS enabled (requires SSL certificates)
echo   - Production security settings
echo   - Persistent data volumes
echo.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo 🔨 Building and starting production containers...
docker-compose -f docker-compose.prod.yml up --build -d

echo 📊 Container Status:
docker-compose -f docker-compose.prod.yml ps

echo 🌐 Production services:
echo   Application: https://localhost (or your domain)
echo   HTTP redirects to HTTPS automatically

echo 📋 Production commands:
echo   View logs: docker-compose -f docker-compose.prod.yml logs -f
echo   Stop all: docker-compose -f docker-compose.prod.yml down
echo   Update: docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d

pause 