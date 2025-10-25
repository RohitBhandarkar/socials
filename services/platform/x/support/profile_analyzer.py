import re
import time

from datetime import datetime
from rich.console import Console
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.platform.x.support.process_container import process_container
from services.platform.x.support.capture_containers_scroll import capture_containers_and_scroll
from services.support.sheets_util import get_google_sheets_service, create_online_action_mode_sheet, save_action_mode_replies_to_sheet

console = Console()

def _log(message: str, verbose: bool, is_error: bool = False):
    if verbose or is_error:
        log_message = message
        if is_error and not verbose:
            match = re.search(r'(\d{3}\\s+.*?)(?:\\.|\\n|$)', message)
            if match:
                log_message = f"Error: {match.group(1).strip()}"
            else:
                log_message = message.split('\\n')[0].strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "bold red" if is_error else "white"
        console.print(f"[profile_analyzer.py] {timestamp}|[{color}]{log_message}[/{color}]")

def analyze_profile(driver, profile_name: str, target_profile_name: str, verbose: bool = False, status=None):
    _log(f"Starting analysis for target profile: {target_profile_name}", verbose)

    sheet_name = f"{profile_name}_profile_{target_profile_name}"
    _log(f"Google Sheet name: {sheet_name}", verbose)

    service = get_google_sheets_service(verbose=verbose, status=status)
    if not service:
        _log("Failed to get Google Sheets service. Exiting.", verbose, is_error=True)
        return

    create_online_action_mode_sheet(service, profile_name, verbose=verbose, status=status)

    profile_url = f"https://x.com/{target_profile_name}/with_replies"
    driver.get(profile_url)
    _log(f"Navigated to {profile_url}", verbose)

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
    )

    raw_containers = []
    processed_tweet_ids = set()
    no_new_content_count = 0
    scroll_count = 0
    max_scrolls = 20

    _log("Starting to scrape tweets...", verbose)

    while no_new_content_count < 3 and scroll_count < max_scrolls:
        initial_processed_count = len(processed_tweet_ids)
        no_new_content_count, scroll_count, new_containers_found_in_this_pass = capture_containers_and_scroll(
            driver, raw_containers, processed_tweet_ids, no_new_content_count, scroll_count, verbose
        )
        scroll_count += 1
        _log(f"Scrolled {scroll_count} times. New containers this pass: {new_containers_found_in_this_pass}. Total processed: {len(processed_tweet_ids)}", verbose)
        time.sleep(1)

    _log(f"Finished scraping. Total raw containers found: {len(raw_containers)}", verbose)

    all_tweet_data = []
    for container in raw_containers:
        tweet_data = process_container(container, verbose)
        if tweet_data:
            all_tweet_data.append(tweet_data)

    _log(f"Processed {len(all_tweet_data)} unique tweets.", verbose)

    if all_tweet_data:
        save_action_mode_replies_to_sheet(service, profile_name, all_tweet_data, verbose=verbose, status=status)
        _log(f"Successfully saved {len(all_tweet_data)} tweets to Google Sheet '{sheet_name}'.", verbose)
    else:
        _log("No tweets to save to Google Sheet.", verbose)

    _log(f"Profile analysis for {target_profile_name} completed.", verbose)
