import json
import logging
import os
import uuid
from datetime import datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SNS_TOPIC_ARN = os.environ.get("FEEDBACK_SNS_TOPIC_ARN")
sns_client = boto3.client("sns")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": True
}

def lambda_handler(event, context):
    logger.info("submit_feedback invoked")

    if not SNS_TOPIC_ARN:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "Configuration error"})
        }

    try:
        body_text = event.get("body")
        if not body_text:
            raise ValueError("Missing body")

        body = json.loads(body_text)
        feedback_text = body.get("text")
        if not feedback_text:
            raise ValueError("'text' is required")

        feedback_id = str(uuid.uuid4())

        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps({
                "feedbackId": feedback_id,
                "text": feedback_text
            })
        )

        return {
            "statusCode": 202,
            "headers": CORS_HEADERS,
            "body": json.dumps({"feedbackId": feedback_id})
        }

    except Exception as exc:
        logger.exception("Unexpected error")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": str(exc)})
        }
