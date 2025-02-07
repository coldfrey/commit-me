#!/usr/bin/env python3
import os
import logging
import base64
import datetime
import random
import json
import urllib.request
import urllib.error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_random_emoji():
    """Return a random emoji from a predefined list."""
    emojis = ["😃", "🚀", "🎉", "🔥", "✨", "👍", "🥳", "😎", "🤖", "🌟"]
    return random.choice(emojis)

def append_date_time_to_readme(token, repo_name, file_path="README.md"):
    """
    Append the current UTC date/time and a random emoji to the repository's README file.

    The function uses GitHub's API to:
      1. Fetch the current README (its content and SHA)
      2. Append a new line containing the timestamp and emoji
      3. Commit the change with an appropriate commit message

    :param token: GitHub Personal Access Token for authentication.
    :param repo_name: Repository name in 'owner/repo' format.
    :param file_path: Path to the file in the repo to update (default: 'README.md').
    """
    api_url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # 1. GET the current README content and SHA
        request = urllib.request.Request(api_url, headers=headers, method="GET")
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode())
        file_content = base64.b64decode(data["content"]).decode("utf-8")
        file_sha = data["sha"]

        # 2. Append the timestamp and random emoji
        current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        new_line = f"{current_time} {get_random_emoji()}"
        new_content = file_content.rstrip() + "\n" + new_line

        # Encode the new content in Base64
        encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        commit_message = f"Automated update: append timestamp and emoji on {current_time}"

        # 3. PUT updated content back to GitHub
        payload = json.dumps({
            "message": commit_message,
            "content": encoded_content,
            "sha": file_sha
        }).encode("utf-8")

        update_request = urllib.request.Request(api_url, headers=headers, data=payload, method="PUT")
        update_response = urllib.request.urlopen(update_request)
        if update_response.getcode() == 200:
            logger.info("✅ README.md updated successfully at %s", current_time)
        else:
            logger.error("Failed to update README.md. HTTP status: %d", update_response.getcode())

    except urllib.error.HTTPError as e:
        error_message = e.read().decode() if e.fp else str(e)
        logger.error("HTTPError while updating README.md: %s (Status code: %s)", error_message, e.code)
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", str(e))

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    
    Expects the following environment variables to be set:
      - GITHUB_TOKEN: Your GitHub Personal Access Token.
      - GITHUB_REPO: The repository in 'owner/repo' format (e.g. 'coldfrey/commit-me').
    """
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    if not token or not repo:
        logger.error("Missing required environment variables: GITHUB_TOKEN or GITHUB_REPO.")
        return {"statusCode": 500, "body": "Configuration error: missing GitHub credentials."}

    try:
        append_date_time_to_readme(token, repo)
        return {"statusCode": 200, "body": "README updated successfully."}
    except Exception as e:
        return {"statusCode": 500, "body": f"Error updating README: {str(e)}"}

# For local testing
if __name__ == "__main__":
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    if not github_token or not github_repo:
        logger.error("Please set the GITHUB_TOKEN and GITHUB_REPO environment variables before running locally.")
    else:
        append_date_time_to_readme(github_token, github_repo)
