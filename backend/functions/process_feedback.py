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
bedrock = boto3.client("bedrock")


def _extract_sns_message(record: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(record.get("body", "{}"))


def _get_available_text_models() -> List[str]:
    """Get list of available text generation models in the current region."""
    try:
        response = bedrock.list_foundation_models()
        text_models = []
        for model in response['modelSummaries']:
            model_id = model['modelId']
            if model.get('modelLifecycle', {}).get('status') == 'ACTIVE':
                if not any(skip in model_id.lower() for skip in ['embed', 'rerank']):
                    text_models.append(model_id)

        nova_models = [m for m in text_models if 'nova' in m]
        other_models = [m for m in text_models if 'nova' not in m]
        return nova_models + other_models
    except Exception as e:
        logger.exception(f"Error listing Bedrock models: {str(e)}")
        return []


def _generate_recommendation_text(feedback_text: str) -> str:
    prompt = (
        "Analyze the following user feedback and provide specific, actionable "
        "improvement suggestions. Keep the response concise.\n\n"
        f"Feedback: {feedback_text}"
    )
    available_models = _get_available_text_models()

    if not available_models:
        logger.error("No text generation models available in this region")
        return (
            "Unable to generate recommendation at this time. "
            "Please try again later."
        )

    for model_id in available_models:
        try:
            logger.info(f"Trying model: {model_id}")
            if 'nova' in model_id:
                body = json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 300,
                        "temperature": 0.5,
                        "topP": 0.9
                    }
                })
            elif 'mistral' in model_id:
                body = json.dumps({
                    "max_tokens": 300,
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            else:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })

            response = bedrock_client.invoke_model(
                modelId=model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )

            response_body = json.loads(response["body"].read())
            logger.info(f"Bedrock response received for model {model_id}")
            logger.debug(f"Response body: {json.dumps(response_body)}")

            generated_text = ""
            if 'nova' in model_id:
                if 'output' in response_body and 'message' in response_body['output']:
                    content = response_body['output']['message'].get('content', [])
                    if content and isinstance(content, list) and len(content) > 0:
                        generated_text = content[0].get('text', '')
                elif 'content' in response_body:
                    content = response_body.get('content', [])
                    if content and isinstance(content, list) and len(content) > 0:
                        generated_text = content[0].get('text', '')
            elif 'mistral' in model_id:
                if 'choices' in response_body and response_body['choices']:
                    generated_text = response_body['choices'][0].get('message', {}).get('content', '')
            else:
                generated_text = (
                    response_body
                    .get("content", [{}])[0]
                    .get("text", "")
                )

            generated_text = generated_text.strip()

            if generated_text:
                logger.info(f"Successfully generated recommendation using {model_id}")
                return generated_text
            else:
                logger.warning(f"Empty response from model {model_id}")
                continue

        except Exception as e:
            logger.exception(f"Error with model {model_id}: {str(e)}")
            continue
    logger.error("All Bedrock models failed")
    return (
        "Unable to generate recommendation at this time. "
        "Please try again later."
    )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("process_feedback invoked")
    logger.debug("event: %s", json.dumps(event))

    import boto3.session
    session = boto3.session.Session()
    current_region = session.region_name
    logger.info(f"Lambda running in region: {current_region}")

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
