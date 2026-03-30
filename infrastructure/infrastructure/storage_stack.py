from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table for Recommendations

        self.recommendations_table = dynamodb.Table(
            self,
            "RecommendationsTable",
            table_name="feedback-app-recommendations",
            partition_key=dynamodb.Attribute(
                name="feedbackId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )


        # Global Secondary Index for querying by userId
        self.recommendations_table.add_global_secondary_index(
            index_name="UserIdIndex",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Outputs
        CfnOutput(
            self,
            "RecommendationsTableName",
            value=self.recommendations_table.table_name,
            description="DynamoDB Recommendations Table Name",
            export_name="FeedbackAppRecommendationsTableName",
        )

        CfnOutput(
            self,
            "RecommendationsTableArn",
            value=self.recommendations_table.table_arn,
            description="DynamoDB Recommendations Table ARN",
            export_name="FeedbackAppRecommendationsTableArn",
        )
