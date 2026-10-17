"""
Data models, schemas, and lifecycle states for Document Intelligence.
"""
from enum import Enum
from typing import Dict, Any, List, Optional

class DocumentStatus(str, Enum):
    """
    Lifecycle processing states for uploaded documents.
    """
    UPLOADED = "UPLOADED"              # Presigned URL generated, uploaded to S3
    PROCESSING = "PROCESSING"          # Textract AnalyzeExpense triggered & analyzing
    PENDING_REVIEW = "PENDING_REVIEW"  # Textract complete, awaiting user review/correction
    REVIEWED = "REVIEWED"              # User reviewed, validated, and saved corrections
    FAILED = "FAILED"                  # Textract extraction or validation error

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/tiff": ".tiff"
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
