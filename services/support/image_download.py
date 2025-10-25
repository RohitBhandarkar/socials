import re
import os
import requests

from datetime import datetime
from rich.console import Console
from urllib.parse import urlparse
from services.support.path_config import get_downloads_dir

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
        console.print(f"[image_download.py] {timestamp}|[{color}]{log_message}[/{color}]")

def download_images(image_urls, profile_name="Default", verbose: bool = False):
    download_dir = os.path.abspath(os.path.join(get_downloads_dir(), 'images', profile_name))
    os.makedirs(download_dir, exist_ok=True)
    
    local_image_paths = []
    for url in image_urls:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            query_params = parsed_url.query.split('&')
            format_param = next((p for p in query_params if p.startswith('format=')), None)
            if format_param:
                ext = format_param.split('=')[1]
                if not filename.endswith(f'.{ext}'):
                    filename = f"{filename.split('.')[0]}.{ext}"
            
            file_path = os.path.join(download_dir, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            local_image_paths.append(file_path)
            _log(f"Downloaded image: {filename}", verbose)
        except Exception as e:
            _log(f"Error downloading image {url}: {str(e)}", verbose, is_error=True)
    return local_image_paths 