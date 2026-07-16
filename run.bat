@echo off
echo Starting AI Agent Task Telemetry Engine...

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Attempting to start Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Please wait for Docker to start, then run this script again.
    pause
    exit /b
)

:: Build and start the containers
echo Building and starting containers via docker-compose...
docker-compose up --build -d

echo.
echo ========================================================
echo ✅ AgentOpsLocal is now running!
echo 🚀 Frontend Dashboard: http://localhost:5173
echo 🔌 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo ========================================================
echo.
echo To stop the engine, run: docker-compose down
pause
