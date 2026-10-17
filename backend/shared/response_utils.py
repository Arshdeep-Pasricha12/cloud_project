import json
from decimal import Decimal
from typing import Any, Dict, Optional

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle DynamoDB Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def build_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Standardize API Gateway Lambda proxy response format with CORS support.
    
    Args:
        status_code: HTTP status code (200, 400, 500, etc.)
        body: Python dict, list, or primitive to be JSON serialized
        headers: Additional custom headers
        
    Returns:
        Dict conforming to AWS API Gateway Lambda Proxy integration response
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }

    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body, cls=DecimalEncoder) if not isinstance(body, str) else body
    }
