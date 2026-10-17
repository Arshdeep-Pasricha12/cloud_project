"""
Unit test placeholders validating shared models and response formatting.
"""
import json
from shared.models import DocumentStatus, ALLOWED_CONTENT_TYPES
from shared.response_utils import build_response

def test_document_statuses_defined():
    """Verify all required lifecycle states are properly defined."""
    assert DocumentStatus.UPLOADED == "UPLOADED"
    assert DocumentStatus.PROCESSING == "PROCESSING"
    assert DocumentStatus.PENDING_REVIEW == "PENDING_REVIEW"
    assert DocumentStatus.REVIEWED == "REVIEWED"
    assert DocumentStatus.FAILED == "FAILED"

def test_allowed_content_types():
    """Verify accepted document formats for invoice ingestion."""
    assert "application/pdf" in ALLOWED_CONTENT_TYPES
    assert "image/jpeg" in ALLOWED_CONTENT_TYPES
    assert "image/png" in ALLOWED_CONTENT_TYPES

def test_build_response_formatting():
    """Verify standard CORS-compliant response format."""
    payload = {"status": "ok", "count": 1}
    res = build_response(200, payload)
    assert res["statusCode"] == 200
    assert res["headers"]["Access-Control-Allow-Origin"] == "*"
    assert json.loads(res["body"]) == payload
