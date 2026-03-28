# AWS CDK Infrastructure Stack Guide

## Overview
This directory contains Python AWS CDK code for deploying the Feedback App infrastructure on AWS. The infrastructure is organized into five modular stacks:

1. **AuthStack** - Cognito User Pool for authentication
2. **StorageStack** - DynamoDB table for recommendations
3. **AsyncStack** - SNS Topic + SQS Queue for async processing
4. **LambdaStack** - Three Lambda functions with IAM roles and permissions
5. **ApiStack** - API Gateway REST API with Cognito authorizer

## Stack Architecture

### Dependencies
```
App (app.py)
├── AuthStack
├── StorageStack
├── AsyncStack
└── LambdaStack (depends on Auth, Storage, Async)
    └── ApiStack (depends on Lambda)
```

## Stacks Detail

### AuthStack (`auth_stack.py`)
- **Cognito User Pool**: `feedback-app-user-pool`
  - Self sign-up enabled with email verification
  - Password policy: 8+ chars, upper/lower, digits
  - Recovery via email
- **User Pool Client**: `feedback-app-client`
  - User-password and SRP authentication flows
  - No client secret for web/mobile apps

**Exports:**
- `FeedbackAppUserPoolId`: User Pool ID
- `FeedbackAppUserPoolArn`: User Pool ARN
- `FeedbackAppClientId`: App Client ID

### StorageStack (`storage_stack.py`)
- **DynamoDB Table**: `feedback-app-recommendations`
  - Partition Key: `feedbackId` (String)
  - Sort Key: `userId` (String)
  - Billing: Pay-per-request (on-demand)
  - Point-in-time recovery enabled
  - GSI on `userId` for querying by user

**Exports:**
- `FeedbackAppRecommendationsTableName`: Table name
- `FeedbackAppRecommendationsTableArn`: Table ARN

### AsyncStack (`async_stack.py`)
- **SNS Topic**: `feedback-app-topic`
  - Receives feedback submission events
- **SQS Queue**: `feedback-app-queue`
  - Subscribed to SNS topic
  - Visibility timeout: 5 minutes
  - DLQ with max 3 receive attempts
- **Dead Letter Queue**: `feedback-app-dlq`
  - For failed messages

**Exports:**
- `FeedbackAppTopicArn`: SNS Topic ARN
- `FeedbackAppQueueUrl`: SQS Queue URL
- `FeedbackAppQueueArn`: SQS Queue ARN

### LambdaStack (`lambda_stack.py`)
Three Lambda functions with least-privilege IAM policies:

#### 1. **SubmitFeedback** (`submit_feedback.lambda_handler`)
- Function: `feedback-app-submit-feedback`
- Runtime: Python 3.11 | Memory: 256 MB | Timeout: 30s
- Environment: `FEEDBACK_SNS_TOPIC_ARN`
- Permissions: `sns:Publish` on feedback topic
- Role: Auto-generated with inline policy

#### 2. **ProcessFeedback** (`process_feedback.lambda_handler`)
- Function: `feedback-app-process-feedback`
- Runtime: Python 3.11 | Memory: 512 MB | Timeout: 60s
- Environment: `RECOMMENDATIONS_TABLE_NAME`
- Permissions:
  - `dynamodb:PutItem` on recommendations table
  - `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` on queue
- Event Source: SQS queue (batch size 10, window 5s)

#### 3. **GetRecommendation** (`get_recommendation.lambda_handler`)
- Function: `feedback-app-get-recommendation`
- Runtime: Python 3.11 | Memory: 256 MB | Timeout: 15s
- Environment: `RECOMMENDATIONS_TABLE_NAME`
- Permissions: `dynamodb:GetItem` on recommendations table

**Exports:**
- `FeedbackAppSubmitFunctionArn`: Submit Lambda ARN
- `FeedbackAppProcessFunctionArn`: Process Lambda ARN
- `FeedbackAppGetRecommendationFunctionArn`: Get Lambda ARN

### ApiStack (`api_stack.py`)
REST API with Cognito authorization:

- **REST API**: `feedback-app-api`
  - Logging: INFO level, data trace enabled
  - Stage: `prod`

#### Routes:

**POST /feedback**
- Authorizer: Cognito User Pool
- Integration: `submit_feedback` Lambda
- Request Body: `{"text": "..."}`
- Response: HTTP 202

**GET /recommendation**
- Authorizer: Cognito User Pool
- Integration: `get_recommendation` Lambda
- Query Params: `feedbackId` (required)
- Response: HTTP 200 with recommendation object

**Exports:**
- `FeedbackAppApiEndpoint`: API Base URL
- `FeedbackAppApiId`: REST API ID

## Deployment

### Prerequisites
1. AWS CDK CLI: `npm install -g aws-cdk`
2. AWS credentials configured: `aws configure`
3. Python 3.11+
4. Python dependencies: `pip install -r requirements.txt`

### Commands

**Synthesize CloudFormation template:**
```bash
cd infrastructure
cdk synth
```

**Diff stacks (preview changes):**
```bash
cdk diff
```

**Deploy all stacks:**
```bash
cdk deploy --all --require-approval=never
```

**Deploy specific stack:**
```bash
cdk deploy AuthStack
cdk deploy StorageStack
cdk deploy AsyncStack
cdk deploy LambdaStack
cdk deploy ApiStack
```

**Destroy all stacks:**
```bash
cdk destroy --all
```

## Environment Setup

The CDK uses `CDK_DEFAULT_ACCOUNT` and `CDK_DEFAULT_REGION` from your AWS CLI configuration.

**Set explicitly (optional):**
```bash
export CDK_DEFAULT_ACCOUNT=123456789012
export CDK_DEFAULT_REGION=us-east-1
```

## Lambda Function Paths

The CDK expects Lambda code at:
- `./backend/functions/submit_feedback.py`
- `./backend/functions/process_feedback.py`
- `./backend/functions/get_recommendation.py`

If using a layer for dependencies, place Python packages at:
- `./backend/layers/python/lib/python3.11/site-packages/`

## Cross-Stack References

Outputs are exported with the `export_name` property, making them available across stacks via:
```python
# In another stack
cdk.Fn.import_value("FeedbackAppUserPoolId")
```

## Notes

- DynamoDB table has `RemovalPolicy.RETAIN`, so data persists after stack deletion
- User Pool has `removal_policy=None` (soft delete); enable hard delete with `RemovalPolicy.DESTROY` if needed
- SNS → SQS subscription includes DLQ for fault tolerance
- Lambda functions use environment variables for configuration (no hardcoded values)
- All Lambda functions include comprehensive logging and error handling

## Troubleshooting

**Lambda code not found:**
```
Error: Cannot find lambda code asset at ./backend/functions
```
→ Ensure Lambda Python files exist in the repository root or update the `code_asset_path` in `lambda_stack.py`.

**Missing environment variables:**
→ CDK synthesizes correctly locally but fails on deployment if `CDK_DEFAULT_ACCOUNT` or `CDK_DEFAULT_REGION` are undefined.

**Cognito authorizer not working:**
→ Ensure the access token is sent in the `Authorization` header with format: `Bearer <token>`

## Next Steps

1. Customize Cognito user attributes in `auth_stack.py` as needed
2. Add CORS to API Gateway if frontend is on different domain
3. Configure domain names for API Gateway (use Route53 + ACM)
4. Enable API caching for GET /recommendation if needed
5. Add CloudWatch alarms for Lambda errors and DLQ messages
6. Set up CI/CD pipeline for automated deployments
