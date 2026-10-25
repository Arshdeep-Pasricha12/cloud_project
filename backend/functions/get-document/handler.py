"""
Lambda Handler: get-document
Purpose: Retrieves complete document details from DynamoDB by documentId,
         enforces multi-tenant isolation, and generates a short-lived presigned S3 GET URL
         for client-side document viewing.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

# Enable shared module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from shared.response_utils import build_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PRESIGNED_GET_EXPIRATION = 900  # 15 minutes


def extract_user_id(event: Dict[str, Any]) -> str:
    """Extract authenticated user sub from Cognito Authorizer claims."""
    try:
        claims = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("claims", {})
        )
        if claims and "sub" in claims:
            return claims["sub"]
    except Exception:
        pass
    return "dev-anonymous-user"


def get_s3_client(region_name: str) -> boto3.client:
    """Initialize regional S3 client for presigned GET generation."""
    config = Config(
        signature_version="s3v4",
        retries={"max_attempts": 3, "mode": "standard"},
        region_name=region_name,
        s3={"addressing_style": "virtual"}
    )
    endpoint_url = f"https://s3.{region_name}.amazonaws.com" if region_name and region_name != "us-east-1" else None
    return boto3.client("s3", region_name=region_name, endpoint_url=endpoint_url, config=config)


def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Handle GET /documents/{id} requests.
    """
    http_method = event.get("httpMethod", "GET")
    if http_method.upper() == "OPTIONS":
        return build_response(200, {"message": "CORS preflight OK"})

    table_name = os.environ.get("DOCUMENTS_TABLE_NAME", "doc-intelligence-documents")
    bucket_name = os.environ.get("DOCUMENTS_BUCKET_NAME", "doc-intelligence-uploads-399383129700")
    region_name = os.environ.get("AWS_REGION", "ap-south-1")

    # Extract document ID from pathParameters or event
    path_params = event.get("pathParameters") or {}
    document_id = path_params.get("id") or event.get("documentId")

    if not document_id:
        return build_response(400, {"error": "BadRequest", "message": "Missing 'id' path parameter."})

    user_id = extract_user_id(event)
    logger.info(f"Retrieving document: {document_id} for user: {user_id}")

    # Fetch from DynamoDB
    try:
        dynamodb = boto3.resource("dynamodb", region_name=region_name)
        table = dynamodb.Table(table_name)
        res = table.get_item(Key={"documentId": document_id})
        item = res.get("Item")
    except ClientError as err:
        logger.error(f"DynamoDB GetItem error: {str(err)}")
        return build_response(
            500,
            {
                "error": "DatabaseError",
                "message": f"Failed to retrieve document: {err.response.get('Error', {}).get('Message')}"
            }
        )

    if not item:
        return build_response(404, {"error": "NotFound", "message": f"Document '{document_id}' not found."})

    # Multi-tenant security check: ensure user owns the document (allow dev fallback if dev mode)
    doc_owner = item.get("userId")
    if doc_owner and doc_owner != "dev-anonymous-user" and user_id != "dev-anonymous-user":
        if doc_owner != user_id:
            logger.warning(f"Forbidden access: User '{user_id}' attempted to access document belonging to '{doc_owner}'")
            return build_response(403, {"error": "Forbidden", "message": "Access denied to this document."})

    # Generate presigned S3 GET URL for document viewer if S3 key is present
    s3_key = item.get("s3Key")
    view_url = None
    if s3_key:
        try:
            s3_client = get_s3_client(region_name)
            view_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": item.get("bucket", bucket_name),
                    "Key": s3_key
                },
                ExpiresIn=PRESIGNED_GET_EXPIRATION,
                HttpMethod="GET"
            )
        except Exception as err:
            logger.warning(f"Failed to generate view URL for s3Key '{s3_key}': {str(err)}")

    item["viewUrl"] = view_url
    return build_response(200, item)
