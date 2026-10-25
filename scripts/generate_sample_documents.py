"""
Generate realistic sample business documents (PDF invoices and PNG/JPG receipts)
for testing the Serverless Document Intelligence Platform upload and extraction pipeline.
"""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "sample_documents"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_invoice_acme_cloud():
    """Generate sample PDF: Acme Cloud Technologies SaaS Invoice"""
    filepath = OUTPUT_DIR / "invoice_acme_cloud.pdf"
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1e293b')
    )
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )
    bold_meta = ParagraphStyle(
        'BoldMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0f172a')
    )

    # Header block
    header_data = [
        [
            Paragraph("<b>ACME CLOUD TECHNOLOGIES INC.</b><br/>100 Innovation Way, Suite 400<br/>San Francisco, CA 94107<br/>billing@acmecloud.io", meta_style),
            Paragraph("<b>INVOICE</b><br/><font color='#6366f1'>#INV-2026-0881</font><br/>Date: Oct 15, 2026<br/>Due: Nov 15, 2026", bold_meta)
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=15))

    # Bill To block
    bill_data = [
        [
            Paragraph("<b>BILLED TO:</b><br/>TechVentures Global Corp.<br/>Attn: Accounts Payable<br/>750 Silicon Boulevard, Floor 8<br/>San Jose, CA 95134", meta_style),
            Paragraph("<b>PAYMENT TERMS:</b><br/>Net 30 Days<br/>Currency: USD ($)<br/>PO Reference: PO-99214", meta_style)
        ]
    ]
    bill_table = Table(bill_data, colWidths=[3.5 * inch, 3.5 * inch])
    bill_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 20))

    # Line Items Table
    table_data = [
        ["Item / Description", "Qty", "Unit Price", "Total Amount"],
        ["Enterprise Cloud Platform Subscription - October 2026", "1", "$1,200.00", "$1,200.00"],
        ["Dedicated VPC & High Availability Load Balancer", "1", "$150.00", "$150.00"],
        ["Document Intelligence Textract API Processing Tier", "1", "$70.50", "$70.50"],
        ["Advanced Threat Detection & Encryption Module", "1", "$85.00", "$85.00"]
    ]
    item_table = Table(table_data, colWidths=[4.2 * inch, 0.7 * inch, 1.1 * inch, 1.1 * inch])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    story.append(item_table)
    story.append(Spacer(1, 15))

    # Totals block
    totals_data = [
        ["Subtotal:", "$1,505.50"],
        ["Sales Tax (8.25%):", "$124.20"],
        ["Total Amount Due:", "$1,629.70"]
    ]
    totals_table = Table(totals_data, colWidths=[5.5 * inch, 1.6 * inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 9),
        ('FONTSIZE', (0, 2), (-1, 2), 11),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#4338ca')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 30))

    # Footer note
    footer_text = "<font color='#94a3b8'>Thank you for your business. Remit electronic ACH payments to Routing: 121000358, Account: 9876543210.</font>"
    story.append(Paragraph(footer_text, meta_style))

    doc.build(story)
    print(f"Created: {filepath.name}")


def create_invoice_nexus_consulting():
    """Generate sample PDF: Nexus Consulting Services Invoice"""
    filepath = OUTPUT_DIR / "invoice_nexus_consulting.pdf"
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    story = []
    styles = getSampleStyleSheet()

    meta_style = ParagraphStyle(
        'MetaText2',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    header_data = [
        [
            Paragraph("<b>NEXUS ARCHITECTURE CONSULTING LLP</b><br/>452 Enterprise Plaza, Suite 1200<br/>New York, NY 10001<br/>tax-id: 13-9827410", meta_style),
            Paragraph("<b>CONSULTING INVOICE</b><br/><font color='#0284c7'>#NEX-2026-1042</font><br/>Issue Date: Oct 20, 2026<br/>Payment Due: Nov 04, 2026", meta_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=15))

    bill_data = [
        [
            Paragraph("<b>CLIENT:</b><br/>Arshdeep Cloud Innovations Ltd.<br/>Project: Serverless Document Intelligence Platform<br/>Email: project@cloudinnovations.dev", meta_style),
            Paragraph("<b>CONTRACT REF:</b><br/>SOW-2026-AWS-ARCH<br/>Net 15 Days", meta_style)
        ]
    ]
    bill_table = Table(bill_data, colWidths=[3.5 * inch, 3.5 * inch])
    bill_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 20))

    table_data = [
        ["Service Description", "Hours", "Hourly Rate", "Total ($)"],
        ["AWS Serverless Architecture Assessment & Well-Architected Review", "16.0", "$175.00", "$2,800.00"],
        ["Amazon Textract AnalyzeExpense Normalization Pipeline Design", "8.0", "$175.00", "$1,400.00"],
        ["IAM Least Privilege Policy Audit & Security Hardening", "6.0", "$190.00", "$1,140.00"]
    ]
    item_table = Table(table_data, colWidths=[4.2 * inch, 0.7 * inch, 1.1 * inch, 1.1 * inch])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
    ]))
    story.append(item_table)
    story.append(Spacer(1, 15))

    totals_data = [
        ["Subtotal:", "$5,340.00"],
        ["Professional Services Tax (Exempt):", "$0.00"],
        ["Total Balance Due:", "$5,340.00"]
    ]
    totals_table = Table(totals_data, colWidths=[5.5 * inch, 1.6 * inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#0284c7')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
    ]))
    story.append(totals_table)
    doc.build(story)
    print(f"Created: {filepath.name}")


def create_receipt_office_depot():
    """Generate sample PNG: Office Equipment & Paper Receipt"""
    filepath = OUTPUT_DIR / "receipt_office_depot.png"
    width, height = 550, 750
    img = Image.new("RGB", (width, height), color=(252, 252, 250))
    draw = ImageDraw.Draw(img)

    # Use default font
    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_item = ImageFont.truetype("cour.ttf", 14)
        font_bold = ImageFont.truetype("courbd.ttf", 16)
    except Exception:
        font_title = font_sub = font_item = font_bold = ImageFont.load_default()

    y = 35
    draw.text((width // 2, y), "OFFICE SUPPLIES DEPOT", fill=(20, 20, 20), font=font_title, anchor="mt")
    y += 30
    draw.text((width // 2, y), "Store #4812 · 720 Tech Drive, Suite 10", fill=(70, 70, 70), font=font_sub, anchor="mt")
    y += 18
    draw.text((width // 2, y), "Tel: (555) 019-2831 · Receipt: RCP-99418", fill=(90, 90, 90), font=font_sub, anchor="mt")
    y += 18
    draw.text((width // 2, y), "Date: 10/22/2026  14:32:18", fill=(90, 90, 90), font=font_sub, anchor="mt")
    y += 30

    # Separator line
    draw.line([(40, y), (width - 40, y)], fill=(180, 180, 180), width=1)
    y += 20

    items = [
        ("Wireless Ergonomic Keyboard Combo", "$65.99"),
        ("Multipurpose Copy Paper 5-Ream Case", "$38.50"),
        ("Dual-Display HDMI Docking Station", "$119.00"),
        ("Gel Ink Pens 12-Pack (Black 0.7mm)", "$14.25")
    ]

    for desc, price in items:
        draw.text((45, y), desc, fill=(30, 30, 30), font=font_item)
        draw.text((width - 45, y), price, fill=(30, 30, 30), font=font_item, anchor="ra")
        y += 30

    y += 10
    draw.line([(40, y), (width - 40, y)], fill=(180, 180, 180), width=1)
    y += 20

    totals = [
        ("Subtotal:", "$237.74"),
        ("Sales Tax (8.25%):", "$19.61"),
        ("TOTAL PAID:", "$257.35")
    ]

    for label, val in totals:
        f = font_bold if "TOTAL" in label else font_item
        color = (0, 0, 0) if "TOTAL" in label else (50, 50, 50)
        draw.text((width - 240, y), label, fill=color, font=f)
        draw.text((width - 45, y), val, fill=color, font=f, anchor="ra")
        y += 28

    y += 20
    draw.line([(40, y), (width - 40, y)], fill=(200, 200, 200), width=1)
    y += 25
    draw.text((width // 2, y), "PAID BY: VISA ENDING IN 4921", fill=(80, 80, 80), font=font_sub, anchor="mt")
    y += 20
    draw.text((width // 2, y), "Auth Code: 088421 · Chip Read Approved", fill=(100, 100, 100), font=font_sub, anchor="mt")
    y += 25
    draw.text((width // 2, y), "*** THANK YOU FOR SHOPPING WITH US ***", fill=(120, 120, 120), font=font_sub, anchor="mt")

    img.save(filepath, "PNG")
    print(f"Created: {filepath.name}")


def create_receipt_urban_cafe():
    """Generate sample JPG: Restaurant / Catering Dining Receipt"""
    filepath = OUTPUT_DIR / "receipt_urban_cafe.jpg"
    width, height = 500, 680
    img = Image.new("RGB", (width, height), color=(255, 253, 248))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_sub = ImageFont.truetype("arial.ttf", 12)
        font_item = ImageFont.truetype("cour.ttf", 13)
        font_bold = ImageFont.truetype("courbd.ttf", 15)
    except Exception:
        font_title = font_sub = font_item = font_bold = ImageFont.load_default()

    y = 30
    draw.text((width // 2, y), "THE URBAN CAFE & BISTRO", fill=(30, 25, 20), font=font_title, anchor="mt")
    y += 26
    draw.text((width // 2, y), "455 Market Street, San Francisco, CA", fill=(80, 75, 70), font=font_sub, anchor="mt")
    y += 18
    draw.text((width // 2, y), "Table: 14  ·  Server: Maya G.  ·  Order #8831", fill=(90, 85, 80), font=font_sub, anchor="mt")
    y += 18
    draw.text((width // 2, y), "Date: 10/24/2026 12:45 PM", fill=(100, 95, 90), font=font_sub, anchor="mt")
    y += 25

    draw.line([(35, y), (width - 35, y)], fill=(180, 175, 165), width=1)
    y += 18

    items = [
        ("2x Artisan Cold Brew Coffee", "$12.00"),
        ("1x Smoked Salmon Tartine", "$17.50"),
        ("1x Organic Quinoa Salad Bowl", "$15.00"),
        ("1x Matcha Almond Croissant", "$6.50")
    ]

    for desc, price in items:
        draw.text((40, y), desc, fill=(35, 30, 25), font=font_item)
        draw.text((width - 40, y), price, fill=(35, 30, 25), font=font_item, anchor="ra")
        y += 28

    y += 10
    draw.line([(35, y), (width - 35, y)], fill=(180, 175, 165), width=1)
    y += 18

    totals = [
        ("Subtotal:", "$51.00"),
        ("Sales Tax:", "$4.46"),
        ("Tip (18%):", "$9.98"),
        ("TOTAL:", "$65.44")
    ]

    for label, val in totals:
        f = font_bold if "TOTAL" in label else font_item
        color = (15, 15, 15) if "TOTAL" in label else (60, 55, 50)
        draw.text((width - 200, y), label, fill=color, font=f)
        draw.text((width - 40, y), val, fill=color, font=f, anchor="ra")
        y += 26

    y += 15
    draw.line([(35, y), (width - 35, y)], fill=(200, 195, 185), width=1)
    y += 20
    draw.text((width // 2, y), "PAID VIA APPLE PAY (Mastercard *8190)", fill=(70, 65, 60), font=font_sub, anchor="mt")
    y += 20
    draw.text((width // 2, y), "Thank you for dining with us!", fill=(110, 105, 100), font=font_sub, anchor="mt")

    img.save(filepath, "JPEG", quality=95)
    print(f"Created: {filepath.name}")


if __name__ == "__main__":
    print(f"Generating realistic test documents in: {OUTPUT_DIR}")
    create_invoice_acme_cloud()
    create_invoice_nexus_consulting()
    create_receipt_office_depot()
    create_receipt_urban_cafe()
    print("All 4 sample test documents generated successfully!")
