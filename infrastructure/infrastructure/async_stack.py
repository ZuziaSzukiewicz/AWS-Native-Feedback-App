from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_sqs as sqs,
    Duration,
    CfnOutput,
)
from constructs import Construct


class AsyncStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # SNS Topic for feedback events
        self.feedback_topic = sns.Topic(
            self,
            "FeedbackTopic",
            topic_name="feedback-app-topic",
            display_name="Feedback App Events",
        )

        # SQS Queue for async processing
        self.feedback_queue = sqs.Queue(
            self,
            "FeedbackQueue",
            queue_name="feedback-app-queue",
            visibility_timeout=Duration.seconds(300),  # MUST be > lambda processing time
            retention_period=Duration.days(14),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=sqs.Queue(
                    self,
                    "FeedbackDLQ",
                    queue_name="feedback-app-dlq",
                ),
            ),
        )

        # Subscribe SQS queue to SNS topic
        self.feedback_topic.add_subscription(
            sns_subscriptions.SqsSubscription(
                self.feedback_queue,
                raw_message_delivery=True
            )
        )

        # Outputs
        CfnOutput(
            self,
            "FeedbackTopicArn",
            value=self.feedback_topic.topic_arn,
            description="SNS Feedback Topic ARN",
            export_name="FeedbackAppTopicArn",
        )

        CfnOutput(
            self,
            "FeedbackQueueUrl",
            value=self.feedback_queue.queue_url,
            description="SQS Feedback Queue URL",
            export_name="FeedbackAppQueueUrl",
        )

        CfnOutput(
            self,
            "FeedbackQueueArn",
            value=self.feedback_queue.queue_arn,
            description="SQS Feedback Queue ARN",
            export_name="FeedbackAppQueueArn",
        )
