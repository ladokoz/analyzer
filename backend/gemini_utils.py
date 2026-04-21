from google import genai
from google.genai import types
from pydantic import BaseModel
import logging

logger = logging.getLogger("gemini")

class AnalysisResult(BaseModel):
    tags: list[str]
    genres: list[str]
    animation_techniques: list[str]
    accessibility_rating: str
    film_directors: list[str]
    film_producers: list[str]
    year: str
    production_companies: list[str]
    school_or_university: list[str]
    distribution_and_sales_companies: list[str]
    animators: list[str]
    script_writers: list[str]
    music_composers: list[str]
    sound_designers: list[str]
    editors: list[str]
    festival_selection: list[str]
    awards: list[str]

def analyze_video(url: str, api_key: str, model_name: str, custom_prompt: str, local_file_path: str = None, video_title: str = "") -> dict:
    client = genai.Client(api_key=api_key)
    
    import time
    import re
    
    uploaded_file = None
    try:
        from backend.status import job_statuses
        if local_file_path:
            logger.info(f"Uploading local file to Gemini API: {local_file_path}")
            job_statuses[url] = "Uploading file to Gemini..."
            uploaded_file = client.files.upload(file=local_file_path)
            
            while uploaded_file.state.name == "PROCESSING":
                job_statuses[url] = "Processing file on Gemini..."
                time.sleep(2)
                uploaded_file = client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise Exception("Video processing failed on Gemini server.")
                
            video_part = types.Part.from_uri(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)
        else:
            # Pass YouTube URL directly to Gemini API! Native Support!
            video_part = types.Part.from_uri(file_uri=url, mime_type="video/mp4")
        
        full_prompt = f"Video URL: {url}\nVideo Title: {video_title}\n\nCustom Instructions: {custom_prompt}\n\nPlease analyze the video file visually/audibly and search the video title to extract the required JSON structure fields (including directors, producers, year, companies, animators, script writers, composers, sound designers, editors, festivals, and awards). Return exactly the requested JSON schema."


        max_retries = 15
        response = None

        for attempt in range(max_retries):
            try:
                job_statuses[url] = f"Analyzing with Gemini (Attempt {attempt+1}/{max_retries})..."
                logger.info(f"Sending request to Gemini API. Model: {model_name}, File URI: {url} (Attempt {attempt+1}/{max_retries})")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[video_part, full_prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AnalysisResult,
                        temperature=0.2
                    )
                )
                logger.info("Received response from Gemini API.")
                break
            except Exception as e:
                error_str = str(e)
                
                # Fail fast if quota is permanently exhausted (e.g., daily limit)
                is_quota_exceeded = "quota" in error_str.lower() and "exceeded" in error_str.lower() and "retry in" not in error_str.lower()
                if is_quota_exceeded:
                    logger.error(f"Daily quota exceeded. Stopping retries: {error_str}", exc_info=True)
                    return {"error": f"API Quota Exceeded. Try another key or wait until tomorrow. Details: {str(e)}"}
                
                # Retry on rate limits (429) AND temporary server errors (500, 502, 503, 504)
                is_retryable = (
                    "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "Too Many Requests" in error_str or
                    "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str.lower() or
                    "500" in error_str or "502" in error_str or "504" in error_str
                )
                
                if is_retryable and attempt < max_retries - 1:
                    match = re.search(r"Please retry in ([\d\.]+)s", error_str)
                    if match:
                        wait_time = float(match.group(1)) + 1.0
                    else:
                        # Exponential backoff base 15s if no explicit retry time
                        wait_time = min(15.0 * (2 ** attempt), 120.0)
                    
                    logger.warning(f"Retryable error hit (e.g., rate limit or 503). Waiting {wait_time:.1f}s before retrying... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                elif attempt == max_retries - 1:
                    logger.error(f"Failed to call Gemini API after {max_retries} attempts: {error_str}", exc_info=True)
                    return {"error": f"Failed to call API after {max_retries} attempts: {str(e)}"}
                else:
                    logger.error(f"Failed to call Gemini API: {error_str}", exc_info=True)
                    return {"error": f"Failed to call API: {str(e)}"}
        
        if response is None:
            return {"error": "Failed to get a response from Gemini API."}

        try:
            import json
            data = json.loads(response.text)
            usage = response.usage_metadata
            if usage:
                tokens = {
                    "input": getattr(usage, "prompt_token_count", 0) or 0,
                    "output": getattr(usage, "candidates_token_count", 0) or 0,
                    "total": getattr(usage, "total_token_count", 0) or 0
                }
            else:
                tokens = {"input": 0, "output": 0, "total": 0}
            logger.info(f"Successfully parsed Gemini API response. Tokens: {tokens}")
            return {"data": data, "tokens": tokens}
        except Exception as e:
            logger.error(f"Failed to parse Gemini API response: {str(e)}", exc_info=True)
            return {"error": f"Failed to parse response: {str(e)}", "raw": response.text}
    finally:
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                logger.info(f"Deleted remote file from Gemini API: {uploaded_file.name}")
            except Exception as e:
                logger.error(f"Failed to delete remote file from Gemini API: {e}")

