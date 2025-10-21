import re
import os
import json

from datetime import datetime
from rich.status import Status
from rich.console import Console
from services.support.path_config import get_schedule_file_path, ensure_dir_exists

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
        console.print(f"[clear_media_files.py] {timestamp}|[{color}]{log_message}[/{color}]")
    elif verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "white"
        console.print(f"[clear_media_files.py] {timestamp}|[{color}]{message}[/{color}]")
    elif status:
        status.update(message)

def clear_media(profile_name, verbose: bool = False):
    _log(f"Clearing media files for profile: {profile_name}", verbose)
    schedule_json_path = get_schedule_file_path(profile_name)
    schedule_folder = os.path.dirname(schedule_json_path)
    
    ensure_dir_exists(schedule_folder)
        
    try:
        with open(schedule_json_path, 'w') as f:
            json.dump([], f)
        _log(f"Cleared schedule file: {schedule_json_path}", verbose)
    except Exception as e:
        _log(f"Error clearing schedule file {schedule_json_path}: {e}", verbose, is_error=True)

    deleted_count = 0
    with Status("[white]Deleting media files...[/white]", spinner="dots", console=console) as status:
        for filename in os.listdir(schedule_folder):
            file_path = os.path.join(schedule_folder, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in [".mp4", ".png", ".jpg", ".jpeg"]:
                    try:
                        os.remove(file_path)
                        _log(f"Deleted: {filename}", verbose, status)
                        deleted_count += 1
                    except Exception as e:
                        _log(f"Error deleting {filename}: {e}", verbose, status, is_error=True)
    _log(f"Cleaned up {deleted_count} media files in {schedule_folder}.", verbose) 