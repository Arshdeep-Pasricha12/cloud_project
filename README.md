# Serverless Document Intelligence Platform

An end-to-end cloud-native serverless web application designed to ingest real business documents (invoices, receipts), extract relevant financial data using **Amazon Textract (`AnalyzeExpense`)**, present extractions in an interactive human-in-the-loop dashboard, and persist verified corrections in **Amazon DynamoDB** while preserving raw extraction immutability.

Built as an enterprise-grade cloud architecture project for academic submission and practical deployment on Amazon Web Services.

---

## 1. System Architecture

```
                                    +-----------------------------------------+
                                    |         Amazon Cognito User Pool        |
                                    |         (JWT Authentication)            |
                                    +--------------------+--------------------+
                                                         |
                                            (JWT Bearer) |
                                                         v
[ React Dashboard (Vite) ]  ======>  [ Amazon API Gateway (REST API) ]
            |                                      |
            | (Direct Presigned PUT)               | Proxy
            v                                      v
 [ Amazon S3 Private Bucket ] <====== [ AWS Lambda Functions (Python 3.12) ]
                                                   |
                             +---------------------+---------------------+
                             |                     |                     |
                             v                     v                     v
                    [ Amazon Textract ]   [ Amazon DynamoDB ]   [ Amazon CloudWatch ]
                   (AnalyzeExpense API)    (Documents Table)     (Centralized Logs)
```

---

## 2. Technology Stack

- **Frontend**:
  - React 19 + Vite
  - React Router v7
  - Lucide React (Clean icon set)
  - Custom Vanilla CSS Design System (Glassmorphic dark aesthetic, Inter & Outfit typography, zero Tailwind)
- **Backend (Serverless Microservices)**:
  - Python 3.12 AWS Lambda functions
  - Amazon API Gateway (REST with Cognito Authorizer)
  - Amazon Cognito User Pools (Authentication & multi-tenant isolation)
  - Amazon S3 (Private document storage with short-lived presigned URLs)
  - Amazon Textract (`AnalyzeExpense` API for financial documents)
  - Amazon DynamoDB (On-Demand billing, immutable raw extraction + separate corrections)
  - Amazon CloudWatch (Logs and metrics)
- **Development & IaC Tooling**:
  - AWS CLI v2
  - Boto3
  - Pytest & Moto (AWS service mocking)
  - Node.js & npm

---

## 3. Directory Layout

```
cloud_project/ (document-intelligence-platform)
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/       # Reusable UI (Sidebar, Header, Metrics, Upload, Table, Badge)
│   │   ├── pages/            # Dashboard, Documents, Document Review, Settings
│   │   ├── services/         # API Gateway & S3 client abstraction (api.js)
│   │   ├── hooks/            # useDocuments state hook
│   │   ├── utils/            # Status enums, formatters, phase constants
│   │   ├── App.jsx           # Routing & layout shell
│   │   ├── main.jsx          # Entry point with BrowserRouter
│   │   └── index.css         # Design system tokens, glassmorphism, animations
│   ├── .env.example          # Placeholders for AWS credentials & endpoints (no secrets)
│   └── package.json
├── backend/
│   ├── shared/               # Shared response utils, CORS, Decimal encoder, models
│   ├── functions/
│   │   ├── create-upload/    # S3 presigned PUT URL generator
│   │   ├── process-document/ # Textract AnalyzeExpense worker & normalizer
│   │   ├── get-document/     # Document retrieval & presigned GET view URL
│   │   ├── list-documents/   # DynamoDB GSI user query & status aggregation
│   │   └── save-corrections/ # Immutability-preserving human corrections writer
│   ├── tests/                # Pytest unit tests for models and formatting
│   └── requirements.txt      # Python dependencies for local development
├── infrastructure/
│   └── README.md             # AWS serverless IaC specifications & resource definitions
├── docs/
│   ├── architecture.md       # High-level architecture, state machines, and data schemas
│   └── implementation-plan.md# Ordered milestones from local shell to production AWS
├── scripts/
│   └── README.md             # Deployment automation & helper scripts
├── .gitignore                # Node, Python, AWS, and environment files ignore rules
└── README.md                 # Project overview and setup guide
```

---

---

## 4. Live Production Endpoints & Cloud Resources

| Service | Cloud Resource | Description | Live Endpoint / Identifier |
| :--- | :--- | :--- | :--- |
| **Web Hosting** | Amazon S3 Static Website | Production Single-Page React App | **[Live Web App](http://doc-intelligence-frontend-399383129700.s3-website.ap-south-1.amazonaws.com)** |
| **Authentication** | Amazon Cognito User Pool | User Auth & JWT token issuance | `ap-south-1_ZIRwwnB44` (Client: `4ai8598ftdkf0fc2hm4bd1v75k`) |
| **API Gateway** | REST API (`doc-intelligence-api`) | Cognito Authorized REST routes | `https://wxgm03t7wc.execute-api.ap-south-1.amazonaws.com/prod` |
| **Document Storage** | Amazon S3 Private Bucket | Encrypted storage (`AES256`, CORS) | `doc-intelligence-uploads-399383129700` |
| **Document Database** | Amazon DynamoDB | On-Demand table with GSI | `doc-intelligence-documents` (`UserDocumentsIndex`) |
| **AI Extraction** | Amazon Textract | Financial document OCR pipeline | `AnalyzeExpense` API (asynchronous S3 trigger) |
| **Operations** | Amazon CloudWatch | Alarms, Metric Filters & Dashboard | **[Live Executive Dashboard](https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards/dashboard/doc-intelligence-dashboard)** |

---

## 5. Milestone Implementation Summary (All 8 Milestones Completed)

- [x] **Milestone 0: Project Shell & UI Foundation** — Vite React SPA with dark glassmorphism, responsive grid, dynamic navigation, and clean empty states.
- [x] **Milestone 1: Amazon Cognito Authentication** — User Pool (`ap-south-1_ZIRwwnB44`), Public SPA Client, email code verification, dynamic avatar, and session management.
- [x] **Milestone 2: S3 Document Ingestion & Presigned URLs** — Client validation, presigned PUT URL generation with cryptographic signature binding, direct binary transfer with progress tracking.
- [x] **Milestone 3: Amazon API Gateway & Cloud Lambda Deployment** — REST API (`wxgm03t7wc`), Cognito JWT Authorizer (`6i102z`), CORS preflight, and default gateway error responses.
- [x] **Milestone 4: Amazon Textract AI Extraction Pipeline** — Event-driven Lambda (`doc-intelligence-process-document`) triggered on `uploads/`, extraction normalizer with field confidence metrics.
- [x] **Milestone 5: Amazon DynamoDB Persistence & Query APIs** — Pay-per-request table with GSI (`UserDocumentsIndex`), `list-documents` calculating status metrics, `get-document` with presigned view URLs.
- [x] **Milestone 6: Human-in-the-Loop Corrections & Review UI** — Dual-pane review workstation (`DocumentReviewPage.jsx`), editable line items, raw extraction immutability guarantee (`rawExtraction` untouched, edits stored in `correctedData`).
- [x] **Milestone 7: Testing, Diagnostics & Observability** — 14-day CloudWatch log retention, metric filter (`DocumentProcessingErrors`), alarms, executive dashboard, and 36 backend + 18 frontend automated tests (100% pass rate).
- [x] **Milestone 8: Cloud Deployment & Presentation Prep** — Production S3 static website hosting, SPA routing fallback (`IndexDocument: index.html`, `ErrorDocument: index.html`), automated deployment script, and academic evaluation runbook ([`docs/college-presentation-guide.md`](docs/college-presentation-guide.md)).

---

## 6. Prerequisites

Ensure you have the following installed locally:
- **Node.js**: v18.0.0 or later (v22.17.0 tested)
- **npm**: v9.0.0 or later (v11.4.2 tested)
- **Python**: v3.10 or later (v3.12.4 tested)
- **AWS CLI v2**: For subsequent cloud deployment phases
- **Git**

---

## 7. Setup & Running Locally

### Step 1: Clone or Navigate to the Workspace
```powershell
cd "c:\Users\arshd\OneDrive - vit.ac.in\Desktop\cloud_project"
```

### Step 2: Install Frontend Dependencies
```powershell
cd frontend
npm install
```

### Step 3: Run the Frontend Development Server
```powershell
npm run dev
```
The application will start locally at **`http://localhost:5173`**. Open this URL in any modern browser.

### Step 4: Run Automated Tests
```powershell
# Run full backend test suite (36 tests passing: S3, DynamoDB, Textract & End-to-End Pipeline)
pytest backend/tests/ -v

# Run frontend test suite (18 tests passing: Auth, Upload & API Gateway integration)
cd frontend
npm test
```

### Academic & College Presentation Guide
A full evaluation runbook, architecture defense talking points, evaluator Q&A script, and live demonstration guide are available in [`docs/college-presentation-guide.md`](docs/college-presentation-guide.md).

### Step 5: Test Real S3 Uploads Locally via Local Lambda Bridge
```powershell
# 1. Set your bucket name and region
$env:DOCUMENTS_BUCKET_NAME="your-s3-bucket-name"
$env:AWS_REGION="us-east-1"

# 2. Start the local Lambda HTTP bridge
python scripts/run_local_backend.py

# 3. In frontend/.env, configure the endpoint:
# VITE_UPLOAD_API_URL=http://localhost:8000/documents/upload-url

# 4. Start frontend and upload documents from http://localhost:5173
cd frontend
npm run dev
```

### Step 6: Validate Production Build
To ensure that all components and CSS compile with zero warnings or errors:
```powershell
cd frontend
npm run build
```

---

## 8. AWS Security & Cost Principles

1. **Zero Secret Ingestion**: AWS access keys, passwords, and tokens are never embedded into frontend source code.
2. **Private S3 Buckets**: Public access block is strictly enabled. Client downloads and uploads use short-lived presigned URLs.
3. **Pay-Per-Request Serverless**: Zero fixed costs when idle; uses Lambda, S3, DynamoDB On-Demand, and API Gateway.
4. **Data Immutability Guard**: Original extraction snapshots from Textract are permanently stored in `rawExtraction` and never modified when users edit corrections.
