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
bedrock_client = boto3.client("bedrock-runtime")


def _extract_sns_message(record: Dict[str, Any]) -> Dict[str, Any]:
    # With raw message delivery, SQS body is directly the SNS message body
    return json.loads(record.get("body", "{}"))


def _generate_recommendation_text(feedback_text: str) -> str:
    prompt = (
        "Analyze the following user feedback and provide specific, actionable "
        "improvement suggestions. Keep the response concise.\n\n"
        f"Feedback: {feedback_text}"
    )

    body = json.dumps({
        "prompt": prompt,
        "max_tokens": 300,
        "temperature": 0.5,
        "top_p": 0.9
    })

    try:
        response = bedrock_client.invoke_model(
            modelId="mistral.mistral-large-2402-v1:0",
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())

        generated_text = (
            response_body
            .get("outputs", [{}])[0]
            .get("text", "")
            .strip()
        )

        return (
            generated_text
            if generated_text
            else "No specific suggestions available."
        )

    except Exception as e:
        logger.exception("Bedrock Mistral error")
        return (
            "Unable to generate recommendation at this time. "
            "Please try again later."
        )


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
