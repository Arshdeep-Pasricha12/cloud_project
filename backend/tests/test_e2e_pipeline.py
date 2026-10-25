"""
End-to-End Integration Test Suite for Serverless Document Intelligence Platform (Milestone 7).
Tests the entire multi-service lifecycle with moto (S3, DynamoDB) and mock Textract:
1. create-upload: Pre-signed S3 URL generation & initial DynamoDB record (UPLOADED)
2. S3 direct object storage
3. process-document: Textract AI extraction & status update (PENDING_REVIEW)
4. list-documents: Multi-tenant GSI query & aggregated metrics counters
5. get-document: Document retrieval with pre-signed view URL
6. save-corrections: Human-in-the-loop review, correctedData persistence & rawExtraction immutability
7. Multi-tenant security isolation enforcement
8. Processing failure handling & FAILED status transition
"""

import json
import os
import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock
import boto3
import pytest
from moto import mock_aws

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Helper to dynamically import lambda handlers
def load_handler(function_name: str, module_name: str):
    handler_path = Path(backend_root) / "functions" / function_name / "handler.py"
    spec = importlib.util.spec_from_file_location(module_name, str(handler_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod.lambda_handler

create_upload_handler = load_handler("create-upload", "e2e_create_upload")
process_document_handler = load_handler("process-document", "e2e_process_document")
list_documents_handler = load_handler("list-documents", "e2e_list_documents")
get_document_handler = load_handler("get-document", "e2e_get_document")
save_corrections_handler = load_handler("save-corrections", "e2e_save_corrections")

TEST_REGION = "ap-south-1"
TEST_BUCKET = "doc-intelligence-uploads-399383129700"
TEST_TABLE = "doc-intelligence-documents"


@pytest.fixture
def aws_env(monkeypatch):
    """Configure environment variables for tests."""
    monkeypatch.setenv("AWS_REGION", TEST_REGION)
    monkeypatch.setenv("AWS_DEFAULT_REGION", TEST_REGION)
    monkeypatch.setenv("DOCUMENTS_BUCKET_NAME", TEST_BUCKET)
    monkeypatch.setenv("DOCUMENTS_TABLE_NAME", TEST_TABLE)
    monkeypatch.setenv("URL_EXPIRATION_SECONDS", "300")


@pytest.fixture
def mock_infrastructure(aws_env):
    """Set up mock S3 bucket and DynamoDB table with GSI."""
    with mock_aws():
        # Setup S3
        s3 = boto3.client("s3", region_name=TEST_REGION)
        s3.create_bucket(
            Bucket=TEST_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": TEST_REGION}
        )

        # Setup DynamoDB with GSI
        dynamodb = boto3.client("dynamodb", region_name=TEST_REGION)
        dynamodb.create_table(
            TableName=TEST_TABLE,
            KeySchema=[
                {"AttributeName": "documentId", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "documentId", "AttributeType": "S"},
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "S"}
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
        yield {"s3": s3, "dynamodb": dynamodb}


MOCK_EXPENSE_RESPONSE = {
    "ExpenseDocuments": [
        {
            "SummaryFields": [
                {
                    "Type": {"Text": "VENDOR_NAME", "Confidence": 98.5},
                    "ValueDetection": {"Text": "TechCorp Cloud Solutions", "Confidence": 98.5}
                },
                {
                    "Type": {"Text": "INVOICE_RECEIPT_ID", "Confidence": 99.1},
                    "ValueDetection": {"Text": "INV-2026-9042", "Confidence": 99.1}
                },
                {
                    "Type": {"Text": "INVOICE_RECEIPT_DATE", "Confidence": 95.0},
                    "ValueDetection": {"Text": "2026-10-20", "Confidence": 95.0}
                },
                {
                    "Type": {"Text": "TOTAL", "Confidence": 99.4},
                    "ValueDetection": {"Text": "4250.00", "Confidence": 99.4}
                },
                {
                    "Type": {"Text": "SUBTOTAL", "Confidence": 96.0},
                    "ValueDetection": {"Text": "3800.00", "Confidence": 96.0}
                },
                {
                    "Type": {"Text": "TAX", "Confidence": 94.0},
                    "ValueDetection": {"Text": "450.00", "Confidence": 94.0}
                }
            ],
            "LineItemGroups": [
                {
                    "LineItems": [
                        {
                            "LineItemExpenseFields": [
                                {
                                    "Type": {"Text": "ITEM", "Confidence": 97.0},
                                    "ValueDetection": {"Text": "Cloud Architecture Consulting", "Confidence": 97.0}
                                },
                                {
                                    "Type": {"Text": "PRICE", "Confidence": 98.0},
                                    "ValueDetection": {"Text": "3000.00", "Confidence": 98.0}
                                }
                            ]
                        },
                        {
                            "LineItemExpenseFields": [
                                {
                                    "Type": {"Text": "ITEM", "Confidence": 96.0},
                                    "ValueDetection": {"Text": "Serverless Security Review", "Confidence": 96.0}
                                },
                                {
                                    "Type": {"Text": "PRICE", "Confidence": 97.0},
                                    "ValueDetection": {"Text": "1250.00", "Confidence": 97.0}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}


class TestEndToEndPipeline:
    """Complete multi-service integration tests."""

    def test_full_document_lifecycle(self, mock_infrastructure):
        """
        Executes the entire end-to-end lifecycle:
        Upload URL -> S3 Upload -> Textract Processing -> Listing -> Detail View -> Review Corrections
        """
        s3 = mock_infrastructure["s3"]
        dynamodb_resource = boto3.resource("dynamodb", region_name=TEST_REGION)
        table = dynamodb_resource.Table(TEST_TABLE)

        user_id = "user_arshdeep_7153bdda"
        user_email = "arshdeepforwork@gmail.com"

        # -------------------------------------------------------------
        # STEP 1: Request Presigned Upload URL (create-upload)
        # -------------------------------------------------------------
        upload_event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "fileName": "techcorp_invoice.pdf",
                "contentType": "application/pdf",
                "fileSize": 25600
            }),
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": user_id,
                        "email": user_email
                    }
                }
            }
        }

        create_res = create_upload_handler(upload_event, {})
        assert create_res["statusCode"] == 200
        upload_data = json.loads(create_res["body"])
        assert "uploadUrl" in upload_data
        assert "documentId" in upload_data
        assert "s3Key" in upload_data
        
        doc_id = upload_data["documentId"]
        s3_key = upload_data["s3Key"]
        assert s3_key.startswith("uploads/")
        assert s3_key.endswith("techcorp_invoice.pdf")

        # Verify DynamoDB record was created with UPLOADED status
        item = table.get_item(Key={"documentId": doc_id}).get("Item")
        assert item is not None
        assert item["status"] == "UPLOADED"
        assert item["userId"] == user_id
        assert item["fileName"] == "techcorp_invoice.pdf"

        # -------------------------------------------------------------
        # STEP 2: S3 Direct Upload Simulation
        # -------------------------------------------------------------
        pdf_bytes = b"%PDF-1.4 Mock Invoice Payload for TechCorp"
        s3.put_object(
            Bucket=TEST_BUCKET,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf"
        )

        # -------------------------------------------------------------
        # STEP 3: Event-Driven Processing (process-document via S3 event)
        # -------------------------------------------------------------
        s3_notification_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": TEST_BUCKET},
                        "object": {"key": s3_key}
                    }
                }
            ]
        }

        mock_textract = MagicMock()
        mock_textract.analyze_expense.return_value = MOCK_EXPENSE_RESPONSE

        with patch("e2e_process_document.get_textract_client", return_value=mock_textract):
            process_res = process_document_handler(s3_notification_event, {})

        assert process_res["statusCode"] == 200
        process_data = json.loads(process_res["body"])
        assert process_data["status"] == "PENDING_REVIEW"
        assert process_data["documentId"] == doc_id
        assert "rawExtraction" in process_data

        # Verify DynamoDB item updated to PENDING_REVIEW with extracted data
        updated_item = table.get_item(Key={"documentId": doc_id})["Item"]
        assert updated_item["status"] == "PENDING_REVIEW"
        assert updated_item["rawExtraction"]["summaryFields"]["vendorName"]["value"] == "TechCorp Cloud Solutions"
        assert float(updated_item["rawExtraction"]["summaryFields"]["totalAmount"]["value"]) == 4250.00
        assert len(updated_item["rawExtraction"]["lineItems"]) == 2

        # -------------------------------------------------------------
        # STEP 4: List Documents & Aggregated Metrics (list-documents)
        # -------------------------------------------------------------
        list_event = {
            "httpMethod": "GET",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": user_id,
                        "email": user_email
                    }
                }
            }
        }

        list_res = list_documents_handler(list_event, {})
        assert list_res["statusCode"] == 200
        list_data = json.loads(list_res["body"])
        assert "items" in list_data
        assert "metrics" in list_data
        assert len(list_data["items"]) == 1
        assert list_data["items"][0]["documentId"] == doc_id
        assert list_data["items"][0]["status"] == "PENDING_REVIEW"
        assert list_data["metrics"]["total"] == 1
        assert list_data["metrics"]["pendingReview"] == 1
        assert list_data["metrics"]["reviewed"] == 0
        assert list_data["metrics"]["failed"] == 0

        # -------------------------------------------------------------
        # STEP 5: Get Document Details with Presigned View URL (get-document)
        # -------------------------------------------------------------
        get_event = {
            "httpMethod": "GET",
            "pathParameters": {"id": doc_id},
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": user_id,
                        "email": user_email
                    }
                }
            }
        }

        get_res = get_document_handler(get_event, {})
        assert get_res["statusCode"] == 200
        get_data = json.loads(get_res["body"])
        assert get_data["documentId"] == doc_id
        assert "viewUrl" in get_data
        assert get_data["rawExtraction"]["summaryFields"]["vendorName"]["value"] == "TechCorp Cloud Solutions"

        # -------------------------------------------------------------
        # STEP 6: Save Human-in-the-Loop Corrections (save-corrections)
        # -------------------------------------------------------------
        corrections_payload = {
            "corrections": {
                "vendorName": "TechCorp Global Solutions Pvt Ltd",  # Corrected name
                "invoiceId": "INV-2026-9042",
                "invoiceDate": "2026-10-20",
                "totalAmount": 4250.00,
                "lineItems": [
                    {
                        "description": "Cloud Architecture Consulting (Senior AWS Architect)",
                        "price": 3000.00
                    },
                    {
                        "description": "Serverless Security Review & CloudWatch Observability",
                        "price": 1250.00
                    }
                ],
                "notes": "Verified invoice against PO #4421. Corrected legal entity name."
            }
        }

        corrections_event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": doc_id},
            "body": json.dumps(corrections_payload),
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": user_id,
                        "email": user_email
                    }
                }
            }
        }

        save_res = save_corrections_handler(corrections_event, {})
        assert save_res["statusCode"] == 200
        save_data = json.loads(save_res["body"])
        assert "document" in save_data
        assert save_data["document"]["status"] == "REVIEWED"
        assert save_data["document"]["documentId"] == doc_id

        # Verify DynamoDB Immutability & Updated Values
        final_item = table.get_item(Key={"documentId": doc_id})["Item"]
        assert final_item["status"] == "REVIEWED"
        assert "reviewedAt" in final_item
        
        # Verify RAW extraction was preserved exactly as originally analyzed (Immutability guarantee)
        assert final_item["rawExtraction"]["summaryFields"]["vendorName"]["value"] == "TechCorp Cloud Solutions"
        
        # Verify CORRECTED data contains reviewer's manual edits
        assert final_item["correctedData"]["vendorName"] == "TechCorp Global Solutions Pvt Ltd"

        # -------------------------------------------------------------
        # STEP 7: Re-fetch List Documents to Verify Metrics Transition
        # -------------------------------------------------------------
        list_res_after = list_documents_handler(list_event, {})
        list_after_data = json.loads(list_res_after["body"])
        assert list_after_data["metrics"]["total"] == 1
        assert list_after_data["metrics"]["pendingReview"] == 0
        assert list_after_data["metrics"]["reviewed"] == 1
        assert list_after_data["metrics"]["failed"] == 0

    def test_multitenant_isolation(self, mock_infrastructure):
        """
        Verifies that User B cannot view or modify User A's uploaded documents.
        """
        dynamodb_resource = boto3.resource("dynamodb", region_name=TEST_REGION)
        table = dynamodb_resource.Table(TEST_TABLE)

        # Pre-seed User A document
        doc_id = "doc_user_a_private_001"
        table.put_item(
            Item={
                "documentId": doc_id,
                "userId": "user_a_owner",
                "fileName": "confidential_payroll.pdf",
                "s3Key": "uploads/user_a/confidential_payroll.pdf",
                "status": "PENDING_REVIEW",
                "createdAt": "2026-10-25T01:00:00Z",
                "rawExtraction": {"summaryFields": {"vendorName": {"value": "Payroll Services"}}}
            }
        )

        # User B attempts to access User A's document via get-document
        user_b_get_event = {
            "httpMethod": "GET",
            "pathParameters": {"id": doc_id},
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user_b_attacker",
                        "email": "attacker@otherdomain.com"
                    }
                }
            }
        }

        get_res = get_document_handler(user_b_get_event, {})
        assert get_res["statusCode"] == 403
        assert "access denied" in json.loads(get_res["body"])["message"].lower()

        # User B attempts to save corrections to User A's document
        user_b_save_event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": doc_id},
            "body": json.dumps({"corrections": {"fraud": True}}),
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user_b_attacker",
                        "email": "attacker@otherdomain.com"
                    }
                }
            }
        }

        save_res = save_corrections_handler(user_b_save_event, {})
        assert save_res["statusCode"] == 403
        assert "access denied" in json.loads(save_res["body"])["message"].lower()

        # User B lists their documents -> should see 0 documents
        user_b_list_event = {
            "httpMethod": "GET",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user_b_attacker",
                        "email": "attacker@otherdomain.com"
                    }
                }
            }
        }

        list_res = list_documents_handler(user_b_list_event, {})
        assert list_res["statusCode"] == 200
        list_data = json.loads(list_res["body"])
        assert "items" in list_data
        assert len(list_data["items"]) == 0
        assert list_data["metrics"]["total"] == 0

    def test_processing_failure_resilience(self, mock_infrastructure):
        """
        Verifies that unreadable/corrupted files or Textract service errors
        gracefully transition document state to FAILED without crashing.
        """
        dynamodb_resource = boto3.resource("dynamodb", region_name=TEST_REGION)
        table = dynamodb_resource.Table(TEST_TABLE)
        s3 = mock_infrastructure["s3"]

        doc_id = "doc_corrupted_file_001"
        s3_key = f"uploads/{doc_id}/corrupted.pdf"

        # Pre-seed record
        table.put_item(
            Item={
                "documentId": doc_id,
                "userId": "user_tester",
                "fileName": "corrupted.pdf",
                "s3Key": s3_key,
                "status": "UPLOADED",
                "createdAt": "2026-10-25T01:00:00Z"
            }
        )

        s3.put_object(Bucket=TEST_BUCKET, Key=s3_key, Body=b"not a valid pdf")

        # Mock Textract throwing an exception (e.g. UnsupportedDocumentException)
        mock_textract = MagicMock()
        mock_textract.analyze_expense.side_effect = Exception("UnsupportedDocumentException: The document cannot be analyzed.")

        s3_notification_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": TEST_BUCKET},
                        "object": {"key": s3_key}
                    }
                }
            ]
        }

        with patch("e2e_process_document.get_textract_client", return_value=mock_textract):
            res = process_document_handler(s3_notification_event, {})

        # Should handle gracefully with 500 status and record failure in DB
        assert res["statusCode"] == 500
        
        # Verify DynamoDB record has FAILED status
        item = table.get_item(Key={"documentId": doc_id})["Item"]
        assert item["status"] == "FAILED"
        assert "errorMessage" in item

