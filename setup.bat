@echo off
echo ========================================
echo   AI Interviewer - Quick Setup
echo ========================================
echo.

echo [1/3] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo.
echo [2/3] Installing dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Setup complete!
echo.
echo ========================================
echo   Next Steps:
echo ========================================
echo 1. Edit backend\config.json with your API keys
echo 2. Run: python backend\main.py
echo 3. Open frontend\index.html in your browser
echo.
echo For detailed instructions, see README.md
echo ========================================
pause
