import re
import os
import json

from datetime import datetime
from rich.console import Console
from services.support.path_config import get_schedule_file_path, ensure_dir_exists

console = Console()

def _log(message: str, verbose: bool, is_error: bool = False):
    if verbose or is_error:
        log_message = message
        if is_error and not verbose:
            match = re.search(r'(\d{3}\s+.*?)(?:\.|\n|$)', message)
            if match:
                log_message = f"Error: {match.group(1).strip()}"
            else:
                log_message = message.split('\n')[0].strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "bold red" if is_error else "white"
        console.print(f"[save_tweet_schedules.py] {timestamp}|[{color}]{log_message}[/{color}]")

def save_tweet_schedules(schedules, profile_name="Default", verbose: bool = False):
    schedule_file_path = get_schedule_file_path(profile_name)
    ensure_dir_exists(os.path.dirname(schedule_file_path))
    
    with open(schedule_file_path, 'w') as f:
        json.dump(schedules, f, indent=2)
    _log(f"Tweet schedules saved to {schedule_file_path}", verbose)
