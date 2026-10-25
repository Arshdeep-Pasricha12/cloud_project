"""
Lambda Handler: save-corrections
Purpose: Saves user-reviewed and corrected invoice data into DynamoDB.

Data Governance & Immutability Rules:
1. rawExtraction is strictly IMMUTABLE: Never overwritten, ensuring original AI output is preserved for audit trails.
2. User edits are recorded in a separate 'correctedData' attribute.
3. Reviewer identity (Cognito sub/email) and timestamp are stamped.
4. Document status transitions to 'REVIEWED'.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

# Enable shared module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import boto3
from botocore.exceptions import ClientError

from shared.models import DocumentStatus
from shared.response_utils import build_response, DecimalEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_user_identity(event: Dict[str, Any]) -> str:
    """Extract authenticated user sub/email from Cognito Authorizer claims."""
    try:
        claims = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("claims", {})
        )
        return claims.get("email") or claims.get("sub") or "dev-anonymous-user"
    except Exception:
        return "dev-anonymous-user"


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Safely parse JSON request body."""
    body = event.get("body")
    if not body:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except Exception as e:
        raise ValueError(f"Invalid JSON request body: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Handle PUT /documents/{id}/corrections requests.
    """
    http_method = event.get("httpMethod", "PUT")
    if http_method.upper() == "OPTIONS":
        return build_response(200, {"message": "CORS preflight OK"})

    table_name = os.environ.get("DOCUMENTS_TABLE_NAME", "doc-intelligence-documents")
    region_name = os.environ.get("AWS_REGION", "ap-south-1")

    # 1. Path parameter: documentId
    path_params = event.get("pathParameters") or {}
    document_id = path_params.get("id") or event.get("documentId")

    if not document_id:
        return build_response(400, {"error": "BadRequest", "message": "Missing 'id' path parameter."})

    # 2. Parse corrections payload
    try:
        payload = parse_body(event)
    except ValueError as val_err:
        return build_response(400, {"error": "BadRequest", "message": str(val_err)})

    corrections = payload.get("corrections")
    if not corrections or not isinstance(corrections, dict):
        return build_response(
            400,
            {
                "error": "BadRequest",
                "message": "Missing or invalid 'corrections' object in request body."
            }
        )

    reviewer = extract_user_identity(event)
    now_iso = datetime.now(timezone.utc).isoformat()

    logger.info(f"Saving corrections for document '{document_id}' by reviewer '{reviewer}'")

    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    table = dynamodb.Table(table_name)

    # 3. Verify document exists and retrieve existing record
    try:
        res = table.get_item(Key={"documentId": document_id})
        existing_item = res.get("Item")
    except ClientError as err:
        logger.error(f"DynamoDB GetItem error: {str(err)}")
        return build_response(
            500,
            {"error": "DatabaseError", "message": f"Failed to check document: {err.response.get('Error', {}).get('Message')}"}
        )

    if not existing_item:
        return build_response(404, {"error": "NotFound", "message": f"Document '{document_id}' not found."})

    # Multi-tenant security check: ensure user owns the document (allow dev fallback if dev mode)
    doc_owner = existing_item.get("userId")
    user_sub = None
    try:
        user_sub = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
    except Exception:
        pass

    if doc_owner and user_sub and doc_owner != "dev-anonymous-user" and user_sub != "dev-anonymous-user":
        if doc_owner != user_sub:
            logger.warning(f"Forbidden edit: User '{user_sub}' attempted to modify document belonging to '{doc_owner}'")
            return build_response(403, {"error": "Forbidden", "message": "Access denied to modify this document."})

    # Convert float numbers in corrections to Decimal for DynamoDB compatibility
    def _to_dynamo_safe(val):
        if isinstance(val, float):
            return Decimal(str(val))
        if isinstance(val, dict):
            return {k: _to_dynamo_safe(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_to_dynamo_safe(v) for v in val]
        return val

    safe_corrections = _to_dynamo_safe(corrections)
    safe_corrections["reviewer"] = reviewer
    safe_corrections["reviewedAt"] = now_iso

    # 4. Update DynamoDB item:
    # - Updates 'correctedData'
    # - Updates 'status' to REVIEWED
    # - Updates 'updatedAt'
    # - Leaves 'rawExtraction' completely untouched!
    try:
        update_res = table.update_item(
            Key={"documentId": document_id},
            UpdateExpression="SET #status = :s, #correctedData = :cd, #updatedAt = :ua, #reviewedAt = :ra",
            ExpressionAttributeNames={
                "#status": "status",
                "#correctedData": "correctedData",
                "#updatedAt": "updatedAt",
                "#reviewedAt": "reviewedAt"
            },
            ExpressionAttributeValues={
                ":s": DocumentStatus.REVIEWED.value,
                ":cd": safe_corrections,
                ":ua": now_iso,
                ":ra": now_iso
            },
            ReturnValues="ALL_NEW"
        )
        updated_item = update_res.get("Attributes", {})
    except ClientError as err:
        logger.error(f"DynamoDB UpdateItem error: {str(err)}")
        return build_response(
            500,
            {"error": "DatabaseError", "message": f"Failed to persist corrections: {err.response.get('Error', {}).get('Message')}"}
        )

    return build_response(
        200,
        {
            "message": "Corrections successfully saved. Status updated to REVIEWED.",
            "document": updated_item
        }
    )
