
import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("RECOMMENDATIONS_TABLE_NAME")
dynamodb = boto3.resource("dynamodb")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": True,
}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("get_recommendation invoked")
    logger.debug("event: %s", json.dumps(event))

    if not TABLE_NAME:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "Server configuration issue"})
        }

    params = event.get("queryStringParameters") or {}
    feedback_id = params.get("feedbackId")

    if not feedback_id:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "feedbackId query parameter is required"})
        }

    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={"feedbackId": feedback_id})
        item = response.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"message": "Recommendation not found"})
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(item)
        }

    except Exception:
        logger.exception("Unexpected error")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "Unexpected internal error"})
        }
