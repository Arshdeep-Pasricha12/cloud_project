"""
Milestone 6 Deployment Automation Script:
Deploys doc-intelligence-save-corrections Lambda function, connects PUT /documents/{id}/corrections
to API Gateway with Cognito Authorizer, and configures CORS preflight.
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
ROLE_NAME = "doc-intelligence-lambda-role"
LAMBDA_NAME = "doc-intelligence-save-corrections"
API_NAME = "doc-intelligence-api"
STAGE_NAME = "prod"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

def log(step: str, msg: str):
    print(f"[{step}] {msg}")

def build_lambda_zip() -> bytes:
    """Build in-memory zip bundle with save-corrections handler and shared package."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        handler_path = os.path.join(BACKEND_DIR, "functions", "save-corrections", "handler.py")
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

def deploy_save_corrections_lambda(lambda_client, role_arn: str) -> str:
    """Deploy or update doc-intelligence-save-corrections Lambda."""
    log("LAMBDA", f"Checking function '{LAMBDA_NAME}'...")
    zip_bytes = build_lambda_zip()
    env_vars = {"DOCUMENTS_TABLE_NAME": TABLE_NAME}

    try:
        res = lambda_client.get_function(FunctionName=LAMBDA_NAME)
        log("LAMBDA", "Function exists. Updating code and configuration...")
        lambda_client.update_function_code(FunctionName=LAMBDA_NAME, ZipFile=zip_bytes)
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
        return res["Configuration"]["FunctionArn"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            log("LAMBDA", f"Creating new function '{LAMBDA_NAME}'...")
            res = lambda_client.create_function(
                FunctionName=LAMBDA_NAME,
                Runtime="python3.12",
                Role=role_arn,
                Handler="handler.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Description="Persists human-in-the-loop invoice corrections while preserving raw extraction immutability",
                Timeout=15,
                MemorySize=256,
                Environment={"Variables": env_vars}
            )
            return res["FunctionArn"]
        else:
            raise e

def configure_api_route(apigw, lambda_client, lambda_arn: str):
    """Expose PUT /documents/{id}/corrections on API Gateway."""
    log("APIGW", "Configuring PUT /documents/{id}/corrections route on API Gateway...")
    apis = apigw.get_rest_apis().get("items", [])
    api = next((a for a in apis if a["name"] == API_NAME), None)
    if not api:
        raise RuntimeError(f"REST API '{API_NAME}' not found.")
    api_id = api["id"]

    resources = apigw.get_resources(restApiId=api_id).get("items", [])
    id_res = next((r for r in resources if r["path"] == "/documents/{id}"), None)
    if not id_res:
        raise RuntimeError("Resource '/documents/{id}' not found.")
    id_res_id = id_res["id"]

    # /documents/{id}/corrections
    corrections_res = next((r for r in resources if r["path"] == "/documents/{id}/corrections"), None)
    if not corrections_res:
        log("APIGW", "Creating resource '/documents/{id}/corrections'...")
        corrections_res = apigw.create_resource(
            restApiId=api_id,
            parentId=id_res_id,
            pathPart="corrections"
        )
    corrections_res_id = corrections_res["id"]

    # Authorizer
    authorizers = apigw.get_authorizers(restApiId=api_id).get("items", [])
    auth = next((a for a in authorizers if a["name"] == "CognitoAuthorizer"), None)
    auth_id = auth["id"] if auth else None

    # PUT method
    uri = f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    try:
        apigw.get_method(restApiId=api_id, resourceId=corrections_res_id, httpMethod="PUT")
        log("APIGW", "PUT method on /documents/{id}/corrections already exists.")
    except ClientError:
        log("APIGW", "Creating PUT method on /documents/{id}/corrections...")
        apigw.put_method(
            restApiId=api_id,
            resourceId=corrections_res_id,
            httpMethod="PUT",
            authorizationType="COGNITO_USER_POOLS" if auth_id else "NONE",
            authorizerId=auth_id if auth_id else None
        )
        apigw.put_integration(
            restApiId=api_id,
            resourceId=corrections_res_id,
            httpMethod="PUT",
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=uri
        )

    # OPTIONS method for CORS
    try:
        apigw.get_method(restApiId=api_id, resourceId=corrections_res_id, httpMethod="OPTIONS")
    except ClientError:
        apigw.put_method(
            restApiId=api_id,
            resourceId=corrections_res_id,
            httpMethod="OPTIONS",
            authorizationType="NONE"
        )
        apigw.put_integration(
            restApiId=api_id,
            resourceId=corrections_res_id,
            httpMethod="OPTIONS",
            type="MOCK",
            requestTemplates={"application/json": '{"statusCode": 200}'}
        )
        apigw.put_method_response(
            restApiId=api_id,
            resourceId=corrections_res_id,
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
            resourceId=corrections_res_id,
            httpMethod="OPTIONS",
            statusCode="200",
            responseParameters={
                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
                "method.response.header.Access-Control-Allow-Methods": "'PUT,OPTIONS'",
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
        )

    # Lambda invoke permission
    stmt_id = f"apigw-invoke-save-corrections-{api_id}"
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=stmt_id,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{api_id}/*/*"
        )
        log("PERMISSIONS", "Added Lambda invoke permission for API Gateway.")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise e

    # Redeploy prod stage
    apigw.create_deployment(restApiId=api_id, stageName=STAGE_NAME)
    log("APIGW", f"Redeployed API Gateway stage '{STAGE_NAME}' with corrections route.")

def main():
    print("=" * 65)
    print("  Milestone 6: Human-in-the-Loop Corrections Deployment")
    print(f"  Region: {AWS_REGION} | Account: {ACCOUNT_ID}")
    print("=" * 65)

    session = boto3.Session(region_name=AWS_REGION)
    iam = session.client("iam")
    lambda_client = session.client("lambda")
    apigw = session.client("apigateway")

    # 1. Get Role ARN
    role_res = iam.get_role(RoleName=ROLE_NAME)
    role_arn = role_res["Role"]["Arn"]

    # 2. Deploy Lambda
    lambda_arn = deploy_save_corrections_lambda(lambda_client, role_arn)

    # 3. Configure API Route: PUT /documents/{id}/corrections
    configure_api_route(apigw, lambda_client, lambda_arn)

    print("\n" + "=" * 65)
    print("  MILESTONE 6 BACKEND DEPLOYMENT COMPLETE!")
    print(f"  Lambda Function: {LAMBDA_NAME}")
    print(f"  Lambda ARN:      {lambda_arn}")
    print(f"  API Route:       PUT /documents/{{id}}/corrections")
    print("=" * 65)

if __name__ == "__main__":
    main()
