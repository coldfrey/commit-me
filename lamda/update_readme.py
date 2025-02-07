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
    Append the current UTC date/time and a random emoji to the README file of the given GitHub repo.

    :param token: GitHub Personal Access Token for authentication.
    :param repo_name: Repository name in 'owner/repo' format.
    :param file_path: Path to the file in the repo to update (default: 'README.md').
    """
    # GitHub API URL for repository content
    api_url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
    # Authorization header with token
    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}

    try:
        # 1. GET the current file content and SHA
        request = urllib.request.Request(api_url, headers=headers, method="GET")
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode())
        # Decode the file content from Base64
        file_content = base64.b64decode(data["content"]).decode("utf-8")
        file_sha = data["sha"]  # SHA is required to update existing file

        # 2. Prepare new content by appending timestamp and emoji
        current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        new_line = f"{current_time} {get_random_emoji()}"
        new_content = file_content.rstrip() + "\n" + new_line  # rstrip() to avoid extra blank lines

        # Encode the updated content to Base64 for GitHub API
        encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        commit_message = f"Update README with timestamp and emoji on {current_time}"

        # 3. PUT request to update the file with new content
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
            # In case GitHub returns a non-200 without raising an exception
            logger.error("Failed to update README.md. HTTP status: %d", update_response.getcode())
    except urllib.error.HTTPError as e:
        # Handle HTTP errors (e.g., authentication issues or permission problems)
        error_message = e.read().decode() if e.fp else str(e)
        logger.error("HTTPError: Failed to update README.md: %s (Status code %s)", error_message, e.code)
    except Exception as e:
        # Handle any other exceptions
        logger.exception("An unexpected error occurred: %s", str(e))

# Lambda entry point (when deployed as AWS Lambda function)
def lambda_handler(event, context):
    """AWS Lambda handler function."""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    if not token or not repo:
        # Log an error if configuration is missing
        logger.error("Environment variables GITHUB_TOKEN or GITHUB_REPO are not set.")
        return {"statusCode": 500, "body": "Configuration error: missing GitHub credentials."}
    # Attempt to update the README and capture outcome
    try:
        append_date_time_to_readme(token, repo)
        return {"statusCode": 200, "body": "README updated successfully."}
    except Exception as e:
        # Errors are already logged in append_date_time_to_readme; return failure response
        return {"statusCode": 500, "body": f"Error updating README: {str(e)}"}

# If run as a standalone script (for testing locally), execute the update function.
if __name__ == "__main__":
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    if not github_token or not github_repo:
        logger.error("Please set the GITHUB_TOKEN and GITHUB_REPO environment variables before running.")
    else:
        append_date_time_to_readme(github_token, github_repo)
