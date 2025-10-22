import re
import random

from rich.console import Console
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from services.platform.youtube.support.save_youtube_schedules import save_youtube_schedules

console = Console()

def _log(message: str, verbose: bool, status=None, is_error: bool = False, api_info: Optional[Dict[str, Any]] = None):
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
        
        quota_str = ""
        if api_info and "error" not in api_info:
            rpm_current = api_info.get('rpm_current', 'N/A')
            rpm_limit = api_info.get('rpm_limit', 'N/A')
            rpd_current = api_info.get('rpd_current', 'N/A')
            rpd_limit = api_info.get('rpd_limit', -1)
            quota_str = (
                f" (RPM: {rpm_current}/{rpm_limit}, "
                f"RPD: {rpd_current}/{rpd_limit if rpd_limit != -1 else 'N/A'})")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "bold red"
        console.print(f"[generate_sample_youtube_posts.py] {timestamp}|[{color}]{log_message}{quota_str}[/{color}]")
    elif verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "white"
        console.print(f"[generate_sample_youtube_posts.py] {timestamp}|[{color}]{message}[/{color}]")
        if status:
            status.start()
    elif status:
        status.update(message)

def generate_sample_youtube_posts(scheduled_title_prefix="My Awesome Video", description="This is a video about awesome things.", tags="awesome,video,youtube", privacyStatus="private", start_video_number=1, num_days=1, profile_name="Default", start_date=None, fixed_gap_hours=0, fixed_gap_minutes=0, gap_minutes_min=1, gap_minutes_max=50, verbose: bool = False):
    _log(f"Generating sample YouTube posts for profile: {profile_name}", verbose)
    
    scheduled_uploads = []
    current_time = datetime.now()
    if start_date:
        current_time = datetime.strptime(start_date, "%Y-%m-%d")

    for day in range(num_days):
        day_end_time = current_time + timedelta(days=1)
        while current_time < day_end_time:
            video_file_name = f"{start_video_number}.mp4"
            title = f"{scheduled_title_prefix} {start_video_number}"

            upload_item = {
                "file": video_file_name,
                "title": title,
                "description": description,
                "tags": tags,
                "privacyStatus": privacyStatus,
                "publishAt": current_time.isoformat() + "Z"
            }
            scheduled_uploads.append(upload_item)

            if fixed_gap_hours or fixed_gap_minutes:
                gap = timedelta(hours=fixed_gap_hours, minutes=fixed_gap_minutes)
            else:
                random_minutes = random.randint(gap_minutes_min, gap_minutes_max)
                gap = timedelta(minutes=random_minutes)
            
            current_time += gap
            start_video_number += 1

    save_youtube_schedules(scheduled_uploads, profile_name)
    _log(f"Generated {len(scheduled_uploads)} sample YouTube posts.", verbose) 