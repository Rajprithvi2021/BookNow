@REM Docker initialization script for BookNow (Windows)

@echo off
setlocal enabledelayedexpansion

echo.
echo 🚀 BookNow Docker Setup
echo =======================
echo.

REM Check Docker installation
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Docker is installed
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    (
        echo # Database Configuration
        echo DB_USER=booknow
        echo DB_PASSWORD=booknow_secure_pass_123
        echo DB_NAME=booknow
        echo.
        echo # API Configuration
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo.
        echo # Frontend Configuration
        echo NEXT_PUBLIC_API_URL=http://localhost:8000/api
        echo.
        echo # Environment
        echo NODE_ENV=development
        echo PYTHONUNBUFFERED=1
        echo PYTHONDONTWRITEBYTECODE=1
    ) > .env
    echo ✅ .env file created
) else (
    echo ✅ .env file already exists
)

echo.
echo 🐳 Building Docker images...
docker-compose build --no-cache

echo.
echo 🚀 Starting services...
docker-compose up -d

echo.
echo ⏳ Waiting for services to be healthy...
timeout /t 15 /nobreak

echo.
echo ✅ BookNow is running!
echo.
echo 📍 Access points:
echo    - Frontend:  http://localhost:3000
echo    - Backend:   http://localhost:8000
echo    - API Docs:  http://localhost:8000/docs
echo    - Adminer:   http://localhost:8081
echo.
echo 📊 Database credentials:
echo    - Server:   localhost:5432
echo    - User:     booknow
echo    - Database: booknow
echo.
echo 🛑 To stop services:
echo    docker-compose down
echo.
echo 📊 View logs:
echo    docker-compose logs -f
echo.
pause
