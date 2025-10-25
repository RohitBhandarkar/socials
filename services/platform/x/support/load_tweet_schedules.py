import os
import re
import json

from datetime import datetime
from rich.console import Console
from services.support.path_config import get_schedule_file_path

console = Console()

def _log(message: str, verbose: bool, is_error: bool = False, status=None):
    if status and (is_error or verbose):
        status.stop()
    
    log_message = message
    if is_error:
        if not verbose:
            match = re.search(r'(\d{3}\s+.*?)(?:\.|\n|$)', message)
            if match:
                log_message = f"Error: {match.group(1).strip()}"
            else:
                log_message = message.split('\n')[0].strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "bold red"
        console.print(f"[load_tweet_schedules.py] {timestamp}|[{color}]{log_message}[/{color}]")
    elif verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "white"
        console.print(f"[load_tweet_schedules.py] {timestamp}|[{color}]{message}[/{color}]")
    elif status:
        status.update(message)

def load_tweet_schedules(profile_name="Default", verbose: bool = False, status=None):
    schedule_file_path = get_schedule_file_path(profile_name)
    
    if not os.path.exists(schedule_file_path):
        _log("Schedule file not found, returning empty list", verbose, status=status)
        return []
    
    with open(schedule_file_path, 'r') as f:
        try:
            schedules = json.load(f)
            return sorted(schedules, key=lambda x: datetime.strptime(x['scheduled_time'], '%Y-%m-%d %H:%M:%S'))
        except json.JSONDecodeError:
            _log("Invalid JSON in schedule file, returning empty list", verbose, is_error=True, status=status)

            return []
