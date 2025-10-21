import re
import os
import warnings

from datetime import datetime
from rich.console import Console
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import List, Dict, Any, Optional, Tuple
from services.support.api_call_tracker import APICallTracker

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

console = Console()
api_call_tracker = APICallTracker(log_file="logs/sheets_api_calls_log.json")

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
        console.print(f"[sheets_util.py] {timestamp}|[{color}]{log_message}{quota_str}[/{color}]")
    elif verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = "white"
        console.print(f"[sheets_util.py] {timestamp}|[{color}]{message}[/{color}]")
        if status:
            status.start()
    elif status:
        status.update(message)

def get_google_sheets_service(verbose: bool = False, status=None):
    try:
        if not os.path.exists('credentials/service_account.json'):
            _log("service_account.json file not found", verbose, is_error=True, status=status)
            return None
            
        try:
            credentials = service_account.Credentials.from_service_account_file(
                'credentials/service_account.json',
                scopes=SCOPES
            )
            _log("Successfully loaded credentials", verbose, status=status)
            api_key_suffix = credentials.service_account_email[-4:] if credentials.service_account_email else None
        except Exception as cred_err:
            _log(f"Failed to load credentials: {cred_err}", verbose, is_error=True, status=status)
            return None
    
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
            _log("Successfully built sheets service", verbose, status=status)
            

            can_call, reason = api_call_tracker.can_make_call("sheets", "read", api_key_suffix=api_key_suffix)
            if not can_call:
                _log(f"[RATE LIMIT] Cannot test connection to sheets API: {reason}", verbose, is_error=True, status=status)
                return None

            _log("[HITTING API] Testing connection to sheets API.", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read", api_key_suffix=api_key_suffix), status=status)
            response = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields='spreadsheetId').execute()
            api_call_tracker.record_call("sheets", "read", success=True, response=response)
            _log("Successfully tested connection to sheets API", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read", api_key_suffix=api_key_suffix), status=status)
            
            return service
        except Exception as build_err:
            api_call_tracker.record_call("sheets", "read", success=False, response=build_err)
            _log(f"Failed to build or test service: {build_err}", verbose, is_error=True, api_info=api_call_tracker.get_quot_info("sheets", "read", api_key_suffix=api_key_suffix), status=status)
            return None
            
    except Exception as e:
        _log(f"Error creating Google Sheets service: {e}", verbose, is_error=True, status=status)
        return None

def sanitize_sheet_name(name):
    sanitized = re.sub(r'[\W_]+', '', name)
    sanitized = sanitized[:30]
    return sanitized.lower()


def create_reply_sheet(service, profile_suffix, verbose: bool = False, status=None):
    try:
        sheet_name = f"{sanitize_sheet_name(profile_suffix)}_replied_tweets"
        
        can_call, reason = api_call_tracker.can_make_call("sheets", "read")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot get spreadsheet properties to check for existing sheets: {reason}", verbose, is_error=True, status=status)
            return None

        _log("[HITTING API] Getting spreadsheet properties to check for existing sheets.", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read"), status=status)
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        api_call_tracker.record_call("sheets", "read", success=True, response=spreadsheet_metadata)
        existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet_metadata['sheets']]
        
        if sheet_name not in existing_sheets:
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]
            body = {'requests': requests}

            can_call, reason = api_call_tracker.can_make_call("sheets", "write")
            if not can_call:
                _log(f"[RATE LIMIT] Cannot add new sheet: {reason}", verbose, is_error=True, status=status)
                return None
            
            _log(f"[HITTING API] Adding new sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            api_call_tracker.record_call("sheets", "write", success=True, response=response)

            headers = [['Tweet Date', 'Tweet URL', 'Tweet Text', 'Media URLs', 'Generated Reply', 'Posted Date', 'Approved', 'Likes', 'Retweets', 'Replies', 'Views', 'Bookmarks']]
            
            can_call, reason = api_call_tracker.can_make_call("sheets", "write")
            if not can_call:
                _log(f"[RATE LIMIT] Cannot update headers for new sheet: {reason}", verbose, is_error=True, status=status)
                return None

            _log(f"[HITTING API] Updating headers for new sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
            response = service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{sheet_name}!A1:L1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            api_call_tracker.record_call("sheets", "write", success=True, response=response)
        return sheet_name
    except Exception as e:
        _log(f"Error creating reply sheet: {str(e)}", verbose, is_error=True, status=status)
        api_call_tracker.record_call("sheets", "write", success=False, response=e)
        return None

def get_generated_replies(service, sheet_name, verbose: bool = False, status=None):
    try:
        _log(f"Fetching replies from sheet: {sheet_name}", verbose, status=status)

        can_call, reason = api_call_tracker.can_make_call("sheets", "read")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot get spreadsheet properties to check for existing sheets: {reason}", verbose, is_error=True, status=status)
            return []

        _log("[HITTING API] Getting spreadsheet properties to check for existing sheets.", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read"), status=status)
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        api_call_tracker.record_call("sheets", "read", success=True, response=spreadsheet_metadata)
        existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet_metadata['sheets']]

        if sheet_name not in existing_sheets:
            create_reply_sheet(service, sheet_name.split('_')[0], verbose)
        
        can_call, reason = api_call_tracker.can_make_call("sheets", "read")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot get values from sheet: {reason}", verbose, is_error=True, status=status)
            return []

        _log(f"[HITTING API] Getting values from sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read"), status=status)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{sheet_name}!A2:L'
        ).execute()
        api_call_tracker.record_call("sheets", "read", success=True, response=result)

        if 'values' in result:
            replies = []
            for row in result['values']:
                while len(row) < 12:
                    row.append('')
                replies.append({
                    'tweet_date': row[0],
                    'tweet_url': row[1],
                    'tweet_text': row[2],
                    'media_urls': row[3],
                    'reply': row[4],
                    'posted_date': row[5],
                    'approved': row[6] == 'Yes',
                    'likes': int(row[7]) if row[7].isdigit() else 0,
                    'retweets': int(row[8]) if row[8].isdigit() else 0,
                    'replies': int(row[9]) if row[9].isdigit() else 0,
                    'views': int(row[10]) if row[10].isdigit() else 0,
                    'bookmarks': int(row[11]) if row[11].isdigit() else 0
                })
            return replies
        return []
    except Exception as e:
        _log(f"Error fetching replies: {str(e)}", verbose, is_error=True, status=status)
        api_call_tracker.record_call("sheets", "read", success=False, response=e)
        return []


def create_online_action_mode_sheet(service, profile_name: str, verbose: bool = False, status=None) -> Optional[str]:
    try:
        sheet_name = f"{sanitize_sheet_name(profile_name)}_online_replies"
        
        can_call, reason = api_call_tracker.can_make_call("sheets", "read")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot get spreadsheet properties to check for existing sheets: {reason}", verbose, is_error=True, status=status)
            return None

        _log("[HITTING API] Getting spreadsheet properties to check for existing sheets.", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read"), status=status)
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        api_call_tracker.record_call("sheets", "read", success=True, response=spreadsheet_metadata)
        existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet_metadata['sheets']]

        if sheet_name not in existing_sheets:
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]

            body = {'requests': requests}

            can_call, reason = api_call_tracker.can_make_call("sheets", "write")
            if not can_call:
                _log(f"[RATE LIMIT] Cannot add new sheet: {reason}", verbose, is_error=True, status=status)
                return None

            _log(f"[HITTING API] Adding new sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            api_call_tracker.record_call("sheets", "write", success=True, response=response)

            headers = [['Tweet ID', 'Tweet Date', 'Tweet URL', 'Tweet Text', 'Media URLs', 'Generated Reply', 'Status', 'Posted Date', 'Scraped Date', 'Run Number', 'Profile Image URL', 'Likes', 'Retweets', 'Replies', 'Views', 'Bookmarks', 'Profile']]
            
            can_call, reason = api_call_tracker.can_make_call("sheets", "write")
            if not can_call:
                _log(f"[RATE LIMIT] Cannot update headers for new sheet: {reason}", verbose, is_error=True, status=status)
                return None

            _log(f"[HITTING API] Updating headers for new sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
            response = service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{sheet_name}!A1:Q1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            api_call_tracker.record_call("sheets", "write", success=True, response=response)
            _log(f"Created new Google Sheet: {sheet_name}", verbose, status=status)

        return sheet_name

    except Exception as e:
        _log(f"Error creating online action mode sheet: {e}", verbose, is_error=True, status=status)
        api_call_tracker.record_call("sheets", "write", success=False, response=e)
        return None

def save_action_mode_replies_to_sheet(service, profile_name: str, replies_data: List[Dict[str, Any]], verbose: bool = False, status=None) -> bool:
    try:
        sheet_name = create_online_action_mode_sheet(service, profile_name, verbose, status=status)
        if not sheet_name:
            return False

        existing_replies = get_online_action_mode_replies(service, profile_name, verbose=verbose, status=status)
        existing_tweet_ids = {reply_item['tweet_id']: idx for idx, (reply_item, _) in enumerate(existing_replies)}

        new_rows = []
        update_operations = []

        for reply_item in replies_data:
            tweet_id = reply_item.get('tweet_id')
            if not tweet_id:
                _log(f"Skipping reply item with no tweet_id: {reply_item}", verbose, is_error=True, status=status)
                continue

            row = [
                tweet_id,
                reply_item.get('tweet_date', ''),
                reply_item.get('tweet_url', ''),
                reply_item.get('tweet_text', ''),
                ';'.join(reply_item.get('media_files', [])) if isinstance(reply_item.get('media_files'), list) else reply_item.get('media_files', ''),
                reply_item.get('generated_reply', ''),
                reply_item.get('status', 'ready_for_approval'),
                reply_item.get('posted_date', ''),
                reply_item.get('scraped_date', ''),
                reply_item.get('run_number', ''),
                reply_item.get('profile_image_url', ''),
                reply_item.get('likes', ''),
                reply_item.get('retweets', ''),
                reply_item.get('replies', ''),
                reply_item.get('views', ''),
                reply_item.get('bookmarks', ''),
                reply_item.get('profile', '')
            ]

            if tweet_id in existing_tweet_ids:
                row_idx = existing_tweet_ids[tweet_id] + 2
                update_operations.append({
                    'range': f'{sheet_name}!A{row_idx}:Q{row_idx}',
                    'values': [row]
                })
            else:
                new_rows.append(row)
        
        if update_operations:
            body = {
                'valueInputOption': 'RAW',
                'data': update_operations
            }
            can_call, reason = api_call_tracker.can_make_call("sheets", "write")
            if not can_call:
                _log(f"[RATE LIMIT] Cannot batch update replies: {reason}", verbose, is_error=True, status=status)
                return False

            _log(f"[HITTING API] Batch updating {len(update_operations)} replies in sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
            response = service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            api_call_tracker.record_call("sheets", "write", success=True, response=response)

        if new_rows:
            body = {
                'values': new_rows
            }
            can_call, reason = api_call_tracker.can_make_call("sheets", "write")
            if not can_call:
                _log(f"[RATE LIMIT] Cannot append new replies: {reason}", verbose, is_error=True, status=status)
                return False

            _log(f"[HITTING API] Appending {len(new_rows)} new replies to sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
            response = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f'{sheet_name}!A2:Q',
                valueInputOption='RAW',
                body=body
            ).execute()
            api_call_tracker.record_call("sheets", "write", success=True, response=response)
        
        _log(f"Successfully saved/updated {len(replies_data)} replies to sheet: {sheet_name}", verbose, status=status)
        return True

    except Exception as e:
        _log(f"Error saving action mode replies to sheet: {e}", verbose, is_error=True, status=status)
        api_call_tracker.record_call("sheets", "write", success=False, response=e)
        return False

def get_online_action_mode_replies(service, profile_name: str, target_date: Optional[str] = None, run_number: Optional[int] = None, verbose: bool = False, status=None) -> List[Tuple[Dict[str, Any], int]]:
    try:
        sheet_name = f"{sanitize_sheet_name(profile_name)}_online_replies"
        
        can_call, reason = api_call_tracker.can_make_call("sheets", "read")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot get spreadsheet properties to check for existing sheets: {reason}", verbose, is_error=True, status=status)
            return []

        _log("[HITTING API] Getting spreadsheet properties to check for existing sheets.", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read"), status=status)
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        api_call_tracker.record_call("sheets", "read", success=True, response=spreadsheet_metadata)
        existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet_metadata['sheets']]

        if sheet_name not in existing_sheets:
            _log(f"Sheet {sheet_name} not found. Returning empty list.", verbose, is_error=True, status=status)
            return []

        can_call, reason = api_call_tracker.can_make_call("sheets", "read")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot get values from sheet: {reason}", verbose, is_error=True, status=status)
            return []

        _log(f"[HITTING API] Getting values from sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read"), status=status)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{sheet_name}!A2:Q'
        ).execute()
        api_call_tracker.record_call("sheets", "read", success=True, response=result)
        
        values = result.get('values', [])
        replies_with_indices = []

        for idx, row in enumerate(values):
            row_idx = idx + 2
            while len(row) < 17:
                row.append('')
            reply_item = {
                'tweet_id': row[0],
                'tweet_date': row[1],
                'tweet_url': row[2],
                'tweet_text': row[3],
                'media_files': row[4],
                'generated_reply': row[5],
                'status': row[6],
                'posted_date': row[7],
                'scraped_date': row[8],
                'run_number': int(row[9]) if row[9].isdigit() else None,
                'profile_image_url': row[10],
                'likes': int(row[11]) if row[11].isdigit() else 0,
                'retweets': int(row[12]) if row[12].isdigit() else 0,
                'replies': int(row[13]) if row[13].isdigit() else 0,
                'views': int(row[14]) if row[14].isdigit() else 0,
                'bookmarks': int(row[15]) if row[15].isdigit() else 0,
                'profile': row[16]
            }
            replies_with_indices.append((reply_item, row_idx))
        
        if target_date:
            replies_with_indices = [item for item in replies_with_indices if item[0].get('scraped_date', '').startswith(target_date)]
        
        if run_number:
            replies_with_indices = [item for item in replies_with_indices if item[0].get('run_number') == run_number]

        return replies_with_indices

    except Exception as e:
        _log(f"Error fetching online action mode replies: {e}", verbose, is_error=True, status=status)
        api_call_tracker.record_call("sheets", "read", success=False, response=e)
        return []

def batch_update_online_action_mode_replies(service, profile_name: str, updates: List[Dict[str, Any]], verbose: bool = False, status=None) -> bool:
    try:
        sheet_name = f"{sanitize_sheet_name(profile_name)}_online_replies"
        
        can_call, reason = api_call_tracker.can_make_call("sheets", "read")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot get spreadsheet properties to check for existing sheets: {reason}", verbose, is_error=True, status=status)
            return False

        _log("[HITTING API] Getting spreadsheet properties to check for existing sheets.", verbose, api_info=api_call_tracker.get_quot_info("sheets", "read"), status=status)
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        api_call_tracker.record_call("sheets", "read", success=True, response=spreadsheet_metadata)
        existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet_metadata['sheets']]

        if sheet_name not in existing_sheets:
            _log(f"Sheet {sheet_name} not found. Cannot perform batch update.", verbose, is_error=True, status=status)
            return False

        if not updates:
            _log("No updates to perform for batch update.", verbose, status=status)
            return True

        body = {
            'valueInputOption': 'RAW',
            'data': updates
        }

        can_call, reason = api_call_tracker.can_make_call("sheets", "write")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot perform batch update: {reason}", verbose, is_error=True, status=status)
            return False

        _log(f"[HITTING API] Batch updating {len(updates)} replies in sheet {sheet_name}.", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
        response = service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        api_call_tracker.record_call("sheets", "write", success=True, response=response)
        
        _log(f"Successfully performed batch update for {len(updates)} replies in sheet {sheet_name}.", verbose, status=status)
        return True

    except Exception as e:
        _log(f"Error performing batch update for online action mode replies: {e}", verbose, is_error=True, status=status)
        api_call_tracker.record_call("sheets", "write", success=False, response=e)
        return False 

def save_posted_reply_to_replied_tweets_sheet(service, profile_name: str, reply_item: Dict[str, Any], verbose: bool = False, status=None) -> bool:
    try:
        sheet_name = f"{sanitize_sheet_name(profile_name)}_replied_tweets"
        create_reply_sheet(service, profile_name, verbose)

        row = [
            reply_item.get('tweet_date', ''),
            reply_item.get('tweet_url', ''),
            reply_item.get('tweet_text', ''),
            ';'.join(reply_item.get('media_files', [])) if isinstance(reply_item.get('media_files'), list) else reply_item.get('media_files', ''),
            reply_item.get('generated_reply', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Yes',
            reply_item.get('likes', ''),
            reply_item.get('retweets', ''),
            reply_item.get('replies', ''),
            reply_item.get('views', ''),
            reply_item.get('bookmarks', '')
        ]

        body = {
            'values': [row]
        }
        can_call, reason = api_call_tracker.can_make_call("sheets", "write")
        if not can_call:
            _log(f"[RATE LIMIT] Cannot append posted reply to sheet: {reason}", verbose, is_error=True, status=status)
            return False

        _log(f"[HITTING API] Appending posted reply to sheet: {sheet_name}", verbose, api_info=api_call_tracker.get_quot_info("sheets", "write"), status=status)
        response = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{sheet_name}!A2:L',
            valueInputOption='RAW',
            body=body
        ).execute()
        api_call_tracker.record_call("sheets", "write", success=True, response=response)
        
        _log(f"Successfully saved posted reply to sheet: {sheet_name}", verbose, status=status)
        return True

    except Exception as e:
        _log(f"Error saving posted reply to replied tweets sheet: {e}", verbose, is_error=True, status=status)
        api_call_tracker.record_call("sheets", "write", success=False, response=e)
        return False 