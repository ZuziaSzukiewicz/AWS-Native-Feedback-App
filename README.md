**This project is the final assignment for the Capgemini AWS Upskilling Program.**

It demonstrates a complete AWS‑native, serverless, AI‑powered application, built end‑to‑end using services such as:

  - Amplify (React frontend + Auth integration)
  - Cognito (user registration & authentication)
  - API Gateway (REST API with Cognito Authorizer)
  - Lambda (serverless compute for all backend logic)
  - SNS → SQS (asynchronous messaging pattern)
  - DynamoDB (NoSQL storage)
  - Amazon Bedrock (AI‑generated recommendations)

The application allows users to:

  - Register & log in
  - Submit feedback they received (e.g., from manager or coworker)
  - Trigger an asynchronous process that evaluates the feedback using an AI model
  - Retrieve AI-generated improvement recommendations from DynamoDB

This project summarizes everything learned during the Upskilling Program, including AWS serverless design, IaC, security, backend architecture, asynchronous patterns, and frontend integration.
