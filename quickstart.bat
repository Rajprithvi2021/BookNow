@echo off
REM Quick start script for BookNow system (Windows)

echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed. Please install Docker Desktop.
    exit /b 1
)

echo.
echo Starting BookNow appointment system...
echo.

echo Starting services with Docker Compose...
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak

echo.
echo Seeding database with availability slots...
docker-compose exec backend python -m scripts.seed_db

echo.
echo ✅ BookNow is running!
echo.
echo Access the application:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000/api
echo   - API Docs: http://localhost:8000/docs
echo.
echo To stop: docker-compose down
