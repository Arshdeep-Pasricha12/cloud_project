"""
Unit tests for save-corrections Lambda handler.
Verifies immutability of rawExtraction and proper state transition to REVIEWED.
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

# Load save-corrections handler dynamically from hyphenated directory
handler_path = Path(__file__).parent.parent / "functions" / "save-corrections" / "handler.py"
spec = importlib.util.spec_from_file_location("save_corrections_handler", str(handler_path))
module = importlib.util.module_from_spec(spec)
sys.modules["save_corrections_handler"] = module
spec.loader.exec_module(module)
save_lambda_handler = module.lambda_handler


class TestSaveCorrectionsHandler:
    @patch("boto3.resource")
    def test_save_corrections_success(self, mock_boto):
        mock_table = MagicMock()
        # Mock get_item returning existing document with immutable rawExtraction
        original_raw = {
            "summaryFields": {
                "vendorName": {"value": "Acme Inc (Misread)"},
                "totalAmount": {"value": 100.0}
            }
        }
        mock_table.get_item.return_value = {
            "Item": {
                "documentId": "doc-777",
                "userId": "user-reviewer",
                "status": "PENDING_REVIEW",
                "rawExtraction": original_raw
            }
        }
        mock_table.update_item.return_value = {
            "Attributes": {
                "documentId": "doc-777",
                "status": "REVIEWED",
                "rawExtraction": original_raw,
                "correctedData": {
                    "vendorName": "Acme Industrial Supplies Inc.",
                    "totalAmount": 1250.00
                }
            }
        }
        mock_dynamo = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_boto.return_value = mock_dynamo

        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "doc-777"},
            "body": json.dumps({
                "corrections": {
                    "vendorName": "Acme Industrial Supplies Inc.",
                    "totalAmount": 1250.00,
                    "notes": "Fixed OCR vendor name misread"
                }
            }),
            "requestContext": {
                "authorizer": {
                    "claims": {"email": "reviewer@company.com"}
                }
            }
        }

        res = save_lambda_handler(event)
        assert res["statusCode"] == 200

        body = json.loads(res["body"])
        assert body["document"]["status"] == "REVIEWED"
        # Ensure rawExtraction was preserved
        assert body["document"]["rawExtraction"]["summaryFields"]["vendorName"]["value"] == "Acme Inc (Misread)"
        # Ensure correctedData was set
        assert body["document"]["correctedData"]["vendorName"] == "Acme Industrial Supplies Inc."

    @patch("boto3.resource")
    def test_save_corrections_not_found(self, mock_boto):
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # Item not found
        mock_dynamo = MagicMock()
        mock_dynamo.Table.return_value = mock_table
        mock_boto.return_value = mock_dynamo

        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "nonexistent-doc"},
            "body": json.dumps({"corrections": {"vendorName": "Test"}})
        }
        res = save_lambda_handler(event)
        assert res["statusCode"] == 404

    def test_missing_corrections_payload(self):
        event = {
            "httpMethod": "PUT",
            "pathParameters": {"id": "doc-123"},
            "body": json.dumps({})
        }
        res = save_lambda_handler(event)
        assert res["statusCode"] == 400

    def test_options_preflight(self):
        event = {"httpMethod": "OPTIONS"}
        res = save_lambda_handler(event)
        assert res["statusCode"] == 200
