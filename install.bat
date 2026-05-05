@echo off
REM DobotHub (Client) - Setup dependencies

echo Installing DobotHub dependencies...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3 is required but not installed.
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade pip
echo Upgrading pip...
pip install --upgrade pip

REM Install dependencies from requirements.txt
if exist "requirements.txt" (
    echo Installing Python packages from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found, skipping pip install
)

echo.
echo DobotHub setup complete!
echo.
echo To activate virtual environment manually:
echo   venv\Scripts\activate.bat
echo.
echo To start DobotHub:
echo   start.bat