# socials

## Project Overview

`socials` is a project exploring the integration of AI agents with social media platforms. This repository serves as a personal learning experiment to understand the capabilities and complexities of building AI-powered tools.

**Disclaimer**: This project is developed purely for educational and experimental purposes. Using tools on social media platforms may violate their respective Terms of Service, which could lead to temporary or permanent suspension of your accounts. Users are solely responsible for adhering to platform policies and bear all risks associated with the use of these tools. This project is **not intended for commercial use** or to circumvent platform rules, but rather to learn about the underlying mechanisms and potential of AI agents. Use at your own risk.

## Features

The project currently includes AI agents designed for social media management across several platforms:

### 1. X/Twitter Management
- **Auto-replies**: AI agents designed to learn from a user's writing style to generate contextual and personalized replies to tweets.
- **Scheduled Posting**: Tools for planning and publishing tweets at specified times.
- **Engagement Features**: Capabilities to manage interactions such as likes, retweets, and follows based on predefined criteria.
- **Action Mode**: This mode allows for generating and posting replies to tweets using AI analysis, scraping recent tweets, analyzing them with Gemini AI, and generating contextual replies.
- **Turbin Mode**: Designed for collecting and analyzing tweets, then saving generated replies for manual review and approval. This mode processes tweets and generates AI-powered responses.
- **Eternity Mode**: Focuses on collecting tweets from specific target profiles, analyzing them with Gemini AI, and saving generated replies for approval, enabling targeted profile monitoring.
- **Community Scraping**: Features to collect tweets from specific X communities based on provided community names.
- **Suggesting Engaging Tweets**: AI-driven analysis of scraped community tweets to identify the most engaging content and suggest optimal tweets for interaction.

### 2. YouTube Management
- **Comment Replies**: AI-powered responses to comments on YouTube videos, maintaining context and tone.
- **Video Scheduling**: Tools for scheduling video uploads and publications.
- **Metadata Scraping**: Tools for extracting video metadata for analysis or content optimization.

### 3. Instagram Management
- **Post Scheduling**: Tools for scheduling and publishing of Instagram posts.
- **Auto-replies**: AI-generated responses to comments and direct messages on Instagram.
- **Engagement Tracking**: Features to monitor and analyze engagement metrics for posts.

## Setup and Installation

To get started with `socials`, follow these general steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/arjumal1311/socials.git
    cd socials
    ```

2.  **Initialize a virtual environment**:
    It is highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Profiles**:
    Rename `profiles.sample.py` to `profiles.py` and populate it with your specific social media profiles. This file is crucial for the AI agents to function.
    ```bash
    mv profiles.sample.py profiles.py
    # Edit profiles.py with your configurations
    ```

5.  **Browser Configuration**:
    The project uses `chromium` for browser interaction by default. If you wish to use a different browser (e.g., Chrome, Firefox), you can adjust the settings in `services/support/web_driver_handler.py`.

6.  **Sample Commands**:
    Refer to the `commands.py` file for a list of sample commands to run various tasks for both `replies.py` and `scheduler.py`.

## Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

As an open-source educational project, we encourage collaboration and learning. If you create a derivative work or copy of this project, I kindly request that you also maintain its open-source nature to further foster a collaborative learning environment.
