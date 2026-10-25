"""
Unit tests for Milestone 5: list-documents and get-document Lambda handlers.
Uses Pytest and moto to mock DynamoDB and S3 services.
"""

import json
import os
import sys
import pytest
from pathlib import Path
import importlib.util
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Load list-documents handler
list_handler_path = Path(__file__).parent.parent / "functions" / "list-documents" / "handler.py"
spec_list = importlib.util.spec_from_file_location("list_documents_handler", str(list_handler_path))
list_module = importlib.util.module_from_spec(spec_list)
sys.modules["list_documents_handler"] = list_module
spec_list.loader.exec_module(list_module)
list_lambda_handler = list_module.lambda_handler

# Load get-document handler
get_handler_path = Path(__file__).parent.parent / "functions" / "get-document" / "handler.py"
spec_get = importlib.util.spec_from_file_location("get_document_handler", str(get_handler_path))
get_module = importlib.util.module_from_spec(spec_get)
sys.modules["get_document_handler"] = get_module
spec_get.loader.exec_module(get_module)
get_lambda_handler = get_module.lambda_handler


class TestListDocumentsHandler:
    @patch("list_documents_handler.get_dynamodb_table")
    def test_list_documents_success_with_metrics(self, mock_get_table):
        mock_table = MagicMock()
        mock_table.query.return_value = {
            "Items": [
                {
                    "documentId": "doc-001",
                    "userId": "user-123",
                    "fileName": "invoice1.pdf",
                    "status": "PENDING_REVIEW",
                    "createdAt": "2026-10-25T01:00:00Z",
                    "rawExtraction": {
                        "summaryFields": {
                            "vendorName": {"value": "Acme Cloud"},
                            "totalAmount": {"value": 150.00}
                        },
                        "metrics": {"averageConfidence": 95.0}
                    }
                },
                {
                    "documentId": "doc-002",
                    "userId": "user-123",
                    "fileName": "invoice2.pdf",
                    "status": "REVIEWED",
                    "createdAt": "2026-10-25T00:30:00Z",
                    "rawExtraction": {
                        "summaryFields": {
                            "vendorName": {"value": "Nexus Consulting"},
                            "totalAmount": {"value": 500.00}
                        },
                        "metrics": {"averageConfidence": 98.2}
                    }
                }
            ]
        }
        mock_get_table.return_value = mock_table

        event = {
            "httpMethod": "GET",
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user-123"}
                }
            }
        }
        res = list_lambda_handler(event)
        assert res["statusCode"] == 200

        body = json.loads(res["body"])
        assert len(body["items"]) == 2
        assert body["items"][0]["vendor"] == "Acme Cloud"
        assert body["items"][0]["totalAmount"] == 150.00

        # Verify metrics computation
        assert body["metrics"]["total"] == 2
        assert body["metrics"]["pendingReview"] == 1
        assert body["metrics"]["reviewed"] == 1
        assert body["metrics"]["processing"] == 0

    def test_options_cors_preflight(self):
        event = {"httpMethod": "OPTIONS"}
        res = list_lambda_handler(event)
        assert res["statusCode"] == 200


class TestGetDocumentHandler:
    @patch("boto3.resource")
    @patch("get_document_handler.get_s3_client")
    def test_get_document_success(self, mock_s3_client, mock_boto_resource):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "documentId": "doc-123",
                "userId": "user-abc",
                "fileName": "invoice_nexus.pdf",
                "s3Key": "uploads/doc-123/invoice_nexus.pdf",
                "status": "PENDING_REVIEW"
            }
        }
        mock_dynamo = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamo

        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://s3.ap-south-1.amazonaws.com/presigned-get-url"
        mock_s3_client.return_value = mock_s3

        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "doc-123"},
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user-abc"}
                }
            }
        }
        res = get_lambda_handler(event)
        assert res["statusCode"] == 200

        body = json.loads(res["body"])
        assert body["documentId"] == "doc-123"
        assert body["viewUrl"] == "https://s3.ap-south-1.amazonaws.com/presigned-get-url"

    @patch("boto3.resource")
    def test_get_document_multi_tenant_isolation(self, mock_boto_resource):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            "Item": {
                "documentId": "doc-456",
                "userId": "victim-user-id",
                "fileName": "secret_invoice.pdf"
            }
        }
        mock_dynamo = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamo

        event = {
            "httpMethod": "GET",
            "pathParameters": {"id": "doc-456"},
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "attacker-user-id"}
                }
            }
        }
        res = get_lambda_handler(event)
        assert res["statusCode"] == 403
        assert "Access denied" in json.loads(res["body"])["message"]
