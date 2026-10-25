"""
Milestone 4 Deployment Automation Script:
Deploys doc-intelligence-process-document Lambda function, updates IAM permissions
for Amazon Textract, connects S3 ObjectCreated event notification, and exposes POST /documents/{id}/process.
"""

import io
import json
import os
import sys
import time
import zipfile
import boto3
from botocore.exceptions import ClientError

AWS_REGION = "ap-south-1"
ACCOUNT_ID = "399383129700"
BUCKET_NAME = "doc-intelligence-uploads-399383129700"
ROLE_NAME = "doc-intelligence-lambda-role"
LAMBDA_NAME = "doc-intelligence-process-document"
API_NAME = "doc-intelligence-api"
STAGE_NAME = "prod"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

def log(step: str, msg: str):
    print(f"[{step}] {msg}")

def update_iam_role_for_textract(iam) -> str:
    """Add Textract AnalyzeExpense permissions to the Lambda execution role."""
    log("IAM", "Adding Amazon Textract policy to Lambda role...")
    textract_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowTextractExpenseAnalysis",
                "Effect": "Allow",
                "Action": [
                    "textract:AnalyzeExpense",
                    "textract:GetExpenseAnalysis",
                    "textract:StartExpenseAnalysis"
                ],
                "Resource": "*"
            },
            {
                "Sid": "AllowS3ReadForProcessing",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:PutObject"
                ],
                "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
            }
        ]
    }
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="DocIntelligenceTextractPolicy",
        PolicyDocument=json.dumps(textract_policy)
    )
    role_res = iam.get_role(RoleName=ROLE_NAME)
    role_arn = role_res["Role"]["Arn"]
    log("IAM", f"Updated Textract permissions on role: {role_arn}")
    return role_arn

def build_process_lambda_zip() -> bytes:
    """Package process-document handler and shared package into zip."""
    log("BUILD", "Packaging process-document Lambda zip artifact...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        handler_path = os.path.join(BACKEND_DIR, "functions", "process-document", "handler.py")
        zf.write(handler_path, arcname="handler.py")

        shared_dir = os.path.join(BACKEND_DIR, "shared")
        for root, _, files in os.walk(shared_dir):
            for file in files:
                if file.endswith(".pyc") or "__pycache__" in root:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BACKEND_DIR)
                zf.write(full_path, arcname=rel_path.replace("\\", "/"))

    zip_bytes = zip_buffer.getvalue()
    log("BUILD", f"Zip package created ({len(zip_bytes)} bytes)")
    return zip_bytes

def deploy_process_lambda(lambda_client, role_arn: str, zip_bytes: bytes) -> str:
    """Create or update doc-intelligence-process-document Lambda function."""
    log("LAMBDA", f"Checking function '{LAMBDA_NAME}'...")
    env_vars = {
        "DOCUMENTS_BUCKET_NAME": BUCKET_NAME
    }

    try:
        res = lambda_client.get_function(FunctionName=LAMBDA_NAME)
        log("LAMBDA", "Function exists. Updating code and configuration...")
        lambda_client.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=zip_bytes
        )
        time.sleep(3)
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.lambda_handler",
            Timeout=60,  # Allow up to 60s for Textract OCR processing
            MemorySize=512,
            Environment={"Variables": env_vars}
        )
        function_arn = res["Configuration"]["FunctionArn"]
        log("LAMBDA", f"Updated process-document Lambda: {function_arn}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            log("LAMBDA", f"Creating new Lambda function '{LAMBDA_NAME}'...")
            res = lambda_client.create_function(
                FunctionName=LAMBDA_NAME,
                Runtime="python3.12",
                Role=role_arn,
                Handler="handler.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Description="Executes Amazon Textract AnalyzeExpense and normalizes invoices",
                Timeout=60,
                MemorySize=512,
                Environment={"Variables": env_vars}
            )
            function_arn = res["FunctionArn"]
            log("LAMBDA", f"Created Lambda function: {function_arn}")
        else:
            raise e

    return function_arn

def configure_s3_event_trigger(s3, lambda_client, lambda_arn: str):
    """Allow S3 to invoke process-document Lambda and configure event notification."""
    log("S3-TRIGGER", "Configuring S3 ObjectCreated event notification...")

    # 1. Grant S3 permission to invoke Lambda
    statement_id = "s3-invoke-process-document"
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn=f"arn:aws:s3:::{BUCKET_NAME}",
            SourceAccount=ACCOUNT_ID
        )
        log("S3-TRIGGER", "Added Lambda invoke permission for S3.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            log("S3-TRIGGER", "S3 invoke permission already exists.")
        else:
            raise e

    # Wait for Lambda resource policy to propagate to S3
    log("S3-TRIGGER", "Waiting 6s for Lambda resource policy propagation...")
    time.sleep(6)

    # 2. Put bucket notification configuration
    notification_config = {
        "LambdaFunctionConfigurations": [
            {
                "Id": "AutoProcessUploadedInvoices",
                "LambdaFunctionArn": lambda_arn,
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {"Name": "prefix", "Value": "uploads/"}
                        ]
                    }
                }
            }
        ]
    }
    s3.put_bucket_notification_configuration(
        Bucket=BUCKET_NAME,
        NotificationConfiguration=notification_config
    )
    log("S3-TRIGGER", f"S3 bucket '{BUCKET_NAME}' notification active on 'uploads/' prefix.")

def configure_api_route(apigw, lambda_client, lambda_arn: str):
    """Expose POST /documents/{id}/process on API Gateway with Cognito Authorizer."""
    log("APIGW", "Configuring /documents/{id}/process route on API Gateway...")
    apis = apigw.get_rest_apis().get("items", [])
    api = next((a for a in apis if a["name"] == API_NAME), None)
    if not api:
        log("APIGW", "REST API not found. Skipping API route.")
        return

    api_id = api["id"]
    resources = apigw.get_resources(restApiId=api_id).get("items", [])
    docs_res = next((r for r in resources if r["path"] == "/documents"), None)
    if not docs_res:
        log("APIGW", "/documents resource missing.")
        return

    # /documents/{id}
    id_res = next((r for r in resources if r["path"] == "/documents/{id}"), None)
    if not id_res:
        id_res = apigw.create_resource(
            restApiId=api_id,
            parentId=docs_res["id"],
            pathPart="{id}"
        )

    # /documents/{id}/process
    resources = apigw.get_resources(restApiId=api_id).get("items", [])
    process_res = next((r for r in resources if r["path"] == "/documents/{id}/process"), None)
    if not process_res:
        process_res = apigw.create_resource(
            restApiId=api_id,
            parentId=id_res["id"],
            pathPart="process"
        )
    process_res_id = process_res["id"]

    # Authorizer
    authorizers = apigw.get_authorizers(restApiId=api_id).get("items", [])
    auth = next((a for a in authorizers if a["name"] == "CognitoAuthorizer"), None)
    auth_id = auth["id"] if auth else None

    # POST method
    uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    try:
        apigw.get_method(restApiId=api_id, resourceId=process_res_id, httpMethod="POST")
        log("APIGW", "POST method on /documents/{id}/process already exists.")
    except ClientError:
        apigw.put_method(
            restApiId=api_id,
            resourceId=process_res_id,
            httpMethod="POST",
            authorizationType="COGNITO_USER_POOLS" if auth_id else "NONE",
            authorizerId=auth_id if auth_id else None
        )
        apigw.put_integration(
            restApiId=api_id,
            resourceId=process_res_id,
            httpMethod="POST",
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=uri
        )

    # OPTIONS method for CORS
    try:
        apigw.get_method(restApiId=api_id, resourceId=process_res_id, httpMethod="OPTIONS")
    except ClientError:
        apigw.put_method(
            restApiId=api_id,
            resourceId=process_res_id,
            httpMethod="OPTIONS",
            authorizationType="NONE"
        )
        apigw.put_integration(
            restApiId=api_id,
            resourceId=process_res_id,
            httpMethod="OPTIONS",
            type="MOCK",
            requestTemplates={"application/json": '{"statusCode": 200}'}
        )
        apigw.put_method_response(
            restApiId=api_id,
            resourceId=process_res_id,
            httpMethod="OPTIONS",
            statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": True,
                "method.response.header.Access-Control-Allow-Methods": True,
                "method.response.header.Access-Control-Allow-Origin": True
            }
        )
        apigw.put_integration_response(
            restApiId=api_id,
            resourceId=process_res_id,
            httpMethod="OPTIONS",
            statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
                "method.response.header.Access-Control-Allow-Methods": "'POST,OPTIONS'",
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
        )

    # Lambda invoke permission
    stmt_id = f"apigw-invoke-process-{api_id}"
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=stmt_id,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{api_id}/*/*"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise e

    # Redeploy prod stage
    apigw.create_deployment(restApiId=api_id, stageName=STAGE_NAME)
    log("APIGW", f"Redeployed stage '{STAGE_NAME}' with /documents/{{id}}/process route.")

def main():
    print("=" * 65)
    print("  Milestone 4: Amazon Textract Processing Lambda & S3 Trigger")
    print(f"  Region: {AWS_REGION} | Account: {ACCOUNT_ID}")
    print("=" * 65)

    session = boto3.Session(region_name=AWS_REGION)
    iam = session.client("iam")
    lambda_client = session.client("lambda")
    s3 = session.client("s3")
    apigw = session.client("apigateway")

    # 1. IAM Permissions for Textract
    role_arn = update_iam_role_for_textract(iam)

    # 2. Package Zip
    zip_bytes = build_process_lambda_zip()

    # 3. Deploy Lambda
    lambda_arn = deploy_process_lambda(lambda_client, role_arn, zip_bytes)

    # 4. Connect S3 Event Notification Trigger
    configure_s3_event_trigger(s3, lambda_client, lambda_arn)

    # 5. Connect API Gateway Route: POST /documents/{id}/process
    configure_api_route(apigw, lambda_client, lambda_arn)

    print("\n" + "=" * 65)
    print("  MILESTONE 4 DEPLOYMENT COMPLETE!")
    print(f"  Lambda Function: {LAMBDA_NAME}")
    print(f"  Lambda ARN:      {lambda_arn}")
    print(f"  S3 Trigger:      s3://{BUCKET_NAME}/uploads/*")
    print(f"  API Route:       POST /documents/{{id}}/process")
    print("=" * 65)

if __name__ == "__main__":
    main()
