@echo off
:: ========================================================================
:: Telecom Analytics - Run API and Open Dashboard
:: ========================================================================
:: This script:
::   1. Activates the virtual environment
::   2. Starts the Uvicorn server
::   3. Opens the dashboard in your default browser
::   4. Stops the server when you close the window
:: ========================================================================

echo ========================================================================
echo         Telecom Analytics - Starting API Server
echo ========================================================================
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo         Please run setup.bat first to create the environment.
    pause
    exit /b 1
)

:: Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo         Virtual environment activated.
echo.

:: Check if app.py exists
if not exist "app.py" (
    echo [ERROR] app.py not found!
    echo         Make sure you are in the project root directory.
    pause
    exit /b 1
)

:: Start Uvicorn server in the background
echo [2/3] Starting Uvicorn server...
echo         Server will run at: http://localhost:8000
echo         Press Ctrl+C to stop the server
echo.

:: Open dashboard in browser after a short delay
start /min cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000/dashboard/"

:: Run the server (this will block the terminal)
uvicorn app:app --reload --host 0.0.0.0 --port 8000

:: This line only runs after the server is stopped
echo.
echo ========================================================================
echo         Server stopped.
echo ========================================================================
pause