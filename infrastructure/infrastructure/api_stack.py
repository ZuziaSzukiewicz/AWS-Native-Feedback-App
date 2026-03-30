from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_lambda as lambda_,
    CfnOutput,
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        user_pool: cognito.UserPool,
        submit_feedback_lambda: lambda_.Function,
        get_recommendation_lambda: lambda_.Function,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ✅ REST API
        self.api = apigw.RestApi(
            self,
            "FeedbackRestApi",
            rest_api_name="FeedbackRestApi",
        )

        # ✅ Cognito Authorizer
        cognito_authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "FeedbackAuthorizer",
            cognito_user_pools=[user_pool],
            identity_source="method.request.header.Authorization"
        )

        # ========== CORS ==========

        def add_cors_options(api_resource):
            api_resource.add_method(
                "OPTIONS",
                apigw.MockIntegration(
                    integration_responses=[
                        apigw.IntegrationResponse(
                            status_code="200",
                            response_parameters={
                                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                                "method.response.header.Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
                                "method.response.header.Access-Control-Allow-Origin": "'*'",
                            },
                        )
                    ],
                    passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
                    request_templates={"application/json": "{\"statusCode\": 200}"}
                ),
                method_responses=[
                    apigw.MethodResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Methods": True,
                            "method.response.header.Access-Control-Allow-Origin": True,
                        }
                    )
                ]
            )

        # ========== POST /feedback ==========
        feedback_res = self.api.root.add_resource("feedback")
        add_cors_options(feedback_res)

        feedback_res.add_method(
            "POST",
            apigw.LambdaIntegration(submit_feedback_lambda, proxy=True, allow_test_invoke=True),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=cognito_authorizer,
        )

        # ========== GET /recommendation ==========
        rec_res = self.api.root.add_resource("recommendation")
        add_cors_options(rec_res)

        rec_res.add_method(
            "GET",
            apigw.LambdaIntegration(get_recommendation_lambda, proxy=True),
            request_parameters={"method.request.querystring.feedbackId": True},
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorizer=cognito_authorizer,
        )

        CfnOutput(
            self,
            "ApiEndpoint",
            value=self.api.url,
            export_name="FeedbackAppApiEndpoint",
        )
