import threading
import queue
import time
import os
import json
import logging
import csv
from datetime import datetime

from backend.config import load_settings
from backend.gemini_utils import analyze_video
from backend.video_utils import download_vimeo_video

logger = logging.getLogger("api")

task_queue = queue.Queue()
jobs_state = {}
worker_thread = None
stop_event = threading.Event()

def get_youtube_title_safe(url: str) -> str:
    from backend.main import get_youtube_title
    return get_youtube_title(url)

def worker_loop():
    while True:
        try:
            task = task_queue.get(timeout=1)
        except queue.Empty:
            continue
            
        url = task['url']
        internal_id = task['internal_id']
        batch_id = task['batch_id']
        
        if stop_event.is_set():
            jobs_state[url]['status'] = "Canceled"
            task_queue.task_done()
            continue
            
        jobs_state[url]['status'] = "Starting..."
        try:
            process_task(url, internal_id, batch_id)
        except Exception as e:
            logger.error(f"Task failed for {url}: {e}", exc_info=True)
            jobs_state[url]['status'] = "Error"
            jobs_state[url]['error'] = str(e)
            
        task_queue.task_done()

def process_task(url, internal_id, batch_id):
    settings = load_settings()
    api_key_to_use = os.getenv("GEMINI_API_KEY")
    
    if not api_key_to_use:
        raise Exception("API Key not configured in .env")
        
    active_prompt_text = next((p.text for p in settings.prompts if p.id == settings.active_prompt_id), "Analyze video")
    
    local_file_path = None
    video_title = "Unknown Title"
    
    is_vimeo = "vimeo.com" in url.lower()
    if is_vimeo:
        jobs_state[url]['status'] = "Downloading video..."
        local_file_path, video_title = download_vimeo_video(
            url, 
            os.getenv("VIMEO_USERNAME", ""), 
            os.getenv("VIMEO_PASSWORD", ""), 
            internal_id
        )
    else:
        jobs_state[url]['status'] = "Fetching metadata..."
        video_title = get_youtube_title_safe(url)
        
    jobs_state[url]['title'] = video_title
    
    if stop_event.is_set():
        jobs_state[url]['status'] = "Canceled"
        return
        
    jobs_state[url]['status'] = "Analyzing..."
    
    try:
        result = analyze_video(url, api_key_to_use, settings.model, active_prompt_text, local_file_path, video_title)
    finally:
        if local_file_path and not settings.keep_downloaded_videos:
            try:
                os.remove(local_file_path)
            except Exception as e:
                logger.error(f"Failed to delete local file {local_file_path}: {e}")
                
    if stop_event.is_set():
        jobs_state[url]['status'] = "Canceled"
        return

    if "data" in result:
        result['data']['clean_title'] = video_title
        result['data']['title'] = video_title
        
        tokens = result.get('tokens', {"input": 0, "output": 0, "total": 0})
        cost = (tokens["input"] * settings.input_cost_per_m + tokens["output"] * settings.output_cost_per_m) / 1000000
        result['cost'] = cost
        
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        result['timestamp'] = now_str
        
        jobs_state[url]['result'] = result
        jobs_state[url]['cost'] = cost
        jobs_state[url]['tokens'] = tokens['total']
        jobs_state[url]['timestamp'] = now_str
        jobs_state[url]['status'] = "Done"
        
        csv_dir = "data/csvs"
        os.makedirs(csv_dir, exist_ok=True)
        safe_batch_id = "".join(c for c in batch_id if c.isalnum() or c in ('-', '_'))
        if not safe_batch_id: safe_batch_id = "default"
        csv_path = os.path.join(csv_dir, f"batch_{safe_batch_id}.csv")
        file_exists = os.path.isfile(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Internal ID', 'Date/Time', 'Video URL', 'Clean Title', 'Tags', 'Genres', 'Animation Techniques', 'Accessibility Rating', 'Film Directors', 'Film Producers', 'Year', 'Production Companies', 'School or University', 'Dist/Sales Companies', 'Animators', 'Script Writers', 'Music Composers', 'Sound Designers', 'Editors', 'Festival Selection', 'Awards', 'Tokens', 'Cost'])
                
            res_data = result['data']
            l_str = lambda k: ", ".join(res_data.get(k, [])) if isinstance(res_data.get(k), list) else str(res_data.get(k, ''))
            r_tags = l_str('tags')
            r_genres = l_str('genres')
            r_anim = l_str('animation_techniques')
            r_acc = str(res_data.get('accessibility_rating', ''))
            r_dirs = l_str('film_directors')
            r_prods = l_str('film_producers')
            r_year = str(res_data.get('year', ''))
            
            row_data = [
                internal_id, now_str, url, video_title, r_tags, r_genres, r_anim, r_acc, r_dirs, r_prods, r_year,
                l_str('production_companies'), l_str('school_or_university'), l_str('distribution_and_sales_companies'),
                l_str('animators'), l_str('script_writers'), l_str('music_composers'), l_str('sound_designers'),
                l_str('editors'), l_str('festival_selection'), l_str('awards'),
                tokens['total'], f"${cost:.5f}"
            ]
            writer.writerow(row_data)
    else:
        jobs_state[url]['status'] = "Error"
        jobs_state[url]['error'] = "No 'data' in result"

def start_worker():
    global worker_thread
    if worker_thread is None or not worker_thread.is_alive():
        worker_thread = threading.Thread(target=worker_loop, daemon=True)
        worker_thread.start()

def enqueue_task(url, internal_id, batch_id):
    start_worker()
    stop_event.clear()
    if url not in jobs_state:
        jobs_state[url] = {
            'url': url,
            'internal_id': internal_id,
            'batch_id': batch_id,
            'status': 'Pending',
            'title': '-',
            'timestamp': '-',
            'cost': 0,
            'tokens': 0,
            'error': None,
            'result': None
        }
    else:
        jobs_state[url]['status'] = 'Pending'
        jobs_state[url]['error'] = None
    task_queue.put({'url': url, 'internal_id': internal_id, 'batch_id': batch_id})

def cancel_all():
    stop_event.set()
    canceled_count = 0
    while not task_queue.empty():
        try:
            task = task_queue.get_nowait()
            url = task['url']
            jobs_state[url]['status'] = "Canceled"
            task_queue.task_done()
            canceled_count += 1
        except queue.Empty:
            break
    logger.info(f"Canceled {canceled_count} pending tasks from the queue.")
    return canceled_count
