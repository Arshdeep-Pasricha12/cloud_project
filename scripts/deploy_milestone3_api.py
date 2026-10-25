"""
Milestone 3 Deployment Automation Script:
Provisions AWS Lambda and Amazon API Gateway REST API with Cognito Authorizer in ap-south-1.
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
USER_POOL_ID = "ap-south-1_ZIRwwnB44"
BUCKET_NAME = "doc-intelligence-uploads-399383129700"

ROLE_NAME = "doc-intelligence-lambda-role"
LAMBDA_NAME = "doc-intelligence-create-upload"
API_NAME = "doc-intelligence-api"
STAGE_NAME = "prod"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_ENV_PATH = os.path.join(BASE_DIR, "frontend", ".env")

def log(step: str, msg: str):
    print(f"[{step}] {msg}")

def get_or_create_lambda_role(iam):
    """Ensure IAM execution role for Lambda exists with S3 and CloudWatch permissions."""
    log("IAM", f"Checking role '{ROLE_NAME}'...")
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        res = iam.get_role(RoleName=ROLE_NAME)
        role_arn = res["Role"]["Arn"]
        log("IAM", f"Role already exists: {role_arn}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            log("IAM", f"Creating role '{ROLE_NAME}'...")
            res = iam.create_role(
                RoleName=ROLE_NAME,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description="Execution role for Document Intelligence Lambda functions"
            )
            role_arn = res["Role"]["Arn"]
            log("IAM", f"Created role: {role_arn}")
            # Attach Basic Lambda Execution managed policy
            iam.attach_role_policy(
                RoleName=ROLE_NAME,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            log("IAM", "Attached AWSLambdaBasicExecutionRole policy.")
            # Wait for IAM role propagation
            log("IAM", "Waiting 10s for IAM eventual consistency...")
            time.sleep(10)
        else:
            raise e

    # Ensure S3 inline policy is attached
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowS3OperationsOnUploads",
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject"
                ],
                "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
            }
        ]
    }
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="DocIntelligenceS3Policy",
        PolicyDocument=json.dumps(s3_policy)
    )
    log("IAM", "Updated inline S3 policy on role.")
    return role_arn

def build_lambda_zip() -> bytes:
    """Build in-memory zip bundle with create-upload handler and shared package."""
    log("BUILD", "Packaging Lambda zip artifact...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Add handler.py from backend/functions/create-upload/handler.py
        handler_path = os.path.join(BACKEND_DIR, "functions", "create-upload", "handler.py")
        zf.write(handler_path, arcname="handler.py")

        # 2. Add shared package
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

def deploy_lambda(lambda_client, role_arn: str, zip_bytes: bytes) -> str:
    """Create or update Lambda function."""
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
            Timeout=15,
            MemorySize=256,
            Environment={"Variables": env_vars}
        )
        function_arn = res["Configuration"]["FunctionArn"]
        log("LAMBDA", f"Updated Lambda: {function_arn}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            log("LAMBDA", f"Creating new Lambda function '{LAMBDA_NAME}'...")
            # Retry a few times if IAM role hasn't fully propagated
            for attempt in range(5):
                try:
                    res = lambda_client.create_function(
                        FunctionName=LAMBDA_NAME,
                        Runtime="python3.12",
                        Role=role_arn,
                        Handler="handler.lambda_handler",
                        Code={"ZipFile": zip_bytes},
                        Description="Generates S3 presigned PUT URLs for document intelligence uploads",
                        Timeout=15,
                        MemorySize=256,
                        Environment={"Variables": env_vars}
                    )
                    function_arn = res["FunctionArn"]
                    log("LAMBDA", f"Created Lambda function: {function_arn}")
                    break
                except ClientError as ce:
                    if "cannot be assumed by Lambda" in str(ce) and attempt < 4:
                        log("LAMBDA", f"Waiting for IAM role to propagate (attempt {attempt+1}/5)...")
                        time.sleep(5)
                    else:
                        raise ce
        else:
            raise e

    return function_arn

def get_or_create_rest_api(apigw):
    """Find or create API Gateway REST API."""
    log("APIGW", f"Searching for REST API '{API_NAME}'...")
    apis = apigw.get_rest_apis().get("items", [])
    for api in apis:
        if api["name"] == API_NAME:
            log("APIGW", f"Found existing REST API: {api['id']}")
            return api["id"]

    log("APIGW", f"Creating new REST API '{API_NAME}'...")
    res = apigw.create_rest_api(
        name=API_NAME,
        description="Serverless Document Intelligence Platform API",
        endpointConfiguration={"types": ["REGIONAL"]}
    )
    api_id = res["id"]
    log("APIGW", f"Created REST API: {api_id}")
    return api_id

def setup_cognito_authorizer(apigw, api_id: str) -> str:
    """Ensure Cognito User Pool Authorizer is configured on API Gateway."""
    log("AUTHORIZER", "Configuring Cognito User Pool Authorizer...")
    user_pool_arn = f"arn:aws:cognito-idp:{AWS_REGION}:{ACCOUNT_ID}:userpool/{USER_POOL_ID}"
    authorizers = apigw.get_authorizers(restApiId=api_id).get("items", [])
    for auth in authorizers:
        if auth["name"] == "CognitoAuthorizer":
            log("AUTHORIZER", f"Found existing authorizer: {auth['id']}")
            return auth["id"]

    res = apigw.create_authorizer(
        restApiId=api_id,
        name="CognitoAuthorizer",
        type="COGNITO_USER_POOLS",
        providerARNs=[user_pool_arn],
        identitySource="method.request.header.Authorization"
    )
    authorizer_id = res["id"]
    log("AUTHORIZER", f"Created Cognito authorizer: {authorizer_id}")
    return authorizer_id

def setup_resource_and_methods(apigw, lambda_client, api_id: str, authorizer_id: str, lambda_arn: str):
    """Create /documents/upload-url path with POST and CORS OPTIONS methods."""
    log("RESOURCES", "Configuring API resources and methods...")
    resources = apigw.get_resources(restApiId=api_id).get("items", [])
    root_id = next(r["id"] for r in resources if r["path"] == "/")
    
    # 1. /documents resource
    docs_res = next((r for r in resources if r["path"] == "/documents"), None)
    if not docs_res:
        log("RESOURCES", "Creating resource '/documents'...")
        docs_res = apigw.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart="documents"
        )
    docs_id = docs_res["id"]

    # 2. /documents/upload-url resource
    resources = apigw.get_resources(restApiId=api_id).get("items", [])
    upload_res = next((r for r in resources if r["path"] == "/documents/upload-url"), None)
    if not upload_res:
        log("RESOURCES", "Creating resource '/documents/upload-url'...")
        upload_res = apigw.create_resource(
            restApiId=api_id,
            parentId=docs_id,
            pathPart="upload-url"
        )
    upload_res_id = upload_res["id"]

    # 3. OPTIONS method for CORS preflight
    try:
        apigw.get_method(restApiId=api_id, resourceId=upload_res_id, httpMethod="OPTIONS")
        log("CORS", "OPTIONS method already exists.")
    except ClientError:
        log("CORS", "Creating OPTIONS method on /documents/upload-url...")
        apigw.put_method(
            restApiId=api_id,
            resourceId=upload_res_id,
            httpMethod="OPTIONS",
            authorizationType="NONE"
        )
        apigw.put_integration(
            restApiId=api_id,
            resourceId=upload_res_id,
            httpMethod="OPTIONS",
            type="MOCK",
            requestTemplates={"application/json": '{"statusCode": 200}'}
        )
        apigw.put_method_response(
            restApiId=api_id,
            resourceId=upload_res_id,
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
            resourceId=upload_res_id,
            httpMethod="OPTIONS",
            statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
                "method.response.header.Access-Control-Allow-Methods": "'POST,OPTIONS'",
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
        )

    # 4. POST method for presigned URL request with Cognito Authorizer
    uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    try:
        apigw.get_method(restApiId=api_id, resourceId=upload_res_id, httpMethod="POST")
        log("POST", "Updating existing POST method on /documents/upload-url...")
        # Update authorizer
        apigw.update_method(
            restApiId=api_id,
            resourceId=upload_res_id,
            httpMethod="POST",
            patchOperations=[
                {"op": "replace", "path": "/authorizationType", "value": "COGNITO_USER_POOLS"},
                {"op": "replace", "path": "/authorizerId", "value": authorizer_id}
            ]
        )
    except ClientError:
        log("POST", "Creating POST method on /documents/upload-url with Cognito Authorizer...")
        apigw.put_method(
            restApiId=api_id,
            resourceId=upload_res_id,
            httpMethod="POST",
            authorizationType="COGNITO_USER_POOLS",
            authorizerId=authorizer_id
        )

    # Configure Lambda Proxy integration on POST
    apigw.put_integration(
        restApiId=api_id,
        resourceId=upload_res_id,
        httpMethod="POST",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=uri
    )

    # 5. Grant API Gateway permission to invoke Lambda
    statement_id = f"apigw-invoke-{api_id}"
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{api_id}/*/*"
        )
        log("PERMISSIONS", "Added Lambda invoke permission for API Gateway.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            log("PERMISSIONS", "Lambda invoke permission already exists.")
        else:
            raise e

    # 5b. Configure Gateway Responses with CORS for 4XX and 5XX
    log("CORS", "Configuring Gateway Responses for 4XX and 5XX with CORS...")
    cors_params = {
        "gatewayresponse.header.Access-Control-Allow-Origin": "'*'",
        "gatewayresponse.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
        "gatewayresponse.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'"
    }
    for r_type in ["DEFAULT_4XX", "DEFAULT_5XX"]:
        try:
            apigw.put_gateway_response(
                restApiId=api_id,
                responseType=r_type,
                responseParameters=cors_params
            )
        except Exception as e:
            log("CORS", f"Gateway response warning: {e}")

    # 6. Deploy API to STAGE_NAME
    log("DEPLOY", f"Deploying API to stage '{STAGE_NAME}'...")
    apigw.create_deployment(
        restApiId=api_id,
        stageName=STAGE_NAME,
        description="Milestone 3 deployment with Cognito Authorizer"
    )

    endpoint_url = f"https://{api_id}.execute-api.{AWS_REGION}.amazonaws.com/{STAGE_NAME}/documents/upload-url"
    base_url = f"https://{api_id}.execute-api.{AWS_REGION}.amazonaws.com/{STAGE_NAME}"
    return endpoint_url, base_url

def update_frontend_env(endpoint_url: str, base_url: str):
    """Update frontend/.env with live API Gateway URLs."""
    log("CONFIG", "Updating frontend/.env with live API Gateway endpoints...")
    if not os.path.exists(FRONTEND_ENV_PATH):
        log("CONFIG", f"Warning: {FRONTEND_ENV_PATH} not found.")
        return

    with open(FRONTEND_ENV_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace VITE_UPLOAD_API_URL
    lines = content.splitlines()
    new_lines = []
    has_base = False
    for line in lines:
        if line.startswith("VITE_UPLOAD_API_URL="):
            new_lines.append(f"VITE_UPLOAD_API_URL={endpoint_url}")
        elif line.startswith("VITE_API_BASE_URL="):
            new_lines.append(f"VITE_API_BASE_URL={base_url}")
            has_base = True
        else:
            new_lines.append(line)

    if not has_base:
        new_lines.insert(3, f"VITE_API_BASE_URL={base_url}")

    with open(FRONTEND_ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    log("CONFIG", "frontend/.env successfully updated!")

def main():
    print("=" * 65)
    print("  Milestone 3: AWS API Gateway & Lambda Deployment")
    print(f"  Region: {AWS_REGION} | Account: {ACCOUNT_ID}")
    print("=" * 65)

    session = boto3.Session(region_name=AWS_REGION)
    iam = session.client("iam")
    lambda_client = session.client("lambda")
    apigw = session.client("apigateway")

    # 1. IAM Role
    role_arn = get_or_create_lambda_role(iam)

    # 2. Package Zip
    zip_bytes = build_lambda_zip()

    # 3. Lambda Function
    lambda_arn = deploy_lambda(lambda_client, role_arn, zip_bytes)

    # 4. API Gateway REST API
    api_id = get_or_create_rest_api(apigw)

    # 5. Cognito Authorizer
    authorizer_id = setup_cognito_authorizer(apigw, api_id)

    # 6. Resources, Methods & Deployment
    endpoint_url, base_url = setup_resource_and_methods(
        apigw, lambda_client, api_id, authorizer_id, lambda_arn
    )

    # 7. Update Frontend Config
    update_frontend_env(endpoint_url, base_url)

    print("\n" + "=" * 65)
    print("  MILESTONE 3 DEPLOYMENT COMPLETE!")
    print(f"  REST API ID:     {api_id}")
    print(f"  Live Base URL:   {base_url}")
    print(f"  Upload Endpoint: {endpoint_url}")
    print(f"  Authorizer:      Cognito User Pool ({USER_POOL_ID})")
    print("=" * 65)

if __name__ == "__main__":
    main()
