import re
import time

from datetime import datetime
from rich.console import Console
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

console = Console()

def _log(message: str, verbose: bool, status=None, is_error: bool = False):
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
        console.print(f"[post_to_community.py] {timestamp}|[{color}]{log_message}[/{color}]")
    elif status:
        status.update(message)

def post_to_community_tweet(driver, tweet_text, community_name, status=None, verbose: bool = False):
    try:
        if status:
            _log("Navigating to tweet compose page...", verbose, status)
        else:
            _log("Navigating to tweet compose page...", verbose)
        driver.get('https://x.com/compose/tweet')
        time.sleep(3)

        tweet_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
        )
        tweet_input.clear()
        tweet_input.send_keys(tweet_text)
        time.sleep(2)

        if status:
            _log(f"Selecting community '{community_name}'...", verbose, status)
        else:
            _log(f"Selecting community '{community_name}'...", verbose)
        
        choose_audience_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Choose audience"]'))
        )
        choose_audience_button.click()
        time.sleep(2)

        community_xpath = f"//span[text()='{community_name}']"
        community_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, community_xpath))
        )
        community_element.click()
        time.sleep(2)
        
        if status:
            _log("Clicking post button...", verbose, status)
        else:
            _log("Clicking post button...", verbose)
        post_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButton"]'))
        )
        post_button.click()
        time.sleep(3)

        driver.get('https://x.com')
        time.sleep(3)
        if status:
            _log(f"Successfully posted tweet to community '{community_name}'", verbose, status)
        else:
            _log(f"Successfully posted tweet to community '{community_name}'", verbose)
        return True
    except Exception as e:
        _log(f"Failed to post tweet to community: {e}", verbose, is_error=True)
        return False
