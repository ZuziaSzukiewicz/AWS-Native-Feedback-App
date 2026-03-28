from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_sqs as sqs,
    Duration,
    CfnOutput,
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct


class LambdaStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        sns_topic_arn: str,
        recommendations_table_arn: str,
        recommendations_table_name: str,
        feedback_queue: sqs.Queue,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda Layer for common dependencies (optional - only if layer exists)
        # lambda_layer = lambda_.LayerVersion(
        #     self,
        #     "FeedbackLayer",
        #     code=lambda_.Code.from_asset("./backend/layers/python/lib/python3.11/site-packages"),
        #     compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
        # )

        # ===== SUBMIT FEEDBACK LAMBDA =====
        submit_feedback_lambda = lambda_.Function(
            self,
            "SubmitFeedbackFunction",
            function_name="feedback-app-submit-feedback",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("../backend/functions"),
            handler="submit_feedback.lambda_handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "FEEDBACK_SNS_TOPIC_ARN": sns_topic_arn,
            },
        )

        # Grant SNS publish permission
        submit_feedback_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sns:Publish"],
                resources=[sns_topic_arn],
            )
        )

        # ===== PROCESS FEEDBACK LAMBDA =====
        process_feedback_lambda = lambda_.Function(
            self,
            "ProcessFeedbackFunction",
            function_name="feedback-app-process-feedback",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("../backend/functions"),
            handler="process_feedback.lambda_handler",
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "RECOMMENDATIONS_TABLE_NAME": recommendations_table_name,
            },
        )

        # Grant DynamoDB put_item permission
        process_feedback_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["dynamodb:PutItem"],
                resources=[recommendations_table_arn],
            )
        )

        # Grant SQS receive/delete message permissions for event source mapping
        process_feedback_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                ],
                resources=[feedback_queue.queue_arn],
            )
        )

        # Connect SQS queue as event source
        process_feedback_lambda.add_event_source(
            SqsEventSource(
                queue=feedback_queue,
                batch_size=10,
                max_batching_window=Duration.seconds(5),
            )
        )

        # ===== GET RECOMMENDATION LAMBDA =====
        get_recommendation_lambda = lambda_.Function(
            self,
            "GetRecommendationFunction",
            function_name="feedback-app-get-recommendation",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("../backend/functions"),
            handler="get_recommendation.lambda_handler",
            timeout=Duration.seconds(15),
            memory_size=256,
            environment={
                "RECOMMENDATIONS_TABLE_NAME": recommendations_table_name,
            },
        )

        # Grant DynamoDB get_item permission
        get_recommendation_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["dynamodb:GetItem"],
                resources=[recommendations_table_arn],
            )
        )

        # Outputs
        CfnOutput(
            self,
            "SubmitFeedbackFunctionArn",
            value=submit_feedback_lambda.function_arn,
            description="Submit Feedback Lambda ARN",
            export_name="FeedbackAppSubmitFunctionArn",
        )

        CfnOutput(
            self,
            "ProcessFeedbackFunctionArn",
            value=process_feedback_lambda.function_arn,
            description="Process Feedback Lambda ARN",
            export_name="FeedbackAppProcessFunctionArn",
        )

        CfnOutput(
            self,
            "GetRecommendationFunctionArn",
            value=get_recommendation_lambda.function_arn,
            description="Get Recommendation Lambda ARN",
            export_name="FeedbackAppGetRecommendationFunctionArn",
        )

        # Store lambda functions as properties for use in other stacks
        self.submit_feedback_lambda = submit_feedback_lambda
        self.process_feedback_lambda = process_feedback_lambda
        self.get_recommendation_lambda = get_recommendation_lambda
