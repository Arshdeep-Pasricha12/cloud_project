"""
Milestone 5 Deployment Automation Script:
1. Creates Amazon DynamoDB Table 'doc-intelligence-documents' with UserDocumentsIndex GSI (Pay-Per-Request).
2. Grants DynamoDB permissions to doc-intelligence-lambda-role.
3. Deploys doc-intelligence-list-documents Lambda.
4. Deploys doc-intelligence-get-document Lambda.
5. Updates doc-intelligence-create-upload and doc-intelligence-process-document with DOCUMENTS_TABLE_NAME.
6. Connects GET /documents and GET /documents/{id} to API Gateway with Cognito Authorizer & CORS.
7. Redeploys API Gateway prod stage.
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
TABLE_NAME = "doc-intelligence-documents"
BUCKET_NAME = "doc-intelligence-uploads-399383129700"
ROLE_NAME = "doc-intelligence-lambda-role"
API_NAME = "doc-intelligence-api"
STAGE_NAME = "prod"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_ENV_PATH = os.path.join(BASE_DIR, "frontend", ".env")

def log(step: str, msg: str):
    print(f"[{step}] {msg}")

def create_dynamodb_table(dynamodb_client) -> str:
    """Create DynamoDB documents table with UserDocumentsIndex GSI."""
    log("DYNAMODB", f"Checking table '{TABLE_NAME}'...")
    try:
        res = dynamodb_client.describe_table(TableName=TABLE_NAME)
        table_arn = res["Table"]["TableArn"]
        log("DYNAMODB", f"Table already exists: {table_arn}")
        return table_arn
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise e

    log("DYNAMODB", f"Creating DynamoDB table '{TABLE_NAME}' (PAY_PER_REQUEST)...")
    res = dynamodb_client.create_table(
        TableName=TABLE_NAME,
        AttributeDefinitions=[
            {"AttributeName": "documentId", "AttributeType": "S"},
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "S"}
        ],
        KeySchema=[
            {"AttributeName": "documentId", "KeyType": "HASH"}
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "UserDocumentsIndex",
                "KeySchema": [
                    {"AttributeName": "userId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    table_arn = res["TableDescription"]["TableArn"]
    log("DYNAMODB", f"Table created: {table_arn}. Waiting for ACTIVE status...")

    waiter = dynamodb_client.get_waiter("table_exists")
    waiter.wait(TableName=TABLE_NAME)
    log("DYNAMODB", "Table is now ACTIVE.")
    return table_arn

def update_iam_role_for_dynamodb(iam):
    """Grant DynamoDB permissions to the Lambda execution role."""
    log("IAM", "Adding DynamoDB policy to Lambda execution role...")
    table_arn = f"arn:aws:dynamodb:{AWS_REGION}:{ACCOUNT_ID}:table/{TABLE_NAME}"
    ddb_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowDynamoDBDocumentOperations",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    table_arn,
                    f"{table_arn}/index/*"
                ]
            }
        ]
    }
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="DocIntelligenceDynamoDBPolicy",
        PolicyDocument=json.dumps(ddb_policy)
    )
    role_res = iam.get_role(RoleName=ROLE_NAME)
    log("IAM", f"Updated DynamoDB policy on role: {role_res['Role']['Arn']}")
    return role_res["Role"]["Arn"]

def build_lambda_zip(handler_subpath: str) -> bytes:
    """Build in-memory zip bundle with a specific handler and shared package."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        handler_path = os.path.join(BACKEND_DIR, "functions", handler_subpath, "handler.py")
        zf.write(handler_path, arcname="handler.py")

        shared_dir = os.path.join(BACKEND_DIR, "shared")
        for root, _, files in os.walk(shared_dir):
            for file in files:
                if file.endswith(".pyc") or "__pycache__" in root:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BACKEND_DIR)
                zf.write(full_path, arcname=rel_path.replace("\\", "/"))

    return zip_buffer.getvalue()

def deploy_lambda_function(lambda_client, name: str, handler_subpath: str, role_arn: str, env_vars: dict, timeout=15, memory=256) -> str:
    """Deploy or update a Lambda function."""
    log("LAMBDA", f"Deploying '{name}'...")
    zip_bytes = build_lambda_zip(handler_subpath)

    try:
        res = lambda_client.get_function(FunctionName=name)
        log("LAMBDA", f"Updating code for '{name}'...")
        lambda_client.update_function_code(FunctionName=name, ZipFile=zip_bytes)
        time.sleep(3)
        lambda_client.update_function_configuration(
            FunctionName=name,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.lambda_handler",
            Timeout=timeout,
            MemorySize=memory,
            Environment={"Variables": env_vars}
        )
        return res["Configuration"]["FunctionArn"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            log("LAMBDA", f"Creating new function '{name}'...")
            res = lambda_client.create_function(
                FunctionName=name,
                Runtime="python3.12",
                Role=role_arn,
                Handler="handler.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Timeout=timeout,
                MemorySize=memory,
                Environment={"Variables": env_vars}
            )
            return res["FunctionArn"]
        else:
            raise e

def configure_api_routes(apigw, lambda_client, list_lambda_arn: str, get_lambda_arn: str):
    """Configure GET /documents and GET /documents/{id} on API Gateway."""
    log("APIGW", "Configuring DynamoDB document query routes on API Gateway...")
    apis = apigw.get_rest_apis().get("items", [])
    api = next((a for a in apis if a["name"] == API_NAME), None)
    if not api:
        raise RuntimeError(f"REST API '{API_NAME}' not found.")
    api_id = api["id"]

    resources = apigw.get_resources(restApiId=api_id).get("items", [])
    docs_res = next((r for r in resources if r["path"] == "/documents"), None)
    if not docs_res:
        raise RuntimeError("Resource '/documents' not found.")
    docs_res_id = docs_res["id"]

    # Authorizer
    authorizers = apigw.get_authorizers(restApiId=api_id).get("items", [])
    auth = next((a for a in authorizers if a["name"] == "CognitoAuthorizer"), None)
    auth_id = auth["id"] if auth else None

    # 1. GET /documents (List Documents)
    list_uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{list_lambda_arn}/invocations"
    try:
        apigw.get_method(restApiId=api_id, resourceId=docs_res_id, httpMethod="GET")
        log("APIGW", "Updating GET /documents method...")
    except ClientError:
        log("APIGW", "Creating GET /documents method...")
        apigw.put_method(
            restApiId=api_id,
            resourceId=docs_res_id,
            httpMethod="GET",
            authorizationType="COGNITO_USER_POOLS" if auth_id else "NONE",
            authorizerId=auth_id if auth_id else None
        )
    apigw.put_integration(
        restApiId=api_id,
        resourceId=docs_res_id,
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=list_uri
    )

    # OPTIONS for /documents
    try:
        apigw.get_method(restApiId=api_id, resourceId=docs_res_id, httpMethod="OPTIONS")
    except ClientError:
        apigw.put_method(restApiId=api_id, resourceId=docs_res_id, httpMethod="OPTIONS", authorizationType="NONE")
        apigw.put_integration(restApiId=api_id, resourceId=docs_res_id, httpMethod="OPTIONS", type="MOCK", requestTemplates={"application/json": '{"statusCode": 200}'})
        apigw.put_method_response(
            restApiId=api_id, resourceId=docs_res_id, httpMethod="OPTIONS", statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": True,
                "method.response.header.Access-Control-Allow-Methods": True,
                "method.response.header.Access-Control-Allow-Origin": True
            }
        )
        apigw.put_integration_response(
            restApiId=api_id, resourceId=docs_res_id, httpMethod="OPTIONS", statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
                "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
        )

    # 2. GET /documents/{id} (Get Document)
    resources = apigw.get_resources(restApiId=api_id).get("items", [])
    id_res = next((r for r in resources if r["path"] == "/documents/{id}"), None)
    if not id_res:
        id_res = apigw.create_resource(restApiId=api_id, parentId=docs_res_id, pathPart="{id}")
    id_res_id = id_res["id"]

    get_uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{get_lambda_arn}/invocations"
    try:
        apigw.get_method(restApiId=api_id, resourceId=id_res_id, httpMethod="GET")
        log("APIGW", "Updating GET /documents/{id} method...")
    except ClientError:
        log("APIGW", "Creating GET /documents/{id} method...")
        apigw.put_method(
            restApiId=api_id,
            resourceId=id_res_id,
            httpMethod="GET",
            authorizationType="COGNITO_USER_POOLS" if auth_id else "NONE",
            authorizerId=auth_id if auth_id else None
        )
    apigw.put_integration(
        restApiId=api_id,
        resourceId=id_res_id,
        httpMethod="GET",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=get_uri
    )

    # OPTIONS for /documents/{id}
    try:
        apigw.get_method(restApiId=api_id, resourceId=id_res_id, httpMethod="OPTIONS")
    except ClientError:
        apigw.put_method(restApiId=api_id, resourceId=id_res_id, httpMethod="OPTIONS", authorizationType="NONE")
        apigw.put_integration(restApiId=api_id, resourceId=id_res_id, httpMethod="OPTIONS", type="MOCK", requestTemplates={"application/json": '{"statusCode": 200}'})
        apigw.put_method_response(
            restApiId=api_id, resourceId=id_res_id, httpMethod="OPTIONS", statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": True,
                "method.response.header.Access-Control-Allow-Methods": True,
                "method.response.header.Access-Control-Allow-Origin": True
            }
        )
        apigw.put_integration_response(
            restApiId=api_id, resourceId=id_res_id, httpMethod="OPTIONS", statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
                "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
        )

    # Lambda invoke permissions
    for fname, name_key in [("doc-intelligence-list-documents", "list"), ("doc-intelligence-get-document", "get")]:
        stmt_id = f"apigw-invoke-{name_key}-{api_id}"
        try:
            lambda_client.add_permission(
                FunctionName=fname,
                StatementId=stmt_id,
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{api_id}/*/*"
            )
            log("PERMISSIONS", f"Added invoke permission for {fname}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceConflictException":
                raise e

    # Redeploy prod stage
    apigw.create_deployment(restApiId=api_id, stageName=STAGE_NAME)
    log("APIGW", f"Redeployed API Gateway stage '{STAGE_NAME}' with DynamoDB routes.")

def update_frontend_env():
    """Ensure VITE_DYNAMODB_DOCUMENTS_TABLE is present in frontend/.env."""
    if not os.path.exists(FRONTEND_ENV_PATH):
        return
    with open(FRONTEND_ENV_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "VITE_DYNAMODB_DOCUMENTS_TABLE=" not in content:
        content += f"\nVITE_DYNAMODB_DOCUMENTS_TABLE={TABLE_NAME}\n"
        with open(FRONTEND_ENV_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        log("CONFIG", f"Added VITE_DYNAMODB_DOCUMENTS_TABLE={TABLE_NAME} to frontend/.env")

def main():
    print("=" * 65)
    print("  Milestone 5: Amazon DynamoDB Persistence & Query APIs")
    print(f"  Region: {AWS_REGION} | Account: {ACCOUNT_ID}")
    print("=" * 65)

    session = boto3.Session(region_name=AWS_REGION)
    iam = session.client("iam")
    lambda_client = session.client("lambda")
    ddb_client = session.client("dynamodb")
    apigw = session.client("apigateway")

    # 1. DynamoDB Table
    table_arn = create_dynamodb_table(ddb_client)

    # 2. IAM Permissions
    role_arn = update_iam_role_for_dynamodb(iam)

    # 3. Deploy list-documents Lambda
    list_arn = deploy_lambda_function(
        lambda_client,
        name="doc-intelligence-list-documents",
        handler_subpath="list-documents",
        role_arn=role_arn,
        env_vars={"DOCUMENTS_TABLE_NAME": TABLE_NAME}
    )

    # 4. Deploy get-document Lambda
    get_arn = deploy_lambda_function(
        lambda_client,
        name="doc-intelligence-get-document",
        handler_subpath="get-document",
        role_arn=role_arn,
        env_vars={
            "DOCUMENTS_TABLE_NAME": TABLE_NAME,
            "DOCUMENTS_BUCKET_NAME": BUCKET_NAME
        }
    )

    # 5. Update create-upload Lambda with DOCUMENTS_TABLE_NAME
    deploy_lambda_function(
        lambda_client,
        name="doc-intelligence-create-upload",
        handler_subpath="create-upload",
        role_arn=role_arn,
        env_vars={
            "DOCUMENTS_BUCKET_NAME": BUCKET_NAME,
            "DOCUMENTS_TABLE_NAME": TABLE_NAME
        }
    )

    # 6. Update process-document Lambda with DOCUMENTS_TABLE_NAME
    deploy_lambda_function(
        lambda_client,
        name="doc-intelligence-process-document",
        handler_subpath="process-document",
        role_arn=role_arn,
        env_vars={
            "DOCUMENTS_BUCKET_NAME": BUCKET_NAME,
            "DOCUMENTS_TABLE_NAME": TABLE_NAME
        },
        timeout=60,
        memory=512
    )

    # 7. Configure API Gateway routes: GET /documents and GET /documents/{id}
    configure_api_routes(apigw, lambda_client, list_arn, get_arn)

    # 8. Update frontend environment
    update_frontend_env()

    print("\n" + "=" * 65)
    print("  MILESTONE 5 DEPLOYMENT COMPLETE!")
    print(f"  DynamoDB Table:  {TABLE_NAME}")
    print(f"  GSI Index:       UserDocumentsIndex (userId + createdAt)")
    print(f"  List API Route:  GET /documents")
    print(f"  Get API Route:   GET /documents/{{id}}")
    print("=" * 65)

if __name__ == "__main__":
    main()
