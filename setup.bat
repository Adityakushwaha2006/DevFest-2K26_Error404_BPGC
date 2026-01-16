@echo off
echo ========================================
echo NEXUS - Setup Script
echo ========================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python is installed and in PATH
    pause
    exit /b 1
)
echo ✓ Virtual environment created!
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated!
echo.

echo Step 3: Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed!
echo.

echo Step 4: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo ✓ .env file created! Please edit it with your API keys.
) else (
    echo ⚠ .env file already exists, skipping...
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Get your GitHub token from: https://github.com/settings/tokens
echo 2. Get your Gemini API key from: https://makersuite.google.com/app/apikey
echo 3. Edit .env file and add your keys
echo 4. Run: cd backend
echo 5. Run: python demo_identity_resolution.py
echo.
pause
