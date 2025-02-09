#!/usr/bin/env python3
import os
from aws_cdk import (
    App,
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    Environment,
)
from constructs import Construct

class GitHubReadmeUpdateStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Retrieve the GitHub token from the environment (set in GitHub Actions)
        # NOTE: This value will be embedded in the CloudFormation template.
        github_token = os.getenv("GITHUB_TOKEN", "")
        if not github_token:
            raise Exception("GITHUB_TOKEN environment variable is not set for CDK deployment.")

        # Define the Lambda function
        update_function = _lambda.Function(
            self, "UpdateReadmeFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="update_readme.lambda_handler",  # Looks for lamda/update_readme.py
            code=_lambda.Code.from_asset("lamda", bundling={
                "image": _lambda.Runtime.PYTHON_3_12.bundling_image,
                "command": [
                    "bash", "-c",
                    "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                ]
            }),  
            timeout=Duration.seconds(30),
            environment={
                # Commit to the same repository that contains the code:
                "GITHUB_REPO": "coldfrey/commit-me",
                "GITHUB_TOKEN": github_token,
            }
        )

        # Create an EventBridge rule to trigger the Lambda daily at 16:20 UTC (4:20 PM UTC)
        rule = events.Rule(
            self, "Daily420Trigger",
            schedule=events.Schedule.cron(minute="20", hour="16")  # Cron: 16:20 every day
        )
        rule.add_target(targets.LambdaFunction(update_function))

# Instantiate the app and stack, targeting the eu-west-1 region
app = App()
GitHubReadmeUpdateStack(app, "GitHubReadmeUpdateStack", env=Environment(region="eu-west-1"))
app.synth()
