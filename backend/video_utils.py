import yt_dlp
import os
import logging
import uuid
import time

logger = logging.getLogger("video_utils")

def download_vimeo_video(url: str, username: str = "", password: str = "", internal_id: str = "") -> tuple[str, str]:
    """
    Downloads a video locally using yt_dlp.
    Returns (local_file_path, video_title).
    """
    os.makedirs("data/tmp_videos", exist_ok=True)
    temp_id = str(uuid.uuid4())
    
    safe_id = "".join(c for c in internal_id if c.isalnum() or c in ('-', '_', ' ')) if internal_id else ""
    prefix = f"{safe_id}_" if safe_id else ""
    
    ydl_opts_base = {
        'outtmpl': f'data/tmp_videos/{prefix}%(title)s_%(id)s.%(ext)s',  # Replaced temp_id with actual title and prefix
        'format': 'b*[ext=mp4]/b*',
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
    }
    
    ydl_opts = dict(ydl_opts_base)
    if username and password:
        ydl_opts['username'] = username
        ydl_opts['password'] = password
        logger.info(f"Using Vimeo credentials for user {username}")

    logger.info(f"Starting download for Vimeo URL: {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown Title')
            
            # ydl.prepare_filename returns the path with the generated actual extension
            file_path = ydl.prepare_filename(info)
            
            if not os.path.exists(file_path):
                pass
                
            return file_path, title
    except Exception as e:
        error_str = str(e)
        if "Unable to log in" in error_str and username and password:
            logger.warning(f"Vimeo login failed, retrying without credentials for {url}")
            try:
                with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown Title')
                    file_path = ydl.prepare_filename(info)
                    return file_path, title
            except Exception as retry_e:
                logger.error(f"Failed to download Vimeo video {url} without credentials: {retry_e}", exc_info=True)
                raise Exception(f"Failed to download video: {str(retry_e)}")
        else:
            logger.error(f"Failed to download Vimeo video {url}: {e}", exc_info=True)
            raise Exception(f"Failed to download video: {error_str}")
