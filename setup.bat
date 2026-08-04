#!/bin/bash
# ========================================================================
# Telecom Analytics - Setup Script for Linux/Mac
# ========================================================================

echo "========================================================================
         Telecom Analytics - Environment Setup Script
========================================================================"
echo ""

# Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "        Please install Python 3.10 or higher."
    exit 1
fi

python3 --version
echo ""

# Create virtual environment
echo "[2/5] Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "        Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
    echo "        Virtual environment created successfully."
fi
echo ""

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment."
    exit 1
fi
echo "        Virtual environment activated."
echo ""

# Upgrade pip
echo "[4/5] Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "        pip upgraded successfully."
echo ""

# Install dependencies
echo "[5/5] Installing dependencies from requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] requirements.txt file not found!"
    echo "        Make sure you are in the project root directory."
    exit 1
fi

echo "        This may take a few minutes..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[WARNING] Some packages failed to install."
    echo "          You may need to install them manually."
else
    echo ""
    echo "        All dependencies installed successfully."
fi
echo ""

# Verify installation
echo "========================================================================"
echo "         Installation Summary"
echo "========================================================================"
echo ""

python -c "import clickhouse_connect" 2>/dev/null && echo "[OK] clickhouse-connect installed" || echo "[WARNING] clickhouse-connect not installed"
python -c "import fastapi" 2>/dev/null && echo "[OK] fastapi installed" || echo "[WARNING] fastapi not installed"
python -c "import uvicorn" 2>/dev/null && echo "[OK] uvicorn installed" || echo "[WARNING] uvicorn not installed"
python -c "import faker" 2>/dev/null && echo "[OK] faker installed" || echo "[WARNING] faker not installed"
python -c "import tabulate" 2>/dev/null && echo "[OK] tabulate installed" || echo "[WARNING] tabulate not installed"
python -c "import pydantic" 2>/dev/null && echo "[OK] pydantic installed" || echo "[WARNING] pydantic not installed"

echo ""
echo "========================================================================"
echo "         Setup Complete!"
echo "========================================================================"
echo ""
echo "To activate the virtual environment manually:"
echo "    source venv/bin/activate"
echo ""
echo "To run the CLI:"
echo "    python main.py"
echo ""
echo "To run the API:"
echo "    uvicorn app:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "To deactivate the virtual environment:"
echo "    deactivate"
echo ""
echo "========================================================================"