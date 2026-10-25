"""
Lambda Handler: list-documents
Purpose: Retrieves all documents belonging to the authenticated user from DynamoDB,
         ordered by creation date (newest first), and computes real-time status summary metrics.
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
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from shared.models import DocumentStatus
from shared.response_utils import build_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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


def get_dynamodb_table(region_name: str, table_name: str):
    """Initialize DynamoDB table resource."""
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    return dynamodb.Table(table_name)


def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Handle GET /documents requests.
    Queries the UserDocumentsIndex GSI on DynamoDB for all records matching the user's ID.
    """
    http_method = event.get("httpMethod", "GET")
    if http_method.upper() == "OPTIONS":
        return build_response(200, {"message": "CORS preflight OK"})

    table_name = os.environ.get("DOCUMENTS_TABLE_NAME", "doc-intelligence-documents")
    region_name = os.environ.get("AWS_REGION", "ap-south-1")
    user_id = extract_user_id(event)

    logger.info(f"Listing documents for user: {user_id}")

    try:
        table = get_dynamodb_table(region_name, table_name)
        # Query GSI: UserDocumentsIndex (partition key: userId, sort key: createdAt)
        response = table.query(
            IndexName="UserDocumentsIndex",
            KeyConditionExpression=Key("userId").eq(user_id),
            ScanIndexForward=False,  # Descending order (newest first)
            Limit=50
        )
        items = response.get("Items", [])
    except ClientError as err:
        logger.error(f"DynamoDB Query error: {str(err)}")
        return build_response(
            500,
            {
                "error": "DatabaseError",
                "message": f"Failed to retrieve documents: {err.response.get('Error', {}).get('Message')}"
            }
        )
    except Exception as err:
        logger.error(f"Unexpected error listing documents: {str(err)}")
        return build_response(
            500,
            {
                "error": "InternalServerError",
                "message": "An unexpected error occurred while listing documents."
            }
        )

    # Compute status metrics dynamically
    metrics = {
        "total": len(items),
        "processing": 0,
        "pendingReview": 0,
        "reviewed": 0,
        "failed": 0
    }

    formatted_items = []
    for item in items:
        status = item.get("status", DocumentStatus.UPLOADED.value)
        if status in (DocumentStatus.PROCESSING.value, DocumentStatus.UPLOADED.value):
            metrics["processing"] += 1
        elif status == DocumentStatus.PENDING_REVIEW.value:
            metrics["pendingReview"] += 1
        elif status == DocumentStatus.REVIEWED.value:
            metrics["reviewed"] += 1
        elif status == DocumentStatus.FAILED.value:
            metrics["failed"] += 1

        # Extract summary vendor, invoice number, date, amount, currency if available
        raw_ext = item.get("rawExtraction") or {}
        summary_fields = raw_ext.get("summaryFields") or {}
        vendor = (
            summary_fields.get("vendorName", {}).get("value")
            or item.get("vendor")
            or ("Processing..." if status in (DocumentStatus.PROCESSING.value, DocumentStatus.UPLOADED.value) else "—")
        )
        total_amount = summary_fields.get("totalAmount", {}).get("value") or item.get("totalAmount")
        invoice_number = (
            summary_fields.get("invoiceNumber", {}).get("value")
            or item.get("invoiceNumber")
            or "—"
        )
        invoice_date = summary_fields.get("invoiceDate", {}).get("value") or item.get("invoiceDate")
        due_date = summary_fields.get("dueDate", {}).get("value") or item.get("dueDate")
        currency = summary_fields.get("currency", {}).get("value") or item.get("currency") or "USD"
        confidence = (
            raw_ext.get("metrics", {}).get("averageConfidence")
            or item.get("confidence")
        )

        formatted_items.append({
            "documentId": item.get("documentId"),
            "userId": item.get("userId"),
            "fileName": item.get("fileName", "invoice.pdf"),
            "fileSizeBytes": item.get("fileSizeBytes", 0),
            "status": status,
            "createdAt": item.get("createdAt"),
            "updatedAt": item.get("updatedAt"),
            "vendor": vendor,
            "totalAmount": total_amount,
            "invoiceNumber": invoice_number,
            "invoiceDate": invoice_date,
            "dueDate": due_date,
            "currency": currency,
            "confidence": confidence,
            "s3Key": item.get("s3Key"),
            "rawExtraction": raw_ext
        })

    return build_response(200, {
        "items": formatted_items,
        "metrics": metrics
    })
