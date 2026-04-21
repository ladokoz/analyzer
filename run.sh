#!/bin/bash

# Define the script file
if [ ! -f "venv/bin/activate" ]; then
    echo "Setting up environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Starting server..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
