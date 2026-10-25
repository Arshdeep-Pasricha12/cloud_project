"""
Unit tests for create-upload Lambda handler and metadata validation.
Uses moto to mock AWS S3 services without requiring real credentials.
"""
import json
import os
import sys
import pytest

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import boto3
from moto import mock_aws

import importlib.util
from pathlib import Path

from shared.models import (
    sanitize_filename,
    validate_upload_metadata,
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE_BYTES,
)

# Load handler from hyphenated directory 'create-upload'
handler_path = Path(__file__).parent.parent / "functions" / "create-upload" / "handler.py"
spec = importlib.util.spec_from_file_location("create_upload_handler", str(handler_path))
create_upload_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(create_upload_module)
lambda_handler = create_upload_module.lambda_handler

TEST_BUCKET_NAME = "test-doc-intelligence-uploads"
TEST_REGION = "us-east-1"


@pytest.fixture(autouse=True)
def setup_env_and_s3():
    """Setup environment variables and mock S3 bucket for every test."""
    os.environ["DOCUMENTS_BUCKET_NAME"] = TEST_BUCKET_NAME
    os.environ["AWS_REGION"] = TEST_REGION
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = TEST_REGION

    with mock_aws():
        s3 = boto3.client("s3", region_name=TEST_REGION)
        s3.create_bucket(Bucket=TEST_BUCKET_NAME)
        yield s3


# ============================================================================
# Filename Sanitization & Metadata Validation Tests
# ============================================================================

def test_sanitize_filename_strips_traversal():
    """Verify path traversal characters are neutralized and double extensions are defanged."""
    assert sanitize_filename("../../../secret.pdf") == "secret.pdf"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.exe.png") == "calc_exe.png"
    assert sanitize_filename("/etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("normal-invoice-2026.pdf") == "normal-invoice-2026.pdf"


def test_sanitize_filename_handles_spaces_and_special_chars():
    """Verify spaces and special characters are cleaned."""
    cleaned = sanitize_filename("My Invoice #123 (Oct 2026).pdf")
    assert " " not in cleaned
    assert "#" not in cleaned
    assert "(" not in cleaned
    assert cleaned.endswith(".pdf")


def test_validate_upload_metadata_valid():
    """Verify valid invoice metadata passes validation."""
    valid, err, sanitized = validate_upload_metadata(
        file_name="vendor_receipt_001.pdf",
        content_type="application/pdf",
        file_size=1024 * 500  # 500 KB
    )
    assert valid is True
    assert err is None
    assert sanitized == "vendor_receipt_001.pdf"


def test_validate_upload_metadata_unsupported_mime():
    """Verify unsupported MIME types are rejected with clear error."""
    valid, err, _ = validate_upload_metadata(
        file_name="document.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_size=50000
    )
    assert valid is False
    assert "Unsupported MIME type" in err


def test_validate_upload_metadata_missing_filename():
    """Verify missing or empty filenames are rejected."""
    valid, err, _ = validate_upload_metadata("", "application/pdf", 1000)
    assert valid is False
    assert "fileName" in err

    valid, err, _ = validate_upload_metadata(None, "application/pdf", 1000)
    assert valid is False


def test_validate_upload_metadata_oversized():
    """Verify files larger than 10MB are rejected."""
    oversized = MAX_FILE_SIZE_BYTES + 1
    valid, err, _ = validate_upload_metadata("huge.pdf", "application/pdf", oversized)
    assert valid is False
    assert "exceeds maximum allowed size" in err


def test_validate_upload_metadata_zero_or_negative_size():
    """Verify 0-byte or negative size files are rejected."""
    valid, err, _ = validate_upload_metadata("empty.pdf", "application/pdf", 0)
    assert valid is False
    assert "greater than 0" in err

    valid, err, _ = validate_upload_metadata("neg.pdf", "application/pdf", -5)
    assert valid is False


# ============================================================================
# Lambda Handler Integration Tests (API Gateway Proxy Events)
# ============================================================================

def test_lambda_handler_success():
    """Verify successful presigned URL generation for valid document."""
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "fileName": "invoice-2026-acme.pdf",
            "contentType": "application/pdf",
            "fileSize": 150000
        }),
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "user-uuid-123"
                }
            }
        }
    }

    response = lambda_handler(event)
    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    body = json.loads(response["body"])
    assert "uploadUrl" in body
    assert "s3Key" in body
    assert body["s3Key"].startswith("uploads/")
    assert body["s3Key"].endswith("invoice-2026-acme.pdf")
    assert body["documentId"] is not None
    assert body["bucket"] == TEST_BUCKET_NAME
    assert body["expiresInSeconds"] == 300
    assert body["contentType"] == "application/pdf"
    assert body["userId"] == "user-uuid-123"

    # Verify presigned URL contains the target bucket and key
    assert TEST_BUCKET_NAME in body["uploadUrl"]
    assert "X-Amz-Signature" in body["uploadUrl"] or "AWSAccessKeyId" in body["uploadUrl"]


def test_lambda_handler_method_not_allowed():
    """Verify non-POST methods are rejected with HTTP 405."""
    event = {
        "httpMethod": "GET",
        "body": None
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 405
    body = json.loads(response["body"])
    assert body["error"] == "Method Not Allowed"


def test_lambda_handler_options_cors_preflight():
    """Verify OPTIONS preflight returns HTTP 200 with CORS headers."""
    event = {
        "httpMethod": "OPTIONS"
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in response["headers"]


def test_lambda_handler_invalid_json():
    """Verify malformed JSON body returns HTTP 400."""
    event = {
        "httpMethod": "POST",
        "body": "{invalid-json-content"
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "BadRequest"


def test_lambda_handler_missing_body():
    """Verify empty/missing request body returns HTTP 400."""
    event = {
        "httpMethod": "POST",
        "body": ""
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 400


def test_lambda_handler_validation_failure_unsupported_mime():
    """Verify unsupported MIME type via Lambda returns HTTP 400 with details."""
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "fileName": "test.exe",
            "contentType": "application/x-msdownload",
            "fileSize": 1024
        })
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "ValidationError"
    assert "Unsupported MIME type" in body["message"]


def test_lambda_handler_missing_bucket_configuration(monkeypatch):
    """Verify 500 returned safely when bucket name environment variable is missing."""
    monkeypatch.delenv("DOCUMENTS_BUCKET_NAME", raising=False)
    monkeypatch.delenv("DOCUMENT_BUCKET_NAME", raising=False)
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "fileName": "test.pdf",
            "contentType": "application/pdf",
            "fileSize": 1024
        })
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["error"] == "ConfigurationError"
