"""
Textract AnalyzeExpense Response Normalizer

Parses raw Amazon Textract AnalyzeExpense API responses into a clean, normalized
invoice schema with field-level confidence scores, bounding geometries, and aggregate metrics.
"""

import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


def _clean_number(text: Optional[str]) -> Optional[float]:
    """Clean monetary and numeric text into a valid float."""
    if not text:
        return None
    # Strip currency symbols, commas, and whitespace
    cleaned = re.sub(r"[^\d.-]", "", text.strip())
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_int(text: Optional[str]) -> Optional[int]:
    """Clean count and integer text."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d]", "", text.strip())
    try:
        return int(cleaned)
    except ValueError:
        return None


def parse_summary_fields(summary_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract and normalize standard invoice summary fields from Textract.
    Maps Textract field types to standardized schema keys with confidence.
    """
    field_mapping = {
        "VENDOR_NAME": "vendorName",
        "VENDOR_ADDRESS": "vendorAddress",
        "VENDOR_PHONE": "vendorPhone",
        "INVOICE_RECEIPT_ID": "invoiceNumber",
        "INVOICE_RECEIPT_DATE": "invoiceDate",
        "DUE_DATE": "dueDate",
        "SUBTOTAL": "subtotal",
        "TAX": "taxAmount",
        "TOTAL": "totalAmount",
        "CURRENCY": "currency",
        "PAYMENT_TERMS": "paymentTerms",
    }

    numeric_fields = {"subtotal", "taxAmount", "totalAmount"}
    normalized: Dict[str, Any] = {}

    for field in summary_fields:
        type_obj = field.get("Type", {})
        type_name = type_obj.get("Text", "").upper()
        
        target_key = field_mapping.get(type_name)
        if not target_key:
            continue

        value_detection = field.get("ValueDetection", {})
        raw_val = value_detection.get("Text", "").strip()
        confidence = float(value_detection.get("Confidence", 0.0))
        geometry = value_detection.get("Geometry", {})

        # Parse numeric value if applicable
        parsed_val: Any = raw_val
        if target_key in numeric_fields:
            num = _clean_number(raw_val)
            parsed_val = num if num is not None else raw_val

        # Store with value, confidence, and bounding box
        normalized[target_key] = {
            "value": parsed_val,
            "rawText": raw_val,
            "confidence": round(confidence, 1),
            "geometry": geometry.get("BoundingBox", {})
        }

    return normalized


def parse_line_item_groups(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract and normalize tabular line items (description, quantity, unit price, total).
    """
    line_items: List[Dict[str, Any]] = []

    for group in groups:
        items = group.get("LineItems", [])
        for item in items:
            fields = item.get("LineItemExpenseFields", [])
            row_data: Dict[str, Any] = {
                "description": None,
                "quantity": 1,
                "unitPrice": None,
                "totalPrice": None,
                "confidence": 0.0
            }
            confidences: List[float] = []

            for f in fields:
                ftype = f.get("Type", {}).get("Text", "").upper()
                vdet = f.get("ValueDetection", {})
                vtext = vdet.get("Text", "").strip()
                vconf = float(vdet.get("Confidence", 0.0))
                confidences.append(vconf)

                if ftype in ("ITEM", "EXPENSE_ROW"):
                    row_data["description"] = vtext
                elif ftype == "QUANTITY":
                    row_data["quantity"] = _clean_int(vtext) or 1
                elif ftype == "UNIT_PRICE":
                    row_data["unitPrice"] = _clean_number(vtext)
                elif ftype == "PRICE":
                    row_data["totalPrice"] = _clean_number(vtext)

            # Fallback total calculation if totalPrice missing
            if row_data["totalPrice"] is None and row_data["unitPrice"] is not None:
                row_data["totalPrice"] = round(row_data["unitPrice"] * row_data["quantity"], 2)

            if confidences:
                row_data["confidence"] = round(sum(confidences) / len(confidences), 1)

            # Only append if we found at least a description or a price
            if row_data["description"] or row_data["totalPrice"] is not None:
                line_items.append(row_data)

    return line_items


def normalize_textract_expense(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full normalization pipeline for Textract AnalyzeExpense JSON output.
    Returns structured invoice extraction with summary fields, line items, and aggregate metrics.
    """
    expense_docs = response.get("ExpenseDocuments", [])
    if not expense_docs:
        return {
            "summaryFields": {},
            "lineItems": [],
            "metrics": {
                "totalFieldsDetected": 0,
                "averageConfidence": 0.0,
                "lowConfidenceFieldCount": 0
            }
        }

    # Analyze primary expense document (index 0)
    primary_doc = expense_docs[0]
    raw_summary = primary_doc.get("SummaryFields", [])
    raw_groups = primary_doc.get("LineItemGroups", [])

    summary = parse_summary_fields(raw_summary)
    line_items = parse_line_item_groups(raw_groups)

    # Compute confidence metrics
    all_confidences: List[float] = []
    low_confidence_count = 0
    CONFIDENCE_THRESHOLD = 80.0

    for f_info in summary.values():
        c = f_info.get("confidence", 0.0)
        all_confidences.append(c)
        if c < CONFIDENCE_THRESHOLD:
            low_confidence_count += 1

    for item in line_items:
        c = item.get("confidence", 0.0)
        all_confidences.append(c)
        if c < CONFIDENCE_THRESHOLD:
            low_confidence_count += 1

    avg_conf = (
        round(sum(all_confidences) / len(all_confidences), 1)
        if all_confidences
        else 0.0
    )

    return {
        "summaryFields": summary,
        "lineItems": line_items,
        "metrics": {
            "totalFieldsDetected": len(summary) + len(line_items),
            "averageConfidence": avg_conf,
            "lowConfidenceFieldCount": low_confidence_count
        }
    }
