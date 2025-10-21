import re
import os
import json

from datetime import datetime
from rich.status import Status
from rich.console import Console
from services.platform.x.support.save_tweet_schedules import save_tweet_schedules

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
        console.print(f"[try_mp4_missing_media.py] {timestamp}|[{color}]{log_message}[/{color}]")
    elif verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "white"
        console.print(f"[try_mp4_missing_media.py] {timestamp}|[{color}]{message}[/{color}]")
    elif status:
        status.update(message)

def try_mp4_for_missing_media(profile_name="Default", verbose: bool = False):
    schedule_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'schedule', profile_name, 'schedule.json')
    schedule_file_path = os.path.abspath(schedule_file_path)
    if not os.path.exists(schedule_file_path):
        _log(f"Schedule file not found at {schedule_file_path}.", verbose)
        return

    with open(schedule_file_path, 'r') as f:
        schedules = json.load(f)
    
    updated_schedules = []
    schedule_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'schedule', profile_name))

    with Status("[white]Checking for missing media...[/white]", spinner="dots", console=console) as status:
        for tweet in schedules:
            media_file = tweet.get('scheduled_image')
            if media_file:
                original_media_path = os.path.join(schedule_folder, media_file)
                if not os.path.exists(original_media_path):
                    base, ext = os.path.splitext(media_file)
                    mp4_media_file = base + ".mp4"
                    mp4_media_path = os.path.join(schedule_folder, mp4_media_file)
                    if os.path.exists(mp4_media_path):
                        _log(f"Found missing media: {media_file}, attempting .mp4 conversion. Found {mp4_media_file}", verbose, status)
                        tweet['scheduled_image'] = mp4_media_file
                    else:
                        _log(f"Neither {media_file} nor {mp4_media_file} found for tweet.", verbose, status)
                updated_schedules.append(tweet)
            else:
                updated_schedules.append(tweet)
        
        save_tweet_schedules(updated_schedules, profile_name, verbose=verbose)
        _log("Media check and update complete.", verbose, status)
