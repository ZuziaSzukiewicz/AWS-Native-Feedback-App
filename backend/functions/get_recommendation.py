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


def _extract_user_identity(event: Dict[str, Any]) -> str:
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    if not claims:
        claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    return claims.get("sub") or claims.get("username") or "anonymous"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("get_recommendation invoked")
    logger.debug("event: %s", json.dumps(event))

    if not TABLE_NAME:
        logger.error("Missing RECOMMENDATIONS_TABLE_NAME environment variable")
        return {"statusCode": 500, "body": json.dumps({"message": "Server configuration issue"})}

    params = event.get("queryStringParameters") or {}
    feedback_id = params.get("feedbackId")

    if not feedback_id:
        logger.warning("Missing feedbackId query parameter")
        return {"statusCode": 400, "body": json.dumps({"message": "feedbackId query parameter is required"})}

    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={"feedbackId": feedback_id})
        item = response.get("Item")

        if not item:
            logger.info("Recommendation not found for feedbackId=%s", feedback_id)
            return {"statusCode": 404, "body": json.dumps({"message": "Recommendation not found"})}

        # Optionally enforce ownership if user identity is required
        requester = _extract_user_identity(event)
        if item.get("userId") != requester and requester != "anonymous":
            logger.warning("Unauthorized access attempt user=%s feedbackId=%s", requester, feedback_id)
            return {"statusCode": 403, "body": json.dumps({"message": "Forbidden"})}

        return {"statusCode": 200, "body": json.dumps(item)}

    except (BotoCoreError, ClientError) as exc:
        logger.exception("DynamoDB get_item failure")
        return {"statusCode": 500, "body": json.dumps({"message": "Database error"})}
    except Exception as exc:
        logger.exception("Unexpected error")
        return {"statusCode": 500, "body": json.dumps({"message": "Unexpected internal error"})}
