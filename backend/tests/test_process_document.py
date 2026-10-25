"""
Unit tests for process-document Lambda handler and Textract normalizer.
Uses Pytest with mocked Textract responses.
"""

import json
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from shared.textract_parser import (
    normalize_textract_expense,
    parse_summary_fields,
    parse_line_item_groups,
)
import importlib.util
from pathlib import Path

handler_path = Path(__file__).parent.parent / "functions" / "process-document" / "handler.py"
spec = importlib.util.spec_from_file_location("process_document_handler", str(handler_path))
process_doc_module = importlib.util.module_from_spec(spec)
sys.modules["process_document_handler"] = process_doc_module
spec.loader.exec_module(process_doc_module)

lambda_handler = process_doc_module.lambda_handler
parse_event_source = process_doc_module.parse_event_source


# Sample realistic Textract AnalyzeExpense payload
SAMPLE_TEXTRACT_EXPENSE = {
    "ExpenseDocuments": [
        {
            "ExpenseIndex": 1,
            "SummaryFields": [
                {
                    "Type": {"Text": "VENDOR_NAME"},
                    "ValueDetection": {"Text": "Acme Cloud Services", "Confidence": 98.7, "Geometry": {}}
                },
                {
                    "Type": {"Text": "INVOICE_RECEIPT_ID"},
                    "ValueDetection": {"Text": "INV-2026-0042", "Confidence": 95.2, "Geometry": {}}
                },
                {
                    "Type": {"Text": "INVOICE_RECEIPT_DATE"},
                    "ValueDetection": {"Text": "2026-10-15", "Confidence": 92.4, "Geometry": {}}
                },
                {
                    "Type": {"Text": "DUE_DATE"},
                    "ValueDetection": {"Text": "2026-11-15", "Confidence": 89.1, "Geometry": {}}
                },
                {
                    "Type": {"Text": "SUBTOTAL"},
                    "ValueDetection": {"Text": "$1,250.00", "Confidence": 94.0, "Geometry": {}}
                },
                {
                    "Type": {"Text": "TAX"},
                    "ValueDetection": {"Text": "$125.00", "Confidence": 78.5, "Geometry": {}}  # Low confidence
                },
                {
                    "Type": {"Text": "TOTAL"},
                    "ValueDetection": {"Text": "$1,375.00", "Confidence": 99.1, "Geometry": {}}
                },
                {
                    "Type": {"Text": "CURRENCY"},
                    "ValueDetection": {"Text": "USD", "Confidence": 96.0, "Geometry": {}}
                }
            ],
            "LineItemGroups": [
                {
                    "LineItemGroupIndex": 1,
                    "LineItems": [
                        {
                            "LineItemExpenseFields": [
                                {
                                    "Type": {"Text": "ITEM"},
                                    "ValueDetection": {"Text": "Cloud Compute Virtual Instances", "Confidence": 93.5}
                                },
                                {
                                    "Type": {"Text": "QUANTITY"},
                                    "ValueDetection": {"Text": "5", "Confidence": 97.0}
                                },
                                {
                                    "Type": {"Text": "UNIT_PRICE"},
                                    "ValueDetection": {"Text": "$200.00", "Confidence": 92.0}
                                },
                                {
                                    "Type": {"Text": "PRICE"},
                                    "ValueDetection": {"Text": "$1,000.00", "Confidence": 95.0}
                                }
                            ]
                        },
                        {
                            "LineItemExpenseFields": [
                                {
                                    "Type": {"Text": "ITEM"},
                                    "ValueDetection": {"Text": "Managed Object Storage (TB)", "Confidence": 91.0}
                                },
                                {
                                    "Type": {"Text": "QUANTITY"},
                                    "ValueDetection": {"Text": "10", "Confidence": 96.0}
                                },
                                {
                                    "Type": {"Text": "UNIT_PRICE"},
                                    "ValueDetection": {"Text": "$25.00", "Confidence": 88.0}
                                },
                                {
                                    "Type": {"Text": "PRICE"},
                                    "ValueDetection": {"Text": "$250.00", "Confidence": 94.0}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}


class TestTextractParser:
    def test_parse_summary_fields(self):
        summary_raw = SAMPLE_TEXTRACT_EXPENSE["ExpenseDocuments"][0]["SummaryFields"]
        parsed = parse_summary_fields(summary_raw)

        assert parsed["vendorName"]["value"] == "Acme Cloud Services"
        assert parsed["vendorName"]["confidence"] == 98.7
        assert parsed["invoiceNumber"]["value"] == "INV-2026-0042"
        assert parsed["totalAmount"]["value"] == 1375.00
        assert parsed["subtotal"]["value"] == 1250.00
        assert parsed["taxAmount"]["value"] == 125.00
        assert parsed["currency"]["value"] == "USD"

    def test_parse_line_item_groups(self):
        groups_raw = SAMPLE_TEXTRACT_EXPENSE["ExpenseDocuments"][0]["LineItemGroups"]
        items = parse_line_item_groups(groups_raw)

        assert len(items) == 2
        assert items[0]["description"] == "Cloud Compute Virtual Instances"
        assert items[0]["quantity"] == 5
        assert items[0]["unitPrice"] == 200.00
        assert items[0]["totalPrice"] == 1000.00

        assert items[1]["description"] == "Managed Object Storage (TB)"
        assert items[1]["quantity"] == 10
        assert items[1]["unitPrice"] == 25.00
        assert items[1]["totalPrice"] == 250.00

    def test_normalize_textract_expense_metrics(self):
        result = normalize_textract_expense(SAMPLE_TEXTRACT_EXPENSE)
        metrics = result["metrics"]

        assert metrics["totalFieldsDetected"] == 10  # 8 summary + 2 line items
        assert metrics["averageConfidence"] > 90.0
        # Tax field had 78.5% confidence (< 80%), so lowConfidenceFieldCount should be 1
        assert metrics["lowConfidenceFieldCount"] == 1

    def test_empty_expense_documents(self):
        result = normalize_textract_expense({"ExpenseDocuments": []})
        assert result["summaryFields"] == {}
        assert result["lineItems"] == []
        assert result["metrics"]["totalFieldsDetected"] == 0


class TestProcessDocumentHandler:
    def test_parse_event_from_s3_notification(self):
        s3_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-doc-bucket"},
                        "object": {"key": "uploads%2Fdoc-12345%2Finvoice%2Bsample.pdf"}
                    }
                }
            ]
        }
        bucket, key, doc_id, user_id = parse_event_source(s3_event)
        assert bucket == "test-doc-bucket"
        assert key == "uploads/doc-12345/invoice+sample.pdf"
        assert doc_id == "doc-12345"

    def test_parse_event_from_api_gateway_proxy(self):
        apigw_event = {
            "body": json.dumps({
                "bucket": "test-doc-bucket",
                "s3Key": "uploads/doc-999/invoice.pdf",
                "documentId": "doc-999"
            }),
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user-cognito-uuid"}
                }
            }
        }
        bucket, key, doc_id, user_id = parse_event_source(apigw_event)
        assert bucket == "test-doc-bucket"
        assert key == "uploads/doc-999/invoice.pdf"
        assert doc_id == "doc-999"
        assert user_id == "user-cognito-uuid"

    @patch("process_document_handler.get_textract_client")
    def test_lambda_handler_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.analyze_expense.return_value = SAMPLE_TEXTRACT_EXPENSE
        mock_get_client.return_value = mock_client

        event = {
            "bucket": "test-doc-bucket",
            "s3Key": "uploads/doc-123/invoice_acme.pdf",
            "documentId": "doc-123"
        }
        response = lambda_handler(event)
        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["status"] == "PENDING_REVIEW"
        assert body["documentId"] == "doc-123"
        assert body["rawExtraction"]["summaryFields"]["vendorName"]["value"] == "Acme Cloud Services"
        assert body["rawExtraction"]["metrics"]["totalFieldsDetected"] == 10

    def test_lambda_handler_missing_bucket_key(self):
        event = {}
        response = lambda_handler(event)
        assert response["statusCode"] == 400
