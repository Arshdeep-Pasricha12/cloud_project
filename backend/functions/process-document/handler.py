"""
Lambda Handler: process-document
Purpose: Triggers Amazon Textract AnalyzeExpense on uploaded S3 invoices,
         normalizes extraction fields, computes confidence metrics, and prepares
         structured records for human review.

Trigger Sources:
1. S3 ObjectCreated Event Notification (Automatic on S3 PUT)
2. API Gateway REST Invocation: POST /documents/{id}/process
3. Direct programmatic invocation (testing & re-processing)
"""

import json
import logging
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

# Enable shared module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import boto3
from botocore.exceptions import ClientError

from shared.document_extractor import (
    extract_from_pdf_stream, 
    extract_from_image_fallback,
    extract_from_rekognition_detections
)
from shared.models import DocumentStatus
from shared.response_utils import build_response
from shared.textract_parser import normalize_textract_expense

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _to_dynamo_safe(val: Any) -> Any:
    """Recursively convert float values to Decimal for DynamoDB serialization."""
    if isinstance(val, float):
        return Decimal(str(val))
    if isinstance(val, dict):
        return {k: _to_dynamo_safe(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_to_dynamo_safe(v) for v in val]
    return val


def get_textract_client(region_name: str) -> boto3.client:
    """Initialize Textract client."""
    return boto3.client("textract", region_name=region_name)


def parse_event_source(event: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract (bucket, s3_key, document_id, user_id) from diverse event sources:
    - S3 Event Notification
    - API Gateway Proxy event
    - Direct invocation payload
    """
    # 1. S3 Event Notification format
    records = event.get("Records")
    if records and isinstance(records, list) and len(records) > 0:
        first_record = records[0]
        s3_info = first_record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        raw_key = s3_info.get("object", {}).get("key", "")
        key = urllib.parse.unquote_plus(raw_key)
        
        doc_id = None
        parts = key.split("/")
        if len(parts) >= 2 and parts[0] == "uploads":
            doc_id = parts[1]

        return bucket, key, doc_id, "s3-event-trigger"

    # 2. API Gateway Proxy Event format
    body = event.get("body")
    payload = {}
    if body:
        if isinstance(body, str):
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}
        elif isinstance(body, dict):
            payload = body

    user_id = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
        .get("sub", "dev-anonymous-user")
    )

    bucket = payload.get("bucket") or event.get("bucket") or os.environ.get("DOCUMENTS_BUCKET_NAME")
    key = payload.get("s3Key") or payload.get("key") or event.get("s3Key") or event.get("key")
    doc_id = payload.get("documentId") or event.get("documentId")

    if not doc_id and key:
        parts = key.split("/")
        if len(parts) >= 2 and parts[0] == "uploads":
            doc_id = parts[1]

    return bucket, key, doc_id, user_id


def process_invoice_document(bucket: str, key: str, region_name: str) -> Dict[str, Any]:
    """
    Calls Amazon Textract AnalyzeExpense and returns normalized JSON.
    Gracefully falls back to the intelligent document extractor if Textract service subscription
    or permissions are not enabled on the AWS account.
    """
    logger.info(f"Initiating Textract AnalyzeExpense for s3://{bucket}/{key} in {region_name}")
    try:
        textract_client = get_textract_client(region_name)
        response = textract_client.analyze_expense(
            Document={"S3Object": {"Bucket": bucket, "Name": key}}
        )
        return normalize_textract_expense(response)
    except Exception as err:
        logger.warning(f"Textract unavailable ({type(err).__name__}: {str(err)}). Engaging AWS Rekognition / Lambda fallback.")
        lower_key = key.lower()
        if lower_key.endswith(".pdf"):
            s3 = boto3.client("s3", region_name=region_name)
            obj = s3.get_object(Bucket=bucket, Key=key)
            body_bytes = obj["Body"].read()
            return extract_from_pdf_stream(body_bytes, filename=key)
        else:
            # Native AWS Rekognition OCR fallback for image documents and receipts
            try:
                rek = boto3.client("rekognition", region_name=region_name)
                rek_res = rek.detect_text(Image={"S3Object": {"Bucket": bucket, "Name": key}})
                return extract_from_rekognition_detections(rek_res.get("TextDetections", []), filename=key)
            except Exception as rek_err:
                logger.warning(f"Rekognition fallback failed ({type(rek_err).__name__}: {str(rek_err)}). Using heuristic fallback.")
                return extract_from_image_fallback(filename=key, s3_key=key)


def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Main Lambda entry point.
    """
    logger.info(f"Received process-document event: {json.dumps(event, default=str)[:300]}")

    region_name = os.environ.get("AWS_REGION") or "ap-south-1"
    bucket, key, doc_id, user_id = parse_event_source(event)

    if not bucket or not key:
        return build_response(
            400,
            {
                "error": "BadRequest",
                "message": "Missing 'bucket' or 's3Key' parameter to identify document in S3."
            }
        )

    # Perform AI extraction
    start_time = datetime.now(timezone.utc)
    try:
        extraction = process_invoice_document(bucket, key, region_name)
        status = DocumentStatus.PENDING_REVIEW.value
        error_details = None
    except Exception as exc:
        logger.error(f"Failed to process document s3://{bucket}/{key}: {str(exc)}")
        extraction = None
        status = DocumentStatus.FAILED.value
        error_details = str(exc)

    end_time = datetime.now(timezone.utc)
    duration_ms = round((end_time - start_time).total_seconds() * 1000)

    # Construct unified document record
    document_record = {
        "documentId": doc_id or "unknown",
        "userId": user_id,
        "bucket": bucket,
        "s3Key": key,
        "status": status,
        "extractedAt": end_time.isoformat(),
        "processingDurationMs": duration_ms,
        "rawExtraction": extraction,
        "error": error_details,
    }

    # DynamoDB persistence
    table_name = os.environ.get("DOCUMENTS_TABLE_NAME") or "doc-intelligence-documents"
    if table_name and doc_id:
        try:
            dynamodb = boto3.resource("dynamodb", region_name=region_name)
            table = dynamodb.Table(table_name)
            
            existing = {}
            try:
                res = table.get_item(Key={"documentId": doc_id})
                existing = res.get("Item") or {}
            except Exception as read_err:
                logger.warning(f"Could not read existing record for {doc_id}: {str(read_err)}")

            merged_record = dict(existing)
            merged_record.update({
                "documentId": doc_id,
                "status": status,
                "updatedAt": end_time.isoformat(),
                "processingDurationMs": duration_ms,
            })
            if extraction:
                merged_record["rawExtraction"] = extraction
                summary_fields = extraction.get("summaryFields") or {}
                if "vendorName" in summary_fields:
                    merged_record["vendor"] = summary_fields["vendorName"].get("value")
                if "invoiceNumber" in summary_fields:
                    merged_record["invoiceNumber"] = summary_fields["invoiceNumber"].get("value")
                if "invoiceDate" in summary_fields:
                    merged_record["invoiceDate"] = summary_fields["invoiceDate"].get("value")
                if "dueDate" in summary_fields:
                    merged_record["dueDate"] = summary_fields["dueDate"].get("value")
                if "totalAmount" in summary_fields:
                    merged_record["totalAmount"] = summary_fields["totalAmount"].get("value")
                if "currency" in summary_fields:
                    merged_record["currency"] = summary_fields["currency"].get("value")
                if "metrics" in extraction:
                    merged_record["confidence"] = extraction["metrics"].get("averageConfidence")

            if error_details:
                merged_record["errorMessage"] = error_details
            if "userId" not in merged_record or not merged_record["userId"]:
                merged_record["userId"] = user_id
            if "bucket" not in merged_record:
                merged_record["bucket"] = bucket
            if "s3Key" not in merged_record:
                merged_record["s3Key"] = key

            table.put_item(Item=_to_dynamo_safe(merged_record))
            logger.info(f"Persisted document record '{doc_id}' with status '{status}' to DynamoDB table '{table_name}'")
        except Exception as ddb_err:
            logger.warning(f"DynamoDB save skipped or failed: {str(ddb_err)}")

    if status == DocumentStatus.FAILED.value:
        return build_response(
            500,
            {
                "status": status,
                "documentId": doc_id,
                "error": error_details,
                "message": "Document AI extraction failed. See error details."
            }
        )

    return build_response(200, document_record)
