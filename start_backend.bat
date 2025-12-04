@echo off
echo ========================================
echo   Starting AI Interviewer Backend
echo ========================================
echo.

cd backend

echo Checking config.json...
if not exist config.json (
    echo ERROR: config.json not found!
    echo Please configure your API keys first.
    pause
    exit /b 1
)

echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python main.py

pause
