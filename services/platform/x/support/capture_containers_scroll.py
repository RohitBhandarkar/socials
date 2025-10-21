import re
import time

from datetime import datetime
from rich.console import Console
from selenium.webdriver.common.by import By

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
        console.print(f"[capture_containers_scroll.py] {timestamp}|[{color}]{log_message}[/{color}]")

def capture_containers_and_scroll(driver, raw_containers, processed_tweet_ids, no_new_content_count, scroll_count, verbose: bool = False):
    tweet_elements = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
    _log(f"DEBUG: Found {len(tweet_elements)} tweet articles.", verbose)

    new_containers_found_in_this_pass = 0
    for tweet_element in tweet_elements:
        try:
            links = tweet_element.find_elements(By.CSS_SELECTOR, 'a[href*="/status/"]')
            
            if not links:
                _log(f"DEBUG: Tweet article has no /status/ link. Text: {tweet_element.text[:50]}...", verbose, is_error=False)
                continue
            
            url = None
            for link in links:
                href = link.get_attribute("href")
                if href and '/status/' in href and '/analytics' not in href:
                    url = href
                    break
            
            if not url:
                _log(f"DEBUG: No valid tweet URL found in article. Text: {tweet_element.text[:50]}...", verbose, is_error=False)
                continue

            tweet_id = url.split("/status/")[1].split("?")[0]
            if tweet_id in processed_tweet_ids:
                _log(f"DEBUG: Skipping already processed tweet ID: {tweet_id}", verbose, is_error=False)
                continue

            profile_image_url = ""
            try:
                profile_image_element = tweet_element.find_element(By.CSS_SELECTOR, 'a[href^="/"] img')
                profile_image_url = profile_image_element.get_attribute('src')
                _log(f"DEBUG (capture_containers_and_scroll): Extracted profile_image_url: {profile_image_url}", verbose)
            except Exception as img_e:
                _log(f"DEBUG: Could not extract profile image for tweet ID {tweet_id}: {img_e}", verbose, is_error=False)

            container_html = tweet_element.get_attribute('outerHTML')
            container_text = tweet_element.text

            _log(f"DEBUG: New tweet found - URL: {url}, ID: {tweet_id}. Total processed: {len(processed_tweet_ids) + 1}", verbose)
            processed_tweet_ids.add(tweet_id)
            raw_containers.append({
                'html': container_html,
                'text': container_text,
                'url': url,
                'tweet_id': tweet_id,
                'profile_image_url': profile_image_url
            })
            new_containers_found_in_this_pass += 1
        except Exception as e:
            _log(f"[ERROR] Exception processing tweet article: {e}", verbose, is_error=True)
            continue

    viewport_height = driver.execute_script("return window.innerHeight")
    current_position = driver.execute_script("return window.pageYOffset")
    scroll_amount = viewport_height * 0.8

    driver.execute_script(f"window.scrollTo(0, {current_position + scroll_amount})")
    time.sleep(0.5)

    if new_containers_found_in_this_pass == 0:
        no_new_content_count += 1
    else:
        no_new_content_count = 0
    
    return no_new_content_count, scroll_count, new_containers_found_in_this_pass