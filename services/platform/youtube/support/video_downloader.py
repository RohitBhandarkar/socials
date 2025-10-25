import os
import re
import subprocess

from datetime import datetime
from rich.console import Console
from typing import List, Dict, Any, Optional
from services.support.path_config import get_downloads_dir

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
        console.print(f"[video_downloader.py] {timestamp}|[{color}]{log_message}{quota_str}[/{color}]")
    elif verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "white"
        console.print(f"[video_downloader.py] {timestamp}|[{color}]{message}[/{color}]")
        if status:
            status.start()
    elif status:
        status.update(message)

def download_videos_for_youtube_scraper(profile_name: str, videos_data: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    results = {
        "success": [],
        "failed": []
    }

    output_dir = os.path.abspath(os.path.join(get_downloads_dir(), 'youtube', profile_name, 'videos'))
    os.makedirs(output_dir, exist_ok=True)

    total_videos = len(videos_data)
    _log(f"Starting to download {total_videos} videos for profile '{profile_name}'", verbose)

    for i, video in enumerate(videos_data):
        video_url = video.get('url')
        video_id = video.get('video_id')
        video_title = video.get('title', 'Unknown Title')

        if not video_url:
            _log(f"No URL found for video {i+1}/{total_videos}. Skipping.", verbose)
            results["failed"].append({
                "video_id": video_id or "Unknown",
                "title": video_title,
                "reason": "No URL provided"
            })
            continue

        console.print(f"[white]Processing video {i+1}/{total_videos}: {video_title}[/white]")

        try:
            cmd = [
                'yt-dlp',
                '--output', os.path.join(output_dir, '%(id)s.%(ext)s'),
                '--restrict-filenames',
                video_url
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True, check=True)
            _log(f"Successfully downloaded: {video_title}", verbose)
            results["success"].append({
                "video_id": video_id,
                "title": video_title,
                "output": process.stdout.strip()
            })
        except subprocess.CalledProcessError as e:
            _log(f"Failed to download video {video_title}: {e.stderr.strip()}", verbose, is_error=True)
            results["failed"].append({
                "video_id": video_id,
                "title": video_title,
                "reason": e.stderr.strip()
            })
        except Exception as e:
            _log(f"An unexpected error occurred while downloading {video_title}: {e}", verbose, is_error=True)
            results["failed"].append({
                "video_id": video_id,
                "title": video_title,
                "reason": str(e)
            })
    
    _log(f"Completed video download. Success: {len(results['success'])}, Failed: {len(results['failed'])}", verbose)
    return results 