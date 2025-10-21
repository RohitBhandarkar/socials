import re
import os
import time

from datetime import datetime
from rich.console import Console
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from services.support.web_driver_handler import setup_driver
from selenium.webdriver.support import expected_conditions as EC

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
        console.print(f"[video_download.py] {timestamp}|[{color}]{log_message}[/{color}]")

def download_twitter_videos(tweet_urls, profile_name="Default", headless=True, verbose: bool = False):
    user_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'browser-data', profile_name))
    driver, setup_messages = setup_driver(user_data_dir, profile=profile_name, headless=headless, verbose=verbose)
    for msg in setup_messages:
        _log(msg, verbose)
        time.sleep(0.1)

    time.sleep(10)
    original_window = driver.current_window_handle
    current_tabs = []
    download_dir = '/home/atg/Documents/socials/videos' 
    
    os.makedirs(download_dir, exist_ok=True)

    initial_files = set(os.listdir(download_dir))
    new_file = None
    
    for url in tweet_urls:
        _log(f"Processing Downloads for URL: {url}", verbose)
        _log(f"Downloading video from: {url}", verbose)
        try:
            driver.execute_script("window.open('');")
            new_tab = driver.window_handles[-1]
            current_tabs.append(new_tab)
            driver.switch_to.window(new_tab)
            driver.get('https://savetwitter.net/en')
            time.sleep(2)
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 's_input'))
            )
            driver.execute_script("arguments[0].value = arguments[1];", input_field, url)
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'btn-red'))
            )
            download_button.click()
            
            try:
                error_div = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'error')]//p[contains(text(), 'Video not found')]" ))
                )
                _log(f"Video not found for URL: {url}, skipping to next URL", verbose, is_error=False)
                continue
            except TimeoutException:
                try:
                    best_quality_link = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'tw-button-dl')][1]" ))
                    )
                    best_quality_link.click()
                    time.sleep(2)
                except TimeoutException:
                    _log(f"Download already initiated for {url}, continuing to next URL", verbose)
            
            max_wait_time = 20
            wait_interval = 2
            waited_time = 0
            
            while waited_time < max_wait_time:
                current_files = set(os.listdir(download_dir))
                new_files = current_files - initial_files
                
                downloading_files = [f for f in new_files if f.endswith('.crdownload') or f.endswith('.tmp')]
                
                if downloading_files:
                    _log(f"Download still in progress: {downloading_files}", verbose)
                    time.sleep(wait_interval)
                    waited_time += wait_interval
                    continue
                
                completed_files = [f for f in new_files if f.endswith('.mp4')]
                if completed_files:
                    new_file = completed_files[0]
                    break
                
                time.sleep(wait_interval)
                waited_time += wait_interval
            
            if new_file is None:
                _log(f"Download timed out for URL: {url}", verbose, is_error=False)
                continue
                
            _log(f"New file downloaded: {new_file}", verbose)
            
            initial_files.add(new_file)
            
            tweet_id = url.split('/')[-1]
            mapping = f'{new_file} -> {tweet_id}\n'

            with open('tmp/downloaded_videos.txt', 'a') as f:
                f.write(mapping)
            _log(f"Video downloaded and mapped: {mapping.strip()}", verbose)

        except Exception as e:
            _log(f"Error processing URL {url}: {str(e)}", verbose, is_error=True)
        finally:
            try:
                driver.close()
                if new_tab in current_tabs:
                    current_tabs.remove(new_tab)
            except:
                pass
            driver.switch_to.window(original_window)

    driver.quit()
    if new_file:
        return os.path.join(download_dir, new_file)
    else:
        return None
