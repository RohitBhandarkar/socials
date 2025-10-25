import re
import os
import json
import google.generativeai as genai

from profiles import PROFILES

from datetime import datetime
from rich.console import Console
from typing import List, Dict, Any, Optional
from services.support.api_key_pool import APIKeyPool
from services.support.rate_limiter import RateLimiter
from services.support.path_config import get_community_dir

console = Console()
api_key_pool = APIKeyPool()
rate_limiter = RateLimiter()

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
        console.print(f"[tweet_analyzer.py] {timestamp}|[{color}]{log_message}[/{color}]")

def analyze_community_tweets_for_engagement(profile_key: str, community_name: str, api_key: Optional[str] = None, verbose: bool = False) -> List[Dict[str, Any]]:
    if api_key:
        api_key_pool.set_explicit_key(api_key)
    
    gemini_api_key = api_key_pool.get_key()
    if not gemini_api_key:
        _log("Error: No Gemini API key available.", verbose, is_error=True)
        return []

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    community_folder = get_community_dir(profile_key)
    
    latest_json_file = None
    latest_timestamp = None

    if not os.path.exists(community_folder):
        _log(f"Community folder '{community_folder}' not found. Please ensure scraping was done correctly for profile '{profile_key}'.", verbose, is_error=True)
        return []

    for f in os.listdir(community_folder):
        if f.startswith(f"{community_name}_") and f.endswith(".json"):
            try:
                parts = f.replace(f"{community_name}_", "").replace(".json", "").split("_")
                if len(parts) == 2:
                    timestamp_str = parts[0] + parts[1]
                else:
                    timestamp_str = f.replace(f"{community_name}_", "").replace(".json", "")
                
                if len(timestamp_str) == 14 or len(timestamp_str) == 15 and '_' in timestamp_str:
                    current_timestamp = datetime.strptime(timestamp_str.replace('_', ''), "%Y%m%d%H%M%S")
                    if latest_timestamp is None or current_timestamp > latest_timestamp:
                        latest_timestamp = current_timestamp
                        latest_json_file = os.path.join(community_folder, f)
            except ValueError:
                continue
    
    if not latest_json_file:
        _log(f"No community JSON file found for '{community_name}' in '{profile_key}'. Please scrape first.", verbose, is_error=True)
        return []

    _log(f"Loading tweets from: {latest_json_file}", verbose)
    with open(latest_json_file, 'r', encoding='utf-8') as f:
        tweets_data = json.load(f)

    if not tweets_data:
        _log("No tweets found in the loaded file.", verbose, is_error=False)
        return []

    _log(f"Analyzing {len(tweets_data)} tweets for engagement...", verbose)

    if 'engagement_analysis_prompt' not in PROFILES[profile_key]:
        _log(f"Error: 'engagement_analysis_prompt' not found for profile '{profile_key}'. Please define it in profiles.py.", verbose, is_error=True)
        return []
    else:
        engagement_prompt = PROFILES[profile_key]['engagement_analysis_prompt']

    prompt_parts = [engagement_prompt, "\n\nTweets for analysis:"]
    for i, tweet in enumerate(tweets_data):
        prompt_parts.append(f"\nTweet {i+1}:")
        prompt_parts.append(f"Text: {tweet.get('tweet_text', 'N/A')}")
        prompt_parts.append(f"Engagement (likes, comments, retweets): {tweet.get('engagement', 'N/A')}")
        prompt_parts.append(f"Media: {', '.join(tweet.get('media_files', []))}")
        prompt_parts.append(f"Author: {tweet.get('author_handle', 'N/A')}")
        prompt_parts.append(f"URL: {tweet.get('tweet_url', 'N/A')}")
        prompt_parts.append(f"Timestamp: {tweet.get('timestamp', 'N/A')}")

    try:
        rate_limiter.wait_if_needed(gemini_api_key)
        response = model.generate_content(prompt_parts)
        
        if response and response.text:
            _log("Engagement analysis complete.", verbose)
            return [{"suggestion": response.text}]
        else:
            _log("Gemini returned no content for engagement analysis.", verbose, is_error=False)
            return []
    except Exception as e:
        _log(f"Error during Gemini engagement analysis: {e}", verbose, is_error=True)
        return []
