@echo off
REM DobotHub (Client) - Start server

echo Starting DobotHub...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Run 'install.bat' first.
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Default port to 8080 if not specified
set PORT=%1
if "%PORT%"=="" set PORT=8080

REM Start the Flask server
echo Starting Flask server on http://localhost:%PORT%
echo Press Ctrl+C to stop
echo.

python web_server.py %PORT%