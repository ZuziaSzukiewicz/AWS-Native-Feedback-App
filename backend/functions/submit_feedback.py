import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SNS_TOPIC_ARN = os.environ.get("FEEDBACK_SNS_TOPIC_ARN")

sns_client = boto3.client("sns")


def _extract_user_identity(event: Dict[str, Any]) -> str:
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    if not claims:
        claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    user_id = claims.get("sub") or claims.get("username") or "anonymous"
    return user_id


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("submit_feedback invoked")
    logger.debug("event: %s", json.dumps(event))

    if not SNS_TOPIC_ARN:
        logger.error("Missing FEEDBACK_SNS_TOPIC_ARN environment variable")
        return {"statusCode": 500, "body": json.dumps({"message": "Server configuration error"})}

    try:
        body_text = event.get("body")
        if not body_text:
            raise ValueError("Missing body")

        body = json.loads(body_text) if isinstance(body_text, str) else body_text
        feedback_text = body.get("text")

        if not feedback_text or not isinstance(feedback_text, str):
            raise ValueError("'text' is required and must be a string")

        feedback_id = str(uuid.uuid4())
        user_id = _extract_user_identity(event)
        now_iso = datetime.utcnow().isoformat() + "Z"

        message_payload = {
            "feedbackId": feedback_id,
            "userId": user_id,
            "text": feedback_text,
            "createdAt": now_iso,
        }

        logger.info("Publishing feedback event to SNS topic %s", SNS_TOPIC_ARN)
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message_payload),
            MessageAttributes={
                "feedbackId": {"DataType": "String", "StringValue": feedback_id},
                "userId": {"DataType": "String", "StringValue": user_id},
            },
        )

        return {
            "statusCode": 202,
            "body": json.dumps({"feedbackId": feedback_id, "message": "Feedback submitted"}),
        }

    except ValueError as exc:
        logger.warning("Bad request: %s", exc)
        return {"statusCode": 400, "body": json.dumps({"message": str(exc)})}
    except (BotoCoreError, ClientError) as exc:
        logger.exception("Error publishing SNS message")
        return {"statusCode": 500, "body": json.dumps({"message": "Error submitting feedback"})}
    except Exception as exc:
        logger.exception("Unexpected error in submit_feedback")
        return {"statusCode": 500, "body": json.dumps({"message": "Unexpected internal error"})}
