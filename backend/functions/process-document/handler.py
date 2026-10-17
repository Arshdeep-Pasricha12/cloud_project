"""
Lambda Handler: process-document
Purpose: Triggered by S3 ObjectCreated event or API invocation to trigger Amazon Textract AnalyzeExpense,
         normalize extraction results, and persist initial records in DynamoDB.

Note: AWS Textract and DynamoDB integration scheduled for Milestone 4 & 5.
"""
import json
import os

def lambda_handler(event, context):
    """
    Processes uploaded documents:
    1. Reads S3 bucket and object key from event.
    2. Updates status to PROCESSING in DynamoDB.
    3. Invokes Amazon Textract AnalyzeExpense API.
    4. Parses and normalizes SummaryFields and LineItemGroups.
    5. Saves original extraction and metadata into DynamoDB.
    6. Updates document status to PENDING_REVIEW (or FAILED on error).
    """
    return {
        "statusCode": 501,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "process-document handler initialized. Textract AnalyzeExpense integration scheduled for Milestone 4.",
            "status": "NOT_IMPLEMENTED"
        })
    }
