# DocuIntel — Serverless Financial Document Intelligence & Operations Platform

An enterprise-grade, serverless cloud platform engineered on Amazon Web Services (AWS) to automate accounts payable, invoice extraction, and financial document operations. 

DocuIntel ingests complex business documents (invoices, receipts, purchase orders), processes them through a multi-tier cloud OCR and AI pipeline (**Amazon Textract** with **Amazon Rekognition** fallback), presents extractions in an interactive human-in-the-loop review workstation, validates arithmetic calculations, guards against duplicate submissions, and persists verified audit records into **Amazon DynamoDB** while strictly maintaining raw extraction immutability.

---

## 1. System Architecture

```
                                    +-----------------------------------------+
                                    |         Amazon Cognito User Pool        |
                                    |       (JWT & REFRESH_TOKEN_AUTH)        |
                                    +--------------------+--------------------+
                                                         |
                                            (JWT Bearer) | (Silent Auto-Renewal)
                                                         v
+-------------------------------+  ======>  +---------------------------------+
|   React Operations Frontend   |           |    Amazon API Gateway REST API  |
|  (S3 Static Website Hosting)  |           |   (Cognito Authorizer & CORS)   |
+---------------+---------------+           +----------------+----------------+
                |                                            |
                | (Direct Presigned PUT)                     | Lambda Proxy
                v                                            v
+-------------------------------+ <======   +---------------------------------+
|  Amazon S3 Document Bucket    |           |   AWS Lambda Microservices      |
|  (Private, SSE-S3 AES-256)    |           |        (Python 3.12)            |
+-------------------------------+           +----------------+----------------+
                                                             |
                             +-------------------------------+-------------------------------+
                             |                               |                               |
                             v                               v                               v
            +---------------------------------+  +-----------------------+  +-----------------------+
            |  Multi-Tier Extraction Engine   |  |   Amazon DynamoDB     |  |   Amazon CloudWatch   |
            |  1. Textract (AnalyzeExpense)   |  |   (Documents Table &  |  |  (Metrics, Alarms,    |
            |  2. Rekognition (DetectText)    |  |  UserDocumentsIndex)  |  |  Executive Dashboard) |
            |  3. Serverless PyPDF Parser     |  |                       |  |                       |
            +---------------------------------+  +-----------------------+  +-----------------------+
```

### Architecture Highlights
- **Direct-to-S3 Ingestion**: Clients request cryptographic presigned PUT URLs via API Gateway; documents are uploaded directly to S3 with `AES256` server-side encryption, bypassing Lambda memory and execution limits.
- **Event-Driven Processing**: S3 uploads trigger processing asynchronously via Lambda, isolating ingestion throughput from compute latency.
- **Multi-Tier AI/OCR Resilience**: Primary extraction uses Amazon Textract `AnalyzeExpense`. If Textract experiences subscription delays or regional throttling, the system seamlessly falls back to Amazon Rekognition OCR (`DetectText`) for receipt and invoice images, and bundled PyPDF parsing for PDF documents.
- **Strict Data Immutability**: The original AI extraction is permanently sealed in `rawExtraction`. User modifications, human approvals, and line-item corrections are stored in an independent `correctedData` object with complete audit timestamps.
- **Persistent Multi-Tenant Security**: User workspaces are keyed by Amazon Cognito `sub` IDs. Sessions automatically rotate via Cognito's `REFRESH_TOKEN_AUTH` flow, ensuring zero session loss on reload.

---

## 2. Live Production Endpoints & Cloud Resources

| Service | Cloud Resource | Description | Live Endpoint / Identifier |
| :--- | :--- | :--- | :--- |
| **Web Hosting** | Amazon S3 Static Website | Production Single-Page React App | **[Live Web App](http://doc-intelligence-frontend-399383129700.s3-website.ap-south-1.amazonaws.com)** |
| **Authentication** | Amazon Cognito User Pool | User Auth, JWT & Silent Refresh | `ap-south-1_ZIRwwnB44` (Client: `4ai8598ftdkf0fc2hm4bd1v75k`) |
| **API Gateway** | REST API (`doc-intelligence-api`) | Cognito Authorized REST routes | `https://wxgm03t7wc.execute-api.ap-south-1.amazonaws.com/prod` |
| **Document Storage** | Amazon S3 Private Bucket | Encrypted storage (`AES256`, CORS) | `doc-intelligence-uploads-399383129700` |
| **Document Database** | Amazon DynamoDB | On-Demand table with GSI | `doc-intelligence-documents` (`UserDocumentsIndex`) |
| **AI & OCR Extraction** | Amazon Textract + Rekognition | Multi-tier financial OCR pipeline | Textract `AnalyzeExpense` & Rekognition `DetectText` |
| **Operations** | Amazon CloudWatch | Alarms, Metric Filters & Dashboard | **[Live Executive Dashboard](https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards/dashboard/doc-intelligence-dashboard)** |

---

## 3. Core Enterprise Capabilities

### 1. Multi-Tier AI Document Extraction
- Extracts structured key-value pairs: Vendor Name, Invoice Number, Invoice Date, Due Date, Payment Terms, Subtotal, Tax / VAT, and Total Amount.
- Normalizes itemized line tables with descriptions, quantities, unit prices, and line totals.
- Assigns field-level confidence scores (0–100%) so reviewers can focus specifically on low-confidence values.

### 2. Automated Financial Reconciliation & Arithmetic Audit
- Automatically validates invoice arithmetic: verifies that `Subtotal + Tax == Total Amount`.
- Immediately flags calculation discrepancies, rounding anomalies, or hidden vendor charges with clear inline alerts in the review workstation.

### 3. Duplicate Invoice & Fraud Prevention Guard
- Cross-references incoming invoice numbers and vendor identities against all historical records in the workspace.
- Warns accounting operators if an identical invoice number from the same vendor has already been ingested or approved.

### 4. 1-Click Accounting & ERP Export Suite
- **Reconciliation CSV**: Generates a standard accounting CSV with vendor names, invoice numbers, dates, subtotal, tax, net total, status, and OCR confidence ratings for instant spreadsheet reconciliation.
- **Enterprise ERP JSON**: Exports standard ERP schemas compatible with SAP, Oracle NetSuite, and QuickBooks, including line items, tax breakdowns, and complete AWS processing metadata.

### 5. Human-in-the-Loop Review Workstation
- Side-by-side interactive document workstation with integrated high-resolution document viewer (zoom, pan, fit-to-width).
- Real-time editable invoice fields and line items with instant total recalculation.
- One-click approval workflows that update document status to `REVIEWED` in DynamoDB.

### 6. Zero-Downtime Session Persistence
- Built-in automatic token renewal using Cognito's `REFRESH_TOKEN_AUTH` flow.
- Seamlessly refreshes authentication tokens in the background within 60 seconds of expiration; eliminates abrupt logouts or "empty upload" states on page refresh.

---

## 4. Technology Stack

- **Frontend Application**:
  - React 19 + Vite SPA architecture
  - React Router v7 with SPA 404-fallback routing
  - Lucide React iconography
  - Custom Vanilla CSS Design System (Clean, calm financial operations interface; Inter & Outfit typography; zero generic dark glassmorphism)
- **Backend & Cloud Infrastructure (Serverless Microservices)**:
  - Python 3.12 AWS Lambda functions
  - Amazon API Gateway (REST API with Cognito User Pool Authorizer & CORS preflight)
  - Amazon Cognito User Pools (Multi-tenant tenant isolation & refresh token auth)
  - Amazon S3 (Document lake with short-lived presigned URLs & SSE-S3 AES-256)
  - Amazon Textract (`AnalyzeExpense` API)
  - Amazon Rekognition (`DetectText` OCR fallback)
  - Amazon DynamoDB (Pay-per-request On-Demand billing, Global Secondary Index)
  - Amazon CloudWatch (Metric filters for `DocumentProcessingErrors`, alarms, and operational dashboard)
- **Quality Assurance & Testing**:
  - Backend: Pytest (36 automated unit and end-to-end pipeline tests)
  - Frontend: Node.js Test Runner (18 unit tests for auth, uploads, and API integration)

---

## 5. Repository Directory Layout

```
cloud_project/
├── frontend/
│   ├── public/               # Static assets & favicon
│   ├── src/
│   │   ├── components/       # Reusable components (Sidebar, Header, MetricsCards, UploadModal)
│   │   ├── context/          # AuthContext with automated token refresh & guest fallback
│   │   ├── hooks/            # useDocuments data fetching & mutation hook
│   │   ├── pages/            # DashboardPage, DocumentsPage, DocumentReviewPage, SettingsPage
│   │   ├── services/         # authService (Cognito SDK), api.js (Gateway client), uploadService
│   │   ├── utils/            # exportUtils (CSV/JSON), constants, formatters
│   │   ├── App.jsx           # App shell with responsive navigation
│   │   ├── main.jsx          # Root React entry point
│   │   └── index.css         # Financial design tokens, layout grids, typography
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── shared/               # Shared response utils, CORS, Decimal encoder, document_extractor
│   ├── functions/
│   │   ├── create-upload/    # S3 presigned PUT URL generator
│   │   ├── process-document/ # Multi-tier Textract & Rekognition OCR extraction engine
│   │   ├── get-document/     # Document retrieval with presigned GET view URLs
│   │   ├── list-documents/   # DynamoDB GSI user query & financial status aggregation
│   │   └── save-corrections/ # Immutability-preserving human corrections writer
│   ├── tests/                # 36 Pytest unit and pipeline tests
│   └── requirements.txt      # Python dependencies
├── infrastructure/           # CloudFormation / serverless resource definitions & architecture specs
├── docs/                     # Architecture documentation and presentation runbooks
│   ├── architecture.md       # High-level architecture, state machines, and data schemas
│   ├── implementation-plan.md# Engineering specifications
│   └── college-presentation-guide.md # Architecture defense talking points & evaluator Q&A
├── scripts/                  # Cloud deployment automation scripts
│   ├── deploy_lambdas.py
│   ├── deploy_milestone8_hosting.py # Production S3 static website builder & deployer
│   └── run_local_backend.py
└── README.md
```

---

## 6. Local Development & Setup

### Prerequisites
- **Node.js**: v18.0.0 or later (v22 tested)
- **npm**: v9.0.0 or later
- **Python**: v3.10 or later (v3.12 tested)
- **AWS CLI v2**: Configured with appropriate AWS credentials

### Step 1: Install Frontend Dependencies
```powershell
cd frontend
npm install
```

### Step 2: Start Development Server
```powershell
npm run dev
```
The application will launch locally at **`http://localhost:5173`**.

### Step 3: Run Automated Test Suites
```powershell
# 1. Run full backend test suite (36 tests: S3, DynamoDB, Textract & End-to-End Pipeline)
pytest backend/tests/ -v

# 2. Run frontend test suite (18 tests: Auth, Uploads, API Gateway client)
cd frontend
npm test
```

### Step 4: Build Production Bundle
```powershell
cd frontend
npm run build
```

### Step 5: Deploy to AWS S3 Static Website Hosting
```powershell
python scripts/deploy_milestone8_hosting.py
```

---

## 7. AWS Security & Cost Optimization

1. **Zero Secret Ingestion**: No AWS access keys, secrets, or administrative credentials exist in frontend client code. All AWS interactions are arbitrated via short-lived Cognito JWTs or signed URLs.
2. **Least Privilege IAM**: Lambda execution roles are scoped strictly to their respective resources (e.g. `s3:GetObject` on `doc-intelligence-uploads-*/*`, `dynamodb:PutItem` on `doc-intelligence-documents`).
3. **Multi-Tenant User Isolation**: Every DynamoDB query strictly enforces the authenticated user's Cognito `sub` identifier as the partition key. Users cannot read or modify documents belonging to another tenant.
4. **100% Free-Tier Eligible Serverless Architecture**:
   - **AWS Lambda**: 1M free requests/month
   - **Amazon API Gateway**: 1M free calls/month (HTTP/REST)
   - **Amazon S3**: 5 GB storage + 20,000 GET requests/month
   - **Amazon DynamoDB**: 25 GB free storage + 25 WCU / 25 RCU On-Demand
   - **Amazon Rekognition**: 5,000 free image analyses/month
   - **Amazon Cognito**: 50,000 free monthly active users (MAUs)
   - **Zero Idle Costs**: When no documents are being processed, cloud billing is exactly $0.00.
