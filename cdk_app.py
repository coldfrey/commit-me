#!/usr/bin/env python3
from aws_cdk import (
    App,
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,  # to retrieve stored token
    Environment,
)
from constructs import Construct

class GitHubReadmeUpdateStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # **1. Securely fetch the GitHub token from AWS Secrets Manager**
        # Assume a secret containing the token has been created (e.g., via AWS console or CLI).
        # Replace "YOUR_SECRET_NAME" with the actual name of the secret storing the PAT.
        github_token_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GitHubTokenSecret", secret_name="YOUR_SECRET_NAME"
        )

        # **2. Define the Lambda function for updating the README**
        update_function = _lambda.Function(
            self, "UpdateReadmeFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,    # Use Python 3.9 runtime (adjust if needed)
            handler="update_readme.lambda_handler",  # File name (update_readme.py) and function (lambda_handler)
            code=_lambda.Code.from_asset("path/to/lambda/code"),  
            # ^^^ "path/to/lambda/code" should be the directory containing your Python script (update_readme.py) and any dependencies.
            timeout=Duration.seconds(30),  # 30 seconds timeout (more than enough for a quick API call)
            environment={ 
                # Pass the GitHub repo and token to the function through environment variables.
                "GITHUB_REPO": "owner/repo_name",  # TODO: set this to your GitHub "owner/repo"
                # Use the secret value for the token; it will be provided securely.
                "GITHUB_TOKEN": github_token_secret.secret_value.to_string()
            }
        )

        # **3. Grant the Lambda permission to read the secret (so it can access the token at runtime)**
        github_token_secret.grant_read(update_function)

        # **4. Schedule the Lambda to run daily at 4:20 PM UTC using EventBridge (Cron expression)**
        rule = events.Rule(
            self, "Daily420Trigger",
            schedule=events.Schedule.cron(minute="20", hour="16")  # 16:20 UTC every day
            # By default, other fields (day, month, year) are '*' (any), making this trigger daily.
        )
        # Set the Lambda as the target of the scheduled rule
        rule.add_target(targets.LambdaFunction(update_function))

# **5. Instantiate the app and stack, specifying the region (eu-west-1)**
app = App()
GitHubReadmeUpdateStack(app, "GitHubReadmeUpdateStack", env=Environment(region="eu-west-1"))
app.synth()
