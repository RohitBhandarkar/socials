import os
import sys
import json
import time
import subprocess

from profiles import PROFILES

from datetime import datetime
from rich.status import Status
from rich.console import Console
from services.support import path_config

console = Console()

def load_schedule(profile_name: str) -> list:
    schedule_path = path_config.get_schedule_file_path(profile_name)
    if not os.path.exists(schedule_path):
        return []
    try:
        with open(schedule_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_schedule(profile_name: str, schedule: list) -> None:
    schedule_path = path_config.get_schedule_file_path(profile_name)
    tmp_path = schedule_path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, schedule_path)


def post_tweet(profile_key: str, tweet_text: str, community_name: str = None) -> bool:
    cmd = [
        "python3",
        os.path.join(os.path.dirname(__file__), '..', 'replies.py'),
        "--profile", profile_key,
    ]
    if community_name:
        cmd.extend([
            "--post-to-community",
            "--post-to-community-tweet", tweet_text,
            "--community-name", community_name,
        ])
    else:
        cmd.extend([
            "--post-tweet", tweet_text,
        ])

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            console.print(f"[dim white]{result.stdout.strip()}[/dim white]")
        if result.stderr:
            console.print(f"[dim yellow]{result.stderr.strip()}[/dim yellow]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Failed to post tweet for profile '{profile_key}': {e.stderr}[/bold red]")
        return False


def process_profile(profile_key: str, start_dt: datetime, verbose: bool = False) -> int:
    posts_to_process = load_schedule(profile_key)
    if not isinstance(posts_to_process, list):
        if verbose:
            console.print(f"[dim white]{profile_key}: schedule not found or invalid at {path_config.get_schedule_file_path(profile_key)} (Expected a list, got {type(posts_to_process)}).[/dim white]")
        return 0

    if verbose:
        console.print(f"[dim white]{profile_key}: scanning schedule at {path_config.get_schedule_file_path(profile_key)} (start_dt={start_dt.isoformat()})[/dim white]")

    posted_count = 0
    updated_posts = []

    for post in posts_to_process:
        if not isinstance(post, dict):
            if verbose:
                console.print(f"[dim white]{profile_key}: non-dict post, skipping[/dim white]")
            updated_posts.append(post) # Keep non-dict posts in the list
            continue

        community_name = post.get("community-tweet")
        already_posted = post.get("community_posted") is True
        tweet_text = post.get("x_captions", "").strip() or post.get("scheduled_tweet", "").strip()
        scheduled_time_str = post.get("scheduled_time", "").strip()

        if not scheduled_time_str:
            if verbose:
                console.print(f"[dim white]{profile_key}: post has no scheduled_time, skipping[/dim white]")
            updated_posts.append(post)
            continue

        try:
            post_dt = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                post_dt = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                if verbose:
                    console.print(f"[dim white]{profile_key}: invalid scheduled_time format '{scheduled_time_str}', skipping[/dim white]")
                updated_posts.append(post)
                continue

        # Only consider posts for the current day
        if post_dt.date() != datetime.now().date():
            if verbose:
                console.print(f"[dim white]{profile_key}: NOT-TODAY skip {post_dt.isoformat()} (community={community_name})[/dim white]")
            updated_posts.append(post)
            continue

        if post_dt < start_dt:
            if verbose:
                console.print(f"[dim white]{profile_key}: BEFORE-START skip {post_dt.isoformat()} < {start_dt.isoformat()} (community={community_name})[/dim white]")
            updated_posts.append(post)
            continue

        now_dt = datetime.now()
        if post_dt > now_dt:
            if verbose:
                console.print(f"[dim white]{profile_key}: WAIT {post_dt.isoformat()} > {now_dt.isoformat()} (community={community_name})[/dim white]")
            updated_posts.append(post)
            continue

        if already_posted:
            if verbose:
                console.print(f"[dim white]{profile_key}: already posted item at {post_dt.isoformat()}, skipping[/dim white]")
            updated_posts.append(post)
            continue

        if not tweet_text:
            console.print(f"[yellow]Skipping empty tweet for '{profile_key}' at {post_dt.strftime('%Y-%m-%d %H:%M')}.[/yellow]")
            post["community_posted"] = True
            post["community_posted_at"] = datetime.now().isoformat()
            updated_posts.append(post)
            continue
        
        if community_name:
            console.print(f"[white]Posting community tweet for '{profile_key}' in '{community_name}' at {post_dt.strftime('%Y-%m-%d %H:%M')}.[/white]")
            success = post_tweet(profile_key, tweet_text, community_name)
        else:
            console.print(f"[white]Posting regular tweet for '{profile_key}' at {post_dt.strftime('%Y-%m-%d %H:%M')}.[/white]")
            success = post_tweet(profile_key, tweet_text)

        if success:
            posted_count += 1
            post["community_posted"] = True
            post["community_posted_at"] = datetime.now().isoformat()
        updated_posts.append(post)

    if posted_count > 0:
        save_schedule(profile_key, updated_posts)

    return posted_count


def has_future_posts(profile_key: str, start_dt: datetime, verbose: bool = False) -> bool:
    posts_to_check = load_schedule(profile_key)
    if not isinstance(posts_to_check, list):
        return False

    now_dt = datetime.now()

    for post in posts_to_check:
        if not isinstance(post, dict):
            continue

        is_community_tweet = post.get("community-tweet")
        
        if post.get("community_posted") is True:
            continue

        scheduled_time_str = post.get("scheduled_time", "").strip()
        if not scheduled_time_str:
            continue

        try:
            post_dt = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                post_dt = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                continue

        # Only consider posts for the current day
        if post_dt.date() != datetime.now().date():
            if verbose:
                console.print(f"[dim white]{profile_key}: NOT-TODAY skip {post_dt.isoformat()} (community={is_community_tweet})[/dim white]")
            continue

        if post_dt >= start_dt and post_dt >= now_dt:
            if verbose:
                console.print(f"[dim white]{profile_key}: future post pending at {post_dt.isoformat()} (community={is_community_tweet})[/dim white]")
            return True
    return False


def run_watcher(profile_keys: list[str], interval_seconds: int, run_once: bool, verbose: bool = False):
    if not profile_keys:
        console.print("[bold red]No profiles provided.[/bold red]")
        sys.exit(1)

    for key in profile_keys:
        if key not in PROFILES:
            console.print(f"[yellow]Warning: Profile key '{key}' not found in PROFILES. Continuing...[/yellow]")

    console.print("[white]Community Post Watcher started. Press Ctrl+C to stop.[/white]")

    def scan_and_post() -> tuple[int, bool]:
        total_posted = 0
        any_future_pending = False
        with Status("[white]Scanning schedules for community tweets...[/white]", spinner="dots", console=console) as status:
            for key in profile_keys:
                status.update(f"[white]Processing {key}...[/white]")
                try:
                    total_posted += process_profile(key, start_dt, verbose=verbose)
                    if has_future_posts(key, start_dt, verbose=verbose):
                        any_future_pending = True
                except Exception as e:
                    console.print(f"[bold red]Error processing profile '{key}': {e}[/bold red]")
            status.stop()
        if total_posted:
            console.print(f"[green]Posted {total_posted} post(s).[/green]")
        else:
            console.print("[dim white]No posts to make.[/dim white]")
        return total_posted, any_future_pending

    if run_once:
        _, any_future = scan_and_post()
        if not any_future:
            console.print("[white]No future posts remaining. Exiting.[/white]")
        return

    start_dt = datetime.now()
    try:
        while True:
            _, any_future = scan_and_post()
            if not any_future:
                console.print("[white]No future posts remaining. Exiting watcher.")
                break
            wait_seconds = max(5, interval_seconds)
            with Status("[white]Waiting before next scan...[/white]", spinner="dots", console=console) as wait_status:
                for remaining in range(wait_seconds, 0, -1):
                    wait_status.update(f"[white]Waiting {remaining} seconds before next scan...[/white]")
                    time.sleep(1)
                wait_status.stop()
    except KeyboardInterrupt:
        console.print("[white]Community Post Watcher stopped.[/white]")
