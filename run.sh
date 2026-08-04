#!/bin/bash
# ========================================================================
# Telecom Analytics - Run API and Open Dashboard
# ========================================================================

echo "========================================================================"
echo "         Telecom Analytics - Starting API Server"
echo "========================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "        Please run ./setup.sh first to create the environment."
    exit 1
fi

# Activate virtual environment
echo "[1/3] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment."
    exit 1
fi
echo "        Virtual environment activated."
echo ""

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "[ERROR] app.py not found!"
    echo "        Make sure you are in the project root directory."
    exit 1
fi

# Start Uvicorn server
echo "[2/3] Starting Uvicorn server..."
echo "        Server will run at: http://localhost:8000"
echo "        Press Ctrl+C to stop the server"
echo ""

# Open dashboard in browser after a short delay
(sleep 2 && open http://localhost:8000/dashboard/) 2>/dev/null || \
(sleep 2 && xdg-open http://localhost:8000/dashboard/) 2>/dev/null || \
(sleep 2 && echo "        Please open http://localhost:8000/dashboard/ in your browser")

# Run the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# This line only runs after the server is stopped
echo ""
echo "========================================================================"
echo "         Server stopped."
echo "========================================================================"