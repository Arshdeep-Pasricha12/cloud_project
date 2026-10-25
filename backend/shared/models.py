"""
Data models, schemas, and lifecycle states for Document Intelligence.
"""
from enum import Enum
import os
import re
from typing import Dict, Any, List, Optional, Tuple

class DocumentStatus(str, Enum):
    """
    Lifecycle processing states for uploaded documents.
    """
    UPLOADED = "UPLOADED"              # Presigned URL generated, uploaded to S3
    PROCESSING = "PROCESSING"          # Textract AnalyzeExpense triggered & analyzing
    PENDING_REVIEW = "PENDING_REVIEW"  # Textract complete, awaiting user review/correction
    REVIEWED = "REVIEWED"              # User reviewed, validated, and saved corrections
    FAILED = "FAILED"                  # Textract extraction or validation error

ALLOWED_CONTENT_TYPES: Dict[str, List[str]] = {
    "application/pdf": [".pdf"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"]
}

MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
URL_EXPIRATION_SECONDS: int = 300            # 5 minutes


def sanitize_filename(raw_filename: str) -> str:
    """
    Sanitize client-provided filename to prevent path traversal and special character injection.
    
    Rules:
    - Strips directory path components (both / and \\).
    - Removes dangerous characters, keeping only alphanumeric, dot, underscore, and hyphen.
    - Limits name to 100 characters before extension.
    - Falls back to 'document' if filename becomes empty.
    """
    if not raw_filename or not isinstance(raw_filename, str):
        return "document.pdf"
    
    # Extract only the base name (strip paths)
    base_name = os.path.basename(raw_filename.replace("\\", "/"))
    
    # Split extension
    parts = base_name.rsplit(".", 1)
    name_part = parts[0]
    ext_part = f".{parts[1].lower()}" if len(parts) > 1 else ""
    
    # Replace whitespace with hyphens and sanitize characters
    clean_name = re.sub(r"[^\w\-_]", "_", name_part.strip())
    clean_name = re.sub(r"_+", "_", clean_name).strip("_")
    
    if not clean_name:
        clean_name = "document"
    
    # Truncate clean_name if too long (max 80 chars + ext)
    clean_name = clean_name[:80]
    
    # Clean extension: only alphanumeric
    clean_ext = re.sub(r"[^\w]", "", ext_part.lstrip("."))
    
    return f"{clean_name}.{clean_ext}" if clean_ext else clean_name


def validate_upload_metadata(
    file_name: Any,
    content_type: Any,
    file_size: Any,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate metadata requested by frontend for presigned S3 upload.
    
    Returns:
        (is_valid, error_message, sanitized_filename)
    """
    # 1. Validate file_name
    if not file_name or not isinstance(file_name, str) or not file_name.strip():
        return False, "Missing or invalid 'fileName' in request body.", None
    
    if len(file_name) > 255:
        return False, "'fileName' is excessively long (maximum 255 characters).", None
    
    # Path traversal check
    if ".." in file_name or file_name.startswith("/") or file_name.startswith("\\"):
        # We will sanitize it, but if it was an active traversal attempt, sanitize ensures it's safe
        pass
    
    sanitized = sanitize_filename(file_name)
    
    # 2. Validate content_type
    if not content_type or not isinstance(content_type, str):
        return False, "Missing or invalid 'contentType' in request body.", None
    
    content_type_clean = content_type.strip().lower()
    if content_type_clean not in ALLOWED_CONTENT_TYPES:
        allowed = ", ".join(ALLOWED_CONTENT_TYPES.keys())
        return False, f"Unsupported MIME type '{content_type}'. Allowed types are: {allowed}.", None
    
    # Check extension matches content type
    allowed_extensions = ALLOWED_CONTENT_TYPES[content_type_clean]
    has_valid_ext = any(sanitized.lower().endswith(ext) for ext in allowed_extensions)
    if not has_valid_ext:
        # Append default extension for this MIME type if missing or mismatched
        sanitized = f"{sanitized}{allowed_extensions[0]}"
    
    # 3. Validate file_size
    if file_size is None or isinstance(file_size, bool) or not isinstance(file_size, (int, float)):
        return False, "Missing or invalid 'fileSize' in request body. Must be a positive integer in bytes.", None
    
    try:
        size_int = int(file_size)
    except (ValueError, TypeError):
        return False, "'fileSize' must be a valid integer.", None
    
    if size_int <= 0:
        return False, "'fileSize' must be greater than 0 bytes.", None
    
    if size_int > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        return False, f"Declared 'fileSize' ({size_int} bytes) exceeds maximum allowed size of {max_mb:.0f} MB.", None
    
    return True, None, sanitized
