#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.auth_stack import AuthStack
from stacks.api_stack import ApiStack
from stacks.async_stack import AsyncStack
from stacks.storage_stack import StorageStack
from stacks.lambda_Stack import LambdaStack

app = cdk.App()

# Instantiate stacks
auth_stack = AuthStack(app, "AuthStack")
api_stack = ApiStack(app, "ApiStack")
async_stack = AsyncStack(app, "AsyncStack")
storage_stack = StorageStack(app, "StorageStack")
lambda_stack = LambdaStack(app, "LambdaStack")

app.synth()