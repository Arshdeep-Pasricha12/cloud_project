"""
Lambda Handler: create-upload
Purpose: Validates document upload metadata and generates a short-lived S3 presigned PUT URL.

Architecture & Security Notes:
-----------------------------
1. S3 Presigned URL Security:
   - The presigned URL is restricted to HTTP PUT for a server-generated object key.
   - The Content-Type is signed into the signature; S3 rejects any upload where
     the client's Content-Type header does not match what was requested.
   - Short expiration (300 seconds / 5 minutes) limits exposure window.
   - No AWS credentials or secrets are ever returned to the client.

2. Security Limitation Disclosure (Pre-Authentication Milestone):
   - In this development milestone, uploads are scoped to a development identity
     ('dev-anonymous-user') until Amazon Cognito User Pool authentication (Milestone 1/3)
     is connected to the API Gateway authorizer.
   - A presigned PUT URL validates that the client-declared Content-Type matches during upload,
     but cannot independently enforce the actual file size or verify file magic bytes at the
     instant of PUT. Frontend validation is NOT a security boundary.
   - Production hardening in subsequent milestones:
     (a) API Gateway Cognito Authorizer enforcing authenticated sub/userId.
     (b) S3 Event Notification triggering Lambda to verify file magic bytes and actual size.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Enable shared module import for both Lambda runtime and local test execution
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from shared.models import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE_BYTES,
    URL_EXPIRATION_SECONDS,
    validate_upload_metadata,
)
from shared.response_utils import build_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_s3_client(region_name: str) -> boto3.client:
    """
    Construct Boto3 S3 client using signature version s3v4 and regional endpoint
    to prevent HTTP 307 Temporary Redirects during cross-origin browser PUT uploads.
    """
    config = Config(
        signature_version="s3v4",
        retries={"max_attempts": 3, "mode": "standard"},
        region_name=region_name,
        s3={"addressing_style": "virtual"}
    )
    endpoint_url = f"https://s3.{region_name}.amazonaws.com" if region_name and region_name != "us-east-1" else None
    return boto3.client("s3", region_name=region_name, endpoint_url=endpoint_url, config=config)


def extract_user_id(event: Dict[str, Any]) -> str:
    """
    Extract user identifier from Cognito Authorizer claims if available.
    Falls back to 'dev-anonymous-user' for this local development milestone.
    """
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


def parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely parse request body whether from API Gateway proxy event or direct call.
    """
    body = event.get("body")
    if body is None:
        # Check if the event itself is the payload (e.g. direct test invoke)
        if "fileName" in event or "contentType" in event:
            return event
        raise ValueError("Missing request body.")

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        body_trimmed = body.strip()
        if not body_trimmed:
            raise ValueError("Request body is empty.")
        try:
            parsed = json.loads(body_trimmed)
            if not isinstance(parsed, dict):
                raise ValueError("JSON request body must be a JSON object.")
            return parsed
        except json.JSONDecodeError as err:
            raise ValueError(f"Invalid JSON in request body: {str(err)}")

    raise ValueError("Unsupported request body format.")


def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Handle POST /documents/upload-url requests.
    
    Expected Request Body (JSON):
    {
        "fileName": "sample-invoice.pdf",
        "contentType": "application/pdf",
        "fileSize": 245120
    }
    
    Successful Response (HTTP 200):
    {
        "documentId": "uuid-v4",
        "uploadUrl": "https://bucket.s3.region.amazonaws.com/...",
        "s3Key": "uploads/uuid-v4/sample_invoice.pdf",
        "bucket": "your-bucket-name",
        "expiresInSeconds": 300,
        "contentType": "application/pdf",
        "fileName": "sample_invoice.pdf",
        "fileSizeBytes": 245120,
        "issuedAt": "2026-10-23T13:00:00Z"
    }
    """
    # 1. Enforce HTTP method restriction (API Gateway proxy format)
    http_method = event.get("httpMethod")
    if http_method:
        if http_method.upper() == "OPTIONS":
            return build_response(200, {"message": "CORS preflight OK"})
        if http_method.upper() != "POST":
            return build_response(
                405,
                {
                    "error": "Method Not Allowed",
                    "message": f"HTTP {http_method} is not supported. Use POST."
                },
                headers={"Allow": "POST, OPTIONS"}
            )

    # 2. Retrieve environment configuration
    bucket_name = (
        os.environ.get("DOCUMENTS_BUCKET_NAME")
        or os.environ.get("DOCUMENT_BUCKET_NAME")
        or os.environ.get("S3_BUCKET_NAME")
    )
    region_name = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )

    if not bucket_name:
        logger.error("Environment misconfiguration: S3 bucket name is not set.")
        return build_response(
            500,
            {
                "error": "ConfigurationError",
                "message": "Storage bucket is not configured on the server. Set DOCUMENTS_BUCKET_NAME."
            }
        )

    # 3. Parse JSON request body
    try:
        body = parse_request_body(event)
    except ValueError as err:
        return build_response(
            400,
            {
                "error": "BadRequest",
                "message": str(err)
            }
        )

    file_name = body.get("fileName")
    content_type = body.get("contentType")
    file_size = body.get("fileSize")

    # 4. Validate metadata
    is_valid, error_msg, sanitized_filename = validate_upload_metadata(
        file_name=file_name,
        content_type=content_type,
        file_size=file_size,
        max_size_bytes=MAX_FILE_SIZE_BYTES,
    )

    if not is_valid:
        return build_response(
            400,
            {
                "error": "ValidationError",
                "message": error_msg
            }
        )

    # 5. Generate secure, unique object key
    document_id = str(uuid.uuid4())
    user_id = extract_user_id(event)
    # Server-generated key: uploads/{document_id}/{sanitized_filename}
    s3_key = f"uploads/{document_id}/{sanitized_filename}"

    # 6. Generate presigned S3 PUT URL
    try:
        s3_client = get_s3_client(region_name)
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket_name,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=URL_EXPIRATION_SECONDS,
            HttpMethod="PUT",
        )
    except ClientError as err:
        logger.error(f"S3 ClientError while generating presigned URL: {str(err)}")
        return build_response(
            500,
            {
                "error": "StorageError",
                "message": "Failed to generate presigned upload URL from storage service."
            }
        )
    except Exception as err:
        logger.error(f"Unexpected error while generating presigned URL: {str(err)}")
        return build_response(
            500,
            {
                "error": "InternalServerError",
                "message": "An internal error occurred while processing the upload request."
            }
        )

    # 7. Persist initial document record into DynamoDB with status UPLOADED
    table_name = os.environ.get("DOCUMENTS_TABLE_NAME")
    now_iso = datetime.now(timezone.utc).isoformat()
    if table_name:
        try:
            dynamodb = boto3.resource("dynamodb", region_name=region_name)
            table = dynamodb.Table(table_name)
            table.put_item(
                Item={
                    "documentId": document_id,
                    "userId": user_id,
                    "fileName": sanitized_filename,
                    "fileSizeBytes": int(file_size),
                    "contentType": content_type,
                    "bucket": bucket_name,
                    "s3Key": s3_key,
                    "status": "UPLOADED",
                    "createdAt": now_iso,
                    "updatedAt": now_iso,
                }
            )
            logger.info(f"Persisted initial document record '{document_id}' to DynamoDB table '{table_name}'")
        except Exception as ddb_err:
            logger.warning(f"Could not persist upload to DynamoDB: {str(ddb_err)}")

    # 8. Construct successful response (never exposes credentials or private keys)
    response_payload = {
        "documentId": document_id,
        "uploadUrl": presigned_url,
        "s3Key": s3_key,
        "bucket": bucket_name,
        "expiresInSeconds": URL_EXPIRATION_SECONDS,
        "contentType": content_type,
        "fileName": sanitized_filename,
        "fileSizeBytes": int(file_size),
        "issuedAt": now_iso,
        "userId": user_id,
    }

    return build_response(200, response_payload)
