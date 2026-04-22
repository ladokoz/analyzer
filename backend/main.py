from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')

import os
import logging
import urllib.request
import urllib.parse
import json
import re
import subprocess
from dotenv import load_dotenv

load_dotenv()

os.makedirs("data", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("data/app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api")

from backend.config import load_settings, save_settings, SettingsModel
from backend.gemini_utils import analyze_video

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

class AnalyzeRequest(BaseModel):
    url: str
    internal_id: str = ""
    batch_id: str = "default"

@app.post("/api/login")
def login(req: LoginRequest):
    logger.info(f"Login attempt for user: {req.username}")
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "ahub123")
    
    if req.username == admin_user and req.password == admin_pass:
        logger.info(f"Login successful for user: {req.username}")
        return {"token": "auth_ok"}
    logger.warning(f"Login failed for user: {req.username}")
    raise HTTPException(status_code=401, detail="Invalid password")

def verify_token(authorization: str = None, token: str = None):
    if authorization == "Bearer auth_ok" or token == "auth_ok":
        return
    raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/api/settings")
def get_settings(authorization: str = Header(None)):
    verify_token(authorization)
    settings = load_settings()
    return {
        "model": settings.model,
        "input_cost_per_m": settings.input_cost_per_m,
        "output_cost_per_m": settings.output_cost_per_m,
        "prompts": [p.model_dump() for p in settings.prompts],
        "active_prompt_id": settings.active_prompt_id,
        "keep_downloaded_videos": settings.keep_downloaded_videos,
        "has_api_key": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.post("/api/settings")
def update_settings(settings: SettingsModel, authorization: str = Header(None)):
    verify_token(authorization)
    logger.info("Updating application settings")
    save_settings(settings)
    logger.info("Application settings updated successfully")
    return {"status": "success"}

@app.get("/api/version")
def get_version(authorization: str = Header(None)):
    verify_token(authorization)
    version = "1.2.1"
    if os.path.exists("CHANGELOG.md"):
        with open("CHANGELOG.md", "r", encoding="utf-8") as f:
            content = f.read()
            # Look for the first version that starts with a digit inside brackets
            match = re.search(r"## \[(\d+\.\d+\.\d+)\]", content)
            if match:
                version = match.group(1)
    return {"version": version}

@app.post("/api/check_update")
def check_update(authorization: str = Header(None)):
    verify_token(authorization)
    try:
        # Fetch latest origin/main
        subprocess.run(["git", "fetch"], check=True, capture_output=True)
        # Check if behind origin/main
        result = subprocess.run(["git", "status", "-uno"], capture_output=True, text=True)
        is_behind = "Your branch is behind" in result.stdout
        return {"update_available": is_behind}
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        return {"update_available": False, "error": str(e)}

@app.post("/api/update")
def perform_update(authorization: str = Header(None)):
    verify_token(authorization)
    try:
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}
        return {"status": "success", "message": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/logs")
def get_logs(authorization: str = Header(None), token: str = None):
    verify_token(authorization, token)
    log_path = "data/app.log"
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="No logs found.")
    return FileResponse(log_path, media_type="text/plain")

@app.delete("/api/logs")
def clear_logs(authorization: str = Header(None)):
    verify_token(authorization)
    log_path = "data/app.log"
    if os.path.exists(log_path):
        open(log_path, 'w', encoding='utf-8').close()
    return {"status": "success", "message": "Logs cleared"}

@app.get("/api/csvs")
def list_csvs(authorization: str = Header(None)):
    verify_token(authorization)
    csv_dir = "data/csvs"
    if not os.path.exists(csv_dir):
        return {"files": []}
    files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    files.sort(reverse=True)
    
    file_info = []
    for f in files:
        file_path = os.path.join(csv_dir, f)
        stats = os.stat(file_path)
        file_info.append({
            "name": f,
            "size": stats.st_size,
            "modified": stats.st_mtime
        })
    return {"files": file_info}

@app.get("/api/csvs/{filename}")
def download_specific_csv(filename: str, authorization: str = Header(None), token: str = None):
    verify_token(authorization, token)
    csv_path = f"data/csvs/{filename}"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(csv_path, media_type="text/csv", filename=filename)

@app.delete("/api/csvs/{filename}")
def delete_specific_csv(filename: str, authorization: str = Header(None)):
    verify_token(authorization)
    csv_path = f"data/csvs/{filename}"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="File not found.")
    os.remove(csv_path)
    return {"status": "success", "message": "CSV deleted"}

@app.delete("/api/csvs")
def delete_all_csvs(authorization: str = Header(None)):
    verify_token(authorization)
    csv_dir = "data/csvs"
    if os.path.exists(csv_dir):
        for f in os.listdir(csv_dir):
            if f.endswith('.csv'):
                os.remove(os.path.join(csv_dir, f))
    return {"status": "success", "message": "All CSVs deleted"}

@app.get("/api/videos")
def list_videos(authorization: str = Header(None)):
    verify_token(authorization)
    video_dir = "data/tmp_videos"
    if not os.path.exists(video_dir):
        return {"files": []}
    files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
    files.sort(reverse=True)
    
    file_info = []
    for f in files:
        file_path = os.path.join(video_dir, f)
        stats = os.stat(file_path)
        file_info.append({
            "name": f,
            "size": stats.st_size,
            "modified": stats.st_mtime
        })
    return {"files": file_info}

@app.get("/api/videos/{filename}")
def download_specific_video(filename: str, authorization: str = Header(None), token: str = None):
    verify_token(authorization, token)
    video_path = f"data/tmp_videos/{filename}"
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(video_path, media_type="video/mp4", filename=filename)

@app.delete("/api/videos/{filename}")
def delete_specific_video(filename: str, authorization: str = Header(None)):
    verify_token(authorization)
    video_path = f"data/tmp_videos/{filename}"
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="File not found.")
    os.remove(video_path)
    return {"status": "success", "message": "Video deleted"}

@app.delete("/api/videos")
def delete_all_videos(authorization: str = Header(None)):
    verify_token(authorization)
    video_dir = "data/tmp_videos"
    if os.path.exists(video_dir):
        for f in os.listdir(video_dir):
            if f.endswith('.mp4'):
                os.remove(os.path.join(video_dir, f))
    return {"status": "success", "message": "All videos deleted"}

def get_youtube_title(url: str) -> str:
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("title", "Unknown Title")
    except Exception as e:
        logger.error(f"Failed to fetch YouTube title for {url}: {e}")
        return "Unknown Title"

@app.on_event("startup")
def startup_event():
    from backend.worker import start_worker
    start_worker()

@app.get("/api/jobs")
def get_jobs(authorization: str = Header(None)):
    verify_token(authorization)
    from backend.worker import jobs_state
    return {"jobs": jobs_state}

@app.post("/api/stop")
def stop_all_jobs(authorization: str = Header(None)):
    verify_token(authorization)
    from backend.worker import cancel_all
    count = cancel_all()
    return {"status": "success", "message": f"Canceled {count} pending tasks."}

@app.get("/api/status")
def get_status(url: str, authorization: str = Header(None)):
    verify_token(authorization)
    from backend.worker import jobs_state
    if url in jobs_state:
        return {"status": jobs_state[url].get("status", "")}
    return {"status": ""}

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, authorization: str = Header(None)):
    verify_token(authorization)
    logger.info(f"Enqueuing analyze request for URL: {req.url} (Internal ID: {req.internal_id})")
    from backend.worker import enqueue_task
    enqueue_task(req.url, req.internal_id, req.batch_id)
    return {"url": req.url, "status": "queued"}

@app.post("/api/batch")
async def deprecated_batch(request: BaseModel = None):
    logger.warning("Received request to deprecated /api/batch endpoint. Frontend is likely cached.")
    raise HTTPException(
        status_code=400, 
        detail="Frontend version mismatch. Please hard-refresh your browser (Ctrl+Shift+R or Cmd+Shift+R) to load the new version."
    )

# Serve Frontend
os.makedirs("frontend", exist_ok=True)
app.mount("/assets", StaticFiles(directory="frontend"), name="assets")

@app.get("/")
def index():
    return FileResponse("frontend/index.html", headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })

@app.get("/{path:path}")
def catch_all(path: str):
    full_path = f"frontend/{path}"
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    return FileResponse("frontend/index.html", headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })
