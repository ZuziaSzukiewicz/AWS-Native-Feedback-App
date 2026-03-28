import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("RECOMMENDATIONS_TABLE_NAME")

dynamodb = boto3.resource("dynamodb")


def _extract_sns_message(record: Dict[str, Any]) -> Dict[str, Any]:
    # SQS event from SNS delivery includes a JSON string in body with 'Message' field
    body = json.loads(record.get("body", "{}"))
    message = body.get("Message")
    if message:
        message = json.loads(message)
    else:
        message = json.loads(record.get("body", "{}"))
    return message


def _generate_recommendation_text(feedback_text: str) -> str:
    # Placeholder logic: Replace with Amazon Bedrock call or smarter NLP
    summary = feedback_text.strip()[:300]
    return f"Suggested improvement: please clarify and focus on the core ask. Source: {summary}"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("process_feedback invoked")
    logger.debug("event: %s", json.dumps(event))

    if not TABLE_NAME:
        logger.error("Missing RECOMMENDATIONS_TABLE_NAME environment variable")
        raise RuntimeError("Table configuration missing")

    table = dynamodb.Table(TABLE_NAME)

    records: List[Dict[str, Any]] = event.get("Records", [])
    if not records:
        logger.warning("No records to process")
        return {"statusCode": 200, "body": "No records"}

    for record in records:
        try:
            message = _extract_sns_message(record)
            feedback_id = message.get("feedbackId")
            user_id = message.get("userId", "anonymous")
            feedback_text = message.get("text", "")

            if not feedback_id or not feedback_text:
                raise ValueError("Missing feedbackId or text in message")

            recommendation_text = _generate_recommendation_text(feedback_text)
            now_iso = datetime.utcnow().isoformat() + "Z"

            item = {
                "feedbackId": feedback_id,
                "userId": user_id,
                "recommendation": recommendation_text,
                "sourceText": feedback_text,
                "updatedAt": now_iso,
            }

            logger.info("Writing recommendation for feedbackId=%s", feedback_id)
            table.put_item(Item=item)

        except (ValueError, KeyError) as exc:
            logger.error("Invalid record, skipping: %s", exc)
            continue
        except (BotoCoreError, ClientError) as exc:
            logger.exception("DynamoDB error, record will be retried")
            raise
        except Exception as exc:
            logger.exception("Unexpected error processing record")
            raise

    return {"statusCode": 200, "body": "Processed"}
