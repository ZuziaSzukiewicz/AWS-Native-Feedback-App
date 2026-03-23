from aws_cdk import Stack
from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Placeholder for Lambda 1: submitFeedback
        # TODO: Implement submitFeedback Lambda

        # Placeholder for Lambda 2: processFeedback
        # TODO: Implement processFeedback Lambda

        # Placeholder for Lambda 3: getRecommendation
        # TODO: Implement getRecommendation Lambda