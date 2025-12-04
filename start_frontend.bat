@echo off
echo ========================================
echo   Starting AI Interviewer Frontend
echo ========================================
echo.

cd frontend

echo Starting local server...
echo Frontend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python -m http.server 3000

pause
