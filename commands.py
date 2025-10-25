# action mode
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --action-review --ignore-video-tweets --verbose --community-name {community_name}

# services/platform/x/replies.py commands
# Profile operations
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --check --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --clear --verbose

# Turbin mode
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --turbin-mode --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --review --port {port_number} --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --post-approved --post-mode turbin --limit {number} --verbose

# Eternity mode
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --eternity-mode --verbose --api-key {gemini_api_key} --eternity-browser {browser_profile_name} --eternity-max-tweets {number}
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --eternity-review --port {port_number} --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --post-approved --post-mode eternity --limit {number} --verbose

# Community scraping and analysis
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --community-scrape --community-name "{community_name}" --max-tweets {number} --browser-profile {browser_profile_name} --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --suggest-engaging-tweets --community-name "{community_name}" --api-key {gemini_api_key} --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --post-to-community --community-name "{community_name}" --post-to-community-tweet "{tweet_text}" --verbose

# Action mode
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --action-mode --ignore-video-tweets --run-number {number} --community-name "{community_name}" --post-via-api --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --action-generate --ignore-video-tweets --run-number {number} --community-name "{community_name}" --post-via-api --verbose --api-key {gemini_api_key}
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --action-review --ignore-video-tweets --run-number {number} --community-name "{community_name}" --post-via-api --verbose --api-key {gemini_api_key} --online
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --action-review --ignore-video-tweets --run-number {number} --community-name "{community_name}" --post-via-api --verbose --api-key {gemini_api_key} --action-port {port_number}
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --post-action-approved --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --post-action-approved-sequential --verbose --run-number {number} --post-via-api
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/replies.py --profile {profile_name} --specific-target-profiles "{profile_key}" --verbose --api-key {gemini_api_key} --run-number {number} --ignore-video-tweets

# Directory Initialization
# source venv/bin/activate && PYTHONPATH=. python -c "from services.support.path_config import initialize_directories; initialize_directories()" --verbose

# services/platform/x/scheduler.py commands
# Profile operations
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --display-tweets --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --clear-media --verbose

# Scheduling operations
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --generate-sample --gap-type random --min-gap-hours {hours} --min-gap-minutes {minutes} --max-gap-hours {hours} --max-gap-minutes {minutes} --tweet-text "{tweet_text}" --start-image-number {number} --num-days {number} --start-date {YYYY-MM-DD} --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --generate-sample --gap-type fixed --fixed-gap-hours {hours} --fixed-gap-minutes {minutes} --tweet-text "{tweet_text}" --start-image-number {number} --num-days {number} --start-date {YYYY-MM-DD} --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --process-tweets --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --sched-tom --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --try-mp4 --verbose
# source venv/bin/activate && PYTHONPATH=. python services/platform/x/scheduler.py --profile {profile_name} --generate-captions --gemini-api-key {gemini_api_key} --verbose