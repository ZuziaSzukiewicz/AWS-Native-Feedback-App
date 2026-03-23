# Project Architecture Instructions for Copilot
This repository contains a full AWS-native serverless application built as part of the AWS Upskilling Program.

## Overall Architecture
The project implements:
- React frontend hosted and managed by AWS Amplify
- User authentication via Cognito User Pool (Amplify Auth)
- API Gateway REST API secured with a Cognito Authorizer
- Three Lambda functions:
  1. submitFeedback → POST /feedback
  2. processFeedback → triggered by SQS
  3. getRecommendation → GET /recommendation
- SNS Topic to initiate asynchronous processing
- SQS Queue subscribed to SNS (buffer + retry)
- DynamoDB table storing recommendations
- Amazon Bedrock for AI-powered feedback improvement suggestions
- AWS CDK (Python) for Infrastructure-as-Code

## Project Structure Guidelines
- /frontend → React + Amplify
- /backend/functions → Lambda code (Python)
- /infrastructure → CDK stacks using Python
- /copilot → instructions, prompts and reusable patterns
- /ci-cd → pipelines for GitHub Actions

## Naming Conventions
- Repository and project names should follow: `aws-upskilling-(aws-service)` (e.g., `aws-upskilling-lambda`, `aws-upskilling-api`, `aws-upskilling-amplify`).
- Cloud resources and stacks should use a similar prefix pattern when appropriate for easier traceability (e.g., `aws-upskilling-feedback-api`, `aws-upskilling-feedback-table`).

## Code Style
For all generated code, follow these rules:
- Prefer Python for AWS Lambda and CDK
- Every Lambda should include:
  - clear handler function
  - logging
  - error handling
  - type hints
- CDK should use:
  - separate stacks (auth, api, async, storage, lambdas)
  - environment variables for cross-stack references
  - least privilege IAM policies

## JavaScript / React Best Practices
- Use TypeScript in frontend and Node.js backend when possible for stronger typing.
- Enforce linting/formatting: ESLint + Prettier config checked in.
- Avoid `var`; prefer `const`/`let`, explicit `async/await`, and structured error handling.
- Use React functional components with hooks (`useState`, `useEffect`, `useMemo`, `useCallback`) and avoid class components for new code.
- Keep components small, reusable, and plain (presentational + container separation).
- Prefer controlled form components, strong PropTypes / interface definitions, and centralized state via context or state management as needed.
- Use Amplify patterns: `withAuthenticator`, `Auth.currentAuthenticatedUser()`, `API.post/get`, and token refresh logic.
- Write unit tests using React Testing Library and jest, covering component behavior and pure functions.

## API Contract
POST /feedback 
→ body: { "text": "..." }
→ returns 202
→ triggers SNS → SQS → Lambda

GET /recommendation?feedbackId=...
→ returns recommendation from DynamoDB

## Prompts Expectations
When generating:
- Lambdas → include IAM permissions, parsing JWT identity
- CDK → generate full constructs with props
- Frontend → ensure integration with Amplify Auth and Amplify API