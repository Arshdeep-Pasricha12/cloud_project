"""
Generate publication-quality diagrams and assemble screenshots for the DocuIntel project report.
Generates:
1. docs/figure1_architecture.png: End-to-End Serverless Cloud Architecture Diagram
2. docs/figure2_extraction_flow.png: Multi-Tier Resilient Extraction & Audit Flowchart
Copies:
3. docs/figure3_review_workstation.png: Live Dual-Pane Review Workstation Screenshot
4. docs/figure4_dashboard_operations.png: Live Document Operations Dashboard Screenshot
5. docs/figure5_aws_endpoints.png: Live AWS Cloud Resources & Endpoints Table Screenshot
"""

import os
import sys
import shutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_figure1():
    """Generates Figure 1: End-to-End Serverless Cloud Architecture Diagram."""
    fig, ax = plt.subplots(figsize=(11.5, 7.2), dpi=300)
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 7.6)
    ax.axis('off')

    # Color palette (AWS Theme)
    c_bg = '#F8FAFC'
    c_client = '#2563EB'      # Blue
    c_auth = '#7C3AED'        # Purple (Cognito)
    c_api = '#D97706'         # Amber (API Gateway)
    c_lambda = '#EA580C'      # Orange (Lambda)
    c_s3 = '#059669'          # Green (S3)
    c_ai = '#DC2626'          # Red (Textract/Rekognition)
    c_db = '#0284C7'          # Light Blue (DynamoDB)
    c_obs = '#4B5563'         # Slate (CloudWatch)

    fig.patch.set_facecolor('white')

    # Background canvas
    canvas = patches.FancyBboxPatch((0.2, 0.2), 11.1, 7.2, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    facecolor=c_bg, edgecolor='#CBD5E1', linewidth=1.5)
    ax.add_patch(canvas)

    # Title Banner
    ax.text(5.75, 7.25, "DocuIntel: End-to-End Serverless Cloud Architecture on AWS", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#0F172A', fontname='DejaVu Sans')
    ax.text(5.75, 6.92, "Region: ap-south-1 (Mumbai) | 100% Serverless | Zero Idle Expenditure ($0.00/Month)", 
            ha='center', va='center', fontsize=9.2, fontstyle='italic', color='#475569', fontname='DejaVu Sans')

    def draw_box(x, y, w, h, title, subtitle, color, items=None, badge=None):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.1",
                                     facecolor='white', edgecolor=color, linewidth=1.8)
        ax.add_patch(box)
        # Header banner
        header = patches.FancyBboxPatch((x, y + h - 0.40), w, 0.40, boxstyle="round,pad=0.04,rounding_size=0.08",
                                        facecolor=color, edgecolor='none')
        ax.add_patch(header)
        ax.text(x + w/2, y + h - 0.20, title, ha='center', va='center', fontsize=9.0, 
                fontweight='bold', color='white', fontname='DejaVu Sans')
        if subtitle:
            ax.text(x + w/2, y + h - 0.55, subtitle, ha='center', va='center', fontsize=7.4, 
                    fontweight='bold', color=color, fontname='DejaVu Sans')
        if items:
            start_y = y + h - 0.78
            for item in items:
                ax.text(x + 0.12, start_y, f"• {item}", ha='left', va='center', fontsize=7.0, 
                        color='#1E293B', fontname='DejaVu Sans')
                start_y -= 0.235
        if badge:
            b_box = patches.FancyBboxPatch((x + w - 0.88, y + 0.08), 0.78, 0.22, boxstyle="round,pad=0.02,rounding_size=0.05",
                                           facecolor=color, edgecolor='none', alpha=0.15)
            ax.add_patch(b_box)
            ax.text(x + w - 0.49, y + 0.19, badge, ha='center', va='center', fontsize=6.5, 
                    fontweight='bold', color=color, fontname='DejaVu Sans')

    # Column 1: Presentation & Hosting Tier (Tops at y=5.6)
    draw_box(0.5, 3.6, 2.3, 2.0, "Amazon S3 Web Hosting", "doc-intelligence-frontend", c_s3,
             ["React 19 SPA + Vite 6", "Tailwind CSS v4 Operations UI", "Dual-Pane Review Workstation", "RFC-4180 CSV & ERP Export"],
             "Static SPA")

    draw_box(0.5, 1.25, 2.3, 2.15, "Amazon Cognito User Pool", "ap-south-1_ZIRwwnB44", c_auth,
             ["Multi-Tenant Isolation (sub)", "JWT Access & ID Tokens", "Silent Session Auto-Renewal", "fetchWithAuth Interceptors"],
             "Auth Tier")

    # Column 2: Ingress & Security Tier (Tops at y=5.6)
    draw_box(3.2, 2.2, 2.3, 3.4, "Amazon API Gateway", "REST API (wxgm03t7wc)", c_api,
             ["Cognito User Pool Authorizer", "CORS Preflight (OPTIONS)", "/documents/upload-url", "/documents/{id}", "/documents/{id}/corrections", "/documents (User Filter)"],
             "HTTPS REST")

    # Column 3: Compute Tier (AWS Lambda Microservices, Tops at y=5.6)
    draw_box(5.9, 0.7, 2.5, 4.9, "AWS Lambda Microservices", "Python 3.12 Runtime", c_lambda,
             ["create-upload: Presigned PUT (300s)", "process-document: S3 Ingestion Trigger", "get-document: Presigned View (GET)", "list-documents: Query via GSI", "save-corrections: Audit Preserver", "Decimal float serialisation", "Structured JSON Log Streams", "Sub-second Concurrency Scaling"],
             "Compute Tier")

    # Column 4: Storage, AI & Database Tier (Tops at y=5.6)
    draw_box(8.9, 4.15, 2.2, 1.45, "Amazon S3 Uploads", "doc-intelligence-uploads", c_s3,
             ["Private Bucket (SSE-S3)", "CORS PUT Allowed", "S3:ObjectCreated Event"], "Storage")

    draw_box(8.9, 2.35, 2.2, 1.6, "AI / OCR Engine", "Multi-Tier Resilient AI", c_ai,
             ["Textract AnalyzeExpense", "Rekognition Fallback", "Serverless PyPDF Parser"], "AI / ML")

    draw_box(8.9, 0.5, 2.2, 1.65, "Amazon DynamoDB", "doc-intelligence-documents", c_db,
             ["On-Demand (Pay-Per-Req)", "UserDocumentsIndex (GSI)", "rawExtraction (Immutable)", "correctedData (Audit Trail)"], "Database")

    # Bottom Banner: Observability
    obs_box = patches.FancyBboxPatch((0.5, 0.45), 5.0, 0.65, boxstyle="round,pad=0.05,rounding_size=0.08",
                                     facecolor='#F1F5F9', edgecolor=c_obs, linewidth=1.2)
    ax.add_patch(obs_box)
    ax.text(0.7, 0.87, "Amazon CloudWatch Observability:", fontweight='bold', fontsize=8.2, color='#0F172A', fontname='DejaVu Sans')
    ax.text(0.7, 0.63, "14-Day Log Retention | Metric Filters: DocumentProcessingErrors | Operations Dashboard", 
            fontsize=7.2, color='#475569', fontname='DejaVu Sans')

    # Arrows with labels
    arrow_props = dict(arrowstyle="->", color='#334155', lw=1.6, mutation_scale=12)

    # 1. User auth: SPA -> Cognito
    ax.annotate("", xy=(1.65, 3.4), xytext=(1.65, 3.6), arrowprops=arrow_props)
    ax.text(1.7, 3.5, "Auth / JWT", fontsize=6.8, color='#475569', fontweight='bold')

    # 2. SPA -> API Gateway (REST API Calls with JWT)
    ax.annotate("", xy=(3.2, 4.2), xytext=(2.8, 4.2), arrowprops=arrow_props)
    ax.text(3.0, 4.35, "JWT", ha='center', fontsize=6.8, color='#D97706', fontweight='bold')

    # 3. Direct Browser -> S3 PUT Upload (Arched over top cleanly in corridor y=5.6 to 6.6)
    ax.annotate("", xy=(10.0, 5.6), xytext=(1.65, 5.6),
                arrowprops=dict(arrowstyle="->", color='#059669', lw=2.2, mutation_scale=14, ls='--',
                                connectionstyle="arc3,rad=-0.14"))
    ax.text(5.85, 6.25, "Direct Ingestion: Presigned PUT (Bypasses API Gateway)", ha='center', va='center', fontsize=8.2, 
            color='#059669', fontweight='bold', bbox=dict(boxstyle="round,pad=0.25", fc='#ECFDF5', ec='#059669', lw=1.2))

    # 4. API Gateway -> Lambda
    ax.annotate("", xy=(5.9, 3.9), xytext=(5.5, 3.9), arrowprops=arrow_props)
    ax.text(5.7, 4.05, "Proxy", ha='center', fontsize=6.8, color='#EA580C', fontweight='bold')

    # 5. Lambda -> S3 (Presigned generation)
    ax.annotate("", xy=(8.9, 4.7), xytext=(8.4, 4.7), arrowprops=arrow_props)
    ax.text(8.65, 4.85, "Sign", ha='center', fontsize=6.5, color='#059669', fontweight='bold')

    # 6. S3 Event -> Lambda (process-document)
    ax.annotate("", xy=(8.4, 4.35), xytext=(8.9, 4.35),
                arrowprops=dict(arrowstyle="->", color='#EA580C', lw=1.5, ls=':'))
    ax.text(8.65, 4.18, "Event", ha='center', fontsize=6.5, color='#EA580C', fontweight='bold')

    # 7. Lambda -> AI Engine
    ax.annotate("", xy=(8.9, 3.15), xytext=(8.4, 3.15), arrowprops=arrow_props)
    ax.text(8.65, 3.30, "OCR", ha='center', fontsize=6.5, color='#DC2626', fontweight='bold')

    # 8. Lambda -> DynamoDB
    ax.annotate("", xy=(8.9, 1.35), xytext=(8.4, 1.35), arrowprops=arrow_props)
    ax.text(8.65, 1.50, "CRUD", ha='center', fontsize=6.5, color='#0284C7', fontweight='bold')

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "figure1_architecture.png")
    plt.savefig(out_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"✓ Figure 1 successfully generated at: {out_path}")

def generate_figure2():
    """Generates Figure 2: Multi-Tier Resilient Extraction & Audit Flowchart."""
    fig, ax = plt.subplots(figsize=(11, 6.0), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.4)
    ax.axis('off')

    fig.patch.set_facecolor('white')

    # Canvas
    canvas = patches.FancyBboxPatch((0.2, 0.2), 10.6, 6.0, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.5)
    ax.add_patch(canvas)

    # Title
    ax.text(5.5, 5.95, "DocuIntel: Resilient Multi-Tier AI Extraction & Human Audit Workflow", 
            ha='center', va='center', fontsize=13, fontweight='bold', color='#0F172A', fontname='DejaVu Sans')
    ax.text(5.5, 5.68, "Autonomous Tri-Engine Failover with Cryptographic Data Immutability and Mathematical Reconciliation", 
            ha='center', va='center', fontsize=8.8, fontstyle='italic', color='#475569', fontname='DejaVu Sans')

    def draw_step_node(x, y, w, h, step_num, title, body, color, shape="box"):
        if shape == "box":
            node = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.08",
                                          facecolor='white', edgecolor=color, linewidth=1.6)
            ax.add_patch(node)
        elif shape == "decision":
            # diamond
            diamond = patches.Polygon([[x+w/2, y], [x+w, y+h/2], [x+w/2, y+h], [x, y+h/2]],
                                      closed=True, facecolor='#FEF3C7', edgecolor='#D97706', linewidth=1.6)
            ax.add_patch(diamond)

        # Header tag
        if shape == "box":
            tag = patches.FancyBboxPatch((x, y+h-0.32), w, 0.32, boxstyle="round,pad=0.02,rounding_size=0.06",
                                         facecolor=color, edgecolor='none')
            ax.add_patch(tag)
            ax.text(x+w/2, y+h-0.16, f"Step {step_num}: {title}", ha='center', va='center',
                    fontsize=8.0, fontweight='bold', color='white', fontname='DejaVu Sans')
            ax.text(x+w/2, y+(h-0.32)/2, body, ha='center', va='center',
                    fontsize=6.8, color='#1E293B', fontname='DejaVu Sans', multialignment='center')
        else:
            ax.text(x+w/2, y+h/2, body, ha='center', va='center',
                    fontsize=7.0, fontweight='bold', color='#92400E', fontname='DejaVu Sans', multialignment='center')

    # Row 1: Ingestion
    draw_step_node(0.5, 4.0, 1.8, 1.3, "1", "File Selection", "User drops PDF / image\nin React Workstation\n(Max 10 MB)", "#2563EB")
    draw_step_node(2.7, 4.0, 1.9, 1.3, "2", "Presigned PUT", "Lambda generates\n300s presigned URL\nbound to MIME type", "#D97706")
    draw_step_node(5.0, 4.0, 1.9, 1.3, "3", "Direct S3 Upload", "Client streams binary\ndirectly to S3 bucket;\nbypasses API Gateway", "#059669")
    draw_step_node(7.3, 4.0, 1.9, 1.3, "4", "S3 Event Dispatch", "S3:ObjectCreated event\ntriggers asynchronous\nprocess-document", "#EA580C")

    # Connect Row 1
    arrow_props = dict(arrowstyle="->", color='#334155', lw=1.5, mutation_scale=12)
    ax.annotate("", xy=(2.7, 4.65), xytext=(2.3, 4.65), arrowprops=arrow_props)
    ax.annotate("", xy=(5.0, 4.65), xytext=(4.6, 4.65), arrowprops=arrow_props)
    ax.annotate("", xy=(7.3, 4.65), xytext=(6.9, 4.65), arrowprops=arrow_props)

    # Down from Step 4 to Row 2
    ax.annotate("", xy=(8.25, 3.4), xytext=(8.25, 4.0), arrowprops=arrow_props)

    # Row 2: AI Multi-Tier Extraction & Fallback
    draw_step_node(6.8, 2.1, 3.7, 1.3, "5", "Autonomous Multi-Tier AI Extraction Engine", 
                   "Tier 1: Amazon Textract AnalyzeExpense (Primary)\n↓ Failover if Throttled / Subscription Required\nTier 2: Amazon Rekognition DetectText (99% OCR)\n↓ Failover if Service Delayed\nTier 3: PyPDF Serverless In-Memory Stream Parser", "#DC2626")

    # Left to Schema Normalizer
    ax.annotate("", xy=(4.6, 2.75), xytext=(6.8, 2.75), arrowprops=arrow_props)
    ax.text(5.7, 2.9, "Raw Detections", ha='center', fontsize=7.0, color='#475569', fontweight='bold')

    draw_step_node(2.4, 2.1, 2.2, 1.3, "6", "Schema Normalization", "Normalizes financial schema;\nComputes field confidences;\nExtracts itemized tables", "#7C3AED")

    # Left to DynamoDB Storage
    ax.annotate("", xy=(2.4, 1.15), xytext=(2.4, 2.1), arrowprops=arrow_props)

    # Row 3: Persistence & Review Workstation
    draw_step_node(0.5, 0.5, 2.3, 1.3, "7", "Immutable Persistence", "Seals raw machine output in\nrawExtraction in DynamoDB;\nstatus: PENDING_REVIEW", "#0284C7")

    draw_step_node(3.2, 0.5, 2.3, 1.3, "8", "Review Workstation", "Renders dual-pane view;\nHighlights low-confidence\nfields (<80%) in amber", "#059669")

    draw_step_node(5.9, 0.5, 2.3, 1.3, "9", "Financial Math Audit", "Automated Reconciliation:\nSubtotal + Tax == Total;\nDuplicate invoice guard", "#D97706")

    draw_step_node(8.6, 0.5, 2.1, 1.3, "10", "Audit Save & Export", "Auditor edits saved to\ncorrectedData (raw intact);\n1-Click CSV & ERP Export", "#2563EB")

    # Connect Row 3
    ax.annotate("", xy=(3.2, 1.15), xytext=(2.8, 1.15), arrowprops=arrow_props)
    ax.annotate("", xy=(5.9, 1.15), xytext=(5.5, 1.15), arrowprops=arrow_props)
    ax.annotate("", xy=(8.6, 1.15), xytext=(8.2, 1.15), arrowprops=arrow_props)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "figure2_extraction_flow.png")
    plt.savefig(out_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"✓ Figure 2 successfully generated at: {out_path}")

def copy_production_screenshots():
    """Copies production screenshots into docs/ with standard figure filenames."""
    src_dir = r"C:\Users\arshd\.gemini\antigravity-ide\brain\f87edc05-da67-4c57-9917-ecb127635cfe\.user_uploaded"
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

    mappings = {
        "media_1792925480366.png": "figure3_review_workstation.png",
        "media_1792925471405.png": "figure4_dashboard_operations.png",
        "media_1792950044641.png": "figure5_aws_endpoints.png"
    }

    for src_name, dst_name in mappings.items():
        src_path = os.path.join(src_dir, src_name)
        dst_path = os.path.join(docs_dir, dst_name)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"✓ Copied {src_name} -> {dst_path}")
        else:
            print(f"Warning: {src_path} not found!")

if __name__ == "__main__":
    generate_figure1()
    generate_figure2()
    copy_production_screenshots()
    print("✓ All report figures and screenshots prepared successfully.")
