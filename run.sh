#!/bin/bash

# Get absolute path of this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[*] Launching Lyra Market Oracle Dashboard..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[!] Virtual environment not found. Running setup first..."
    chmod +x setup.sh
    ./setup.sh
fi

# Run Streamlit
source venv/bin/activate
streamlit run scripts/dashboard.py
