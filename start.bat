@echo off
echo Starting PortScanner...

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Start the scan agent in a new window
echo Starting scan agent (native Windows)...
start "PortScanner - Scan Agent" cmd /k "python scan-agent/agent.py"

REM Wait a moment for agent to start
timeout /t 2 /nobreak >nul

REM Start Docker containers
echo Starting Docker containers...
docker compose up --build

pause