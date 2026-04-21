@echo off
if not exist "venv\Scripts\activate.bat" (
    echo Setting up environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
echo Starting server...
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
