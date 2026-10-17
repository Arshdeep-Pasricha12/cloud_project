"""
Lambda Handler: create-upload
Purpose: Generates a short-lived S3 presigned PUT URL for authenticated users to upload documents directly to S3.

Note: AWS integration pending - scheduled for Milestone 2 & 3.
"""
import json
import os
import uuid
from datetime import datetime

# Future imports once packages are wired:
# import boto3
# from shared.response_utils import build_response
# from shared.models import DocumentStatus, ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE_BYTES

def lambda_handler(event, context):
    """
    Handle POST /documents/upload-url requests.
    
    Expected Request Body (JSON):
    {
        "fileName": "invoice-2026-001.pdf",
        "contentType": "application/pdf"
    }
    
    Response:
    {
        "documentId": "<uuid>",
        "uploadUrl": "<presigned-s3-put-url>",
        "s3Key": "documents/<userId>/<uuid>/invoice-2026-001.pdf",
        "expiresInSeconds": 300
    }
    """
    return {
        "statusCode": 501,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "create-upload handler initialized. AWS S3 presigned URL integration scheduled for Milestone 2.",
            "status": "NOT_IMPLEMENTED"
        })
    }
