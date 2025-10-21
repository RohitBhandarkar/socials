import re
import os
import time
import google.generativeai as genai

from datetime import datetime
from rich.console import Console

console = Console()

def _log(message: str, verbose: bool, status=None, is_error: bool = False):
    if is_error:
        if status:
            status.stop()
        log_message = message
        if not verbose:
            match = re.search(r'(\d{3}\s+.*?)(?:\.|\n|$)', message)
            if match:
                log_message = f"Error: {match.group(1).strip()}"
            else:
                log_message = message.split('\n')[0].strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "bold red"
        console.print(f"[gemini_util.py] {timestamp}|[{color}]{log_message}[/{color}]")
    elif verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "white"
        console.print(f"[gemini_util.py] {timestamp}|[{color}]{message}[/{color}]")
        if status:
            status.start()
    elif status:
        status.update(message)

def generate_gemini(media_path, api_key, prompt_text, model_name='gemini-2.0-flash-lite', status=None, verbose: bool = False):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    uploaded_file = None
    if media_path:
        base_filename = os.path.basename(media_path)
        sanitized_display_name = re.sub(r'\s*\(.*?\)|\s*\[.*?\]', '', base_filename).strip()

        message = f"[Gemini] Uploading media: {media_path}"
        _log(message, verbose, status)
        uploaded_file = genai.upload_file(path=media_path, display_name=sanitized_display_name)
        
        timeout_seconds = 600
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            file_status = genai.get_file(uploaded_file.name)
            if file_status.state.name == "ACTIVE":
                message = f"[Gemini] File {uploaded_file.display_name} ({file_status.name}) is now ACTIVE."
                _log(message, verbose, status)
                break
            elif file_status.state == "FAILED":
                message = f"Gemini file upload failed for {uploaded_file.display_name} ({file_status.name})."
                _log(message, verbose, status, is_error=True)
                return None
            message = f"[Gemini] Waiting for file {uploaded_file.display_name} ({file_status.state.name}) to become ACTIVE (current state: {file_status.state})... This can take several minutes for large videos."
            _log(message, verbose, status)
            time.sleep(5)
        else:
            message = f"Gemini file {uploaded_file.display_name} ({uploaded_file.name}) did not become ACTIVE within {timeout_seconds} seconds. Aborting content generation."
            _log(message, verbose, status, is_error=True)
            return None

    content = [prompt_text]
    if uploaded_file:
        content.append(uploaded_file)

    message = f"[Gemini] Generating content for {uploaded_file.display_name if uploaded_file else 'text-only'}"
    _log(message, verbose, status)
    response = model.generate_content(content)
    
    try:
        caption = response.text.strip().replace('\n', ' ')
    except ValueError:
        _log(f"Gemini Response (no text): {response}", verbose, status, is_error=True)
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.finish_reason:
                message = f"Gemini generation failed: Finish reason - {candidate.finish_reason.name}."
                if candidate.safety_ratings:
                    message += " Safety ratings: " + ", ".join([f"{s.category.name}: {s.probability.name}" for s in candidate.safety_ratings])
            else:
                message = "Gemini generation failed: No text in response and no clear finish reason."
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            message = f"Gemini generation blocked by prompt feedback: {response.prompt_feedback.block_reason.name}."
        else:
            message = "Gemini generation failed: No text in response and no further details."
        
        _log(message, verbose, status, is_error=True)
        return None

    message = f"[Gemini] Generated content for {uploaded_file.display_name if uploaded_file else 'text-only'}"
    _log(message, verbose, status)

    if uploaded_file:
        try:
            genai.delete_file(uploaded_file.name)
            message = f"[Gemini] Deleted uploaded file: {uploaded_file.display_name}"
            _log(message, verbose, status)
                
        except Exception as e:
            if "PermissionDenied" in str(type(e)):
                message = f"PermissionDenied error when deleting uploaded file {uploaded_file.display_name}: {e}. Skipping deletion."
                _log(message, verbose, status, is_error=True)
            else:
                message = f"An unexpected error occurred when deleting uploaded file {uploaded_file.display_name}: {e}. Skipping deletion."
                _log(message, verbose, status, is_error=True)
    return caption
