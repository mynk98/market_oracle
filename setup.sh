#!/bin/bash

# Exit on error
set -e

# Get absolute path of this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[*] Creating virtual environment (venv) in $SCRIPT_DIR..."
python3 -m venv venv

echo "[*] Activating virtual environment..."
source venv/bin/activate

echo "[*] Upgrading pip..."
pip install --upgrade pip

echo "[*] Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "[!] requirements.txt not found, installing manually..."
    pip install pandas pandas_ta streamlit plotly yfinance duckduckgo_search matplotlib
fi

echo "[*] Creating data directories..."
mkdir -p data/news_archive

echo "[*] Setup complete. Run ./run.sh to start the dashboard."
