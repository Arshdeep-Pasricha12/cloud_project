"""
Lambda Handler: get-document
Purpose: Retrieves single document details from DynamoDB by documentId, including processing status,
         original Textract extraction, user-corrected values, and a temporary presigned GET URL for viewing.

Note: AWS DynamoDB and S3 integration scheduled for Milestone 5.
"""
import json

def lambda_handler(event, context):
    """
    Handle GET /documents/{id} requests.
    
    Path Parameters:
        id: documentId (UUID)
        
    Response Body:
    {
        "documentId": "<uuid>",
        "userId": "<cognito-sub>",
        "fileName": "invoice.pdf",
        "status": "PENDING_REVIEW",
        "createdAt": "2026-10-17T12:00:00Z",
        "updatedAt": "2026-10-17T12:01:00Z",
        "viewUrl": "<presigned-s3-get-url>",
        "rawExtraction": { ... },
        "correctedData": { ... }
    }
    """
    return {
        "statusCode": 501,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "get-document handler initialized. DynamoDB retrieval scheduled for Milestone 5.",
            "status": "NOT_IMPLEMENTED"
        })
    }
