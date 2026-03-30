#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infrastructure.auth_stack import AuthStack
from infrastructure.storage_stack import StorageStack
from infrastructure.async_stack import AsyncStack
from infrastructure.lambda_stack import LambdaStack
from infrastructure.api_stack import ApiStack


app = cdk.App()

# Environment configuration
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)

# Create Authentication Stack (Cognito User Pool)
auth_stack = AuthStack(app, "AuthStack", env=env)

# Create Storage Stack (DynamoDB)
storage_stack = StorageStack(app, "StorageStack", env=env)

# Create Async Stack (SNS Topic + SQS Queue)
async_stack = AsyncStack(app, "AsyncStack", env=env)

# Create Lambda Stack (all three Lambda functions)
lambda_stack = LambdaStack(
    app,
    "LambdaStack",
    sns_topic_arn=async_stack.feedback_topic.topic_arn,
    recommendations_table_arn=storage_stack.recommendations_table.table_arn,
    recommendations_table_name=storage_stack.recommendations_table.table_name,
    feedback_queue=async_stack.feedback_queue,
    env=env,
)

# Create API Stack (API Gateway + routes + Cognito authorizer)
api_stack = ApiStack(
    app,
    "ApiStack",
    user_pool=auth_stack.user_pool,
    submit_feedback_lambda=lambda_stack.submit_feedback_lambda,
    get_recommendation_lambda=lambda_stack.get_recommendation_lambda,
    env=env,
)

# Add stack dependencies
api_stack.add_dependency(lambda_stack)
lambda_stack.add_dependency(auth_stack)
lambda_stack.add_dependency(storage_stack)
lambda_stack.add_dependency(async_stack)

app.synth()