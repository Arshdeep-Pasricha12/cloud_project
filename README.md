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

## 4. Current Functionality (Milestone 0 - Complete)

- [x] **Application Shell**: Full React + Vite application running in local development mode.
- [x] **Modern UI/UX**: Premium dark-mode interface with glassmorphic cards, responsive grid, and custom typography (Google Fonts Inter and Outfit).
- [x] **Navigation**: Dedicated routes for Dashboard (`/`), Document Repository (`/documents`), Document Review (`/review`), and AWS Configuration Settings (`/settings`).
- [x] **Genuine Empty States**: 
  - Summary metrics cards start at zero (`0` Total, `0` Processing, `0` Pending Review, `0` Reviewed).
  - Documents table renders an explicit empty state with no fake records or mocked data.
- [x] **File Ingestion Panel**: Interactive drag-and-drop zone with client-side file type (`.pdf, .jpg, .png`) and size validation (10 MB limit) with file selection preview.
- [x] **Document Review Workstation**: Split-screen dual pane layout with original document canvas placeholder and normalized invoice form fields (Vendor, Invoice #, Dates, Amounts, Line Items).
- [x] **Explicit Status Labelling**: Every component not yet connected to AWS is clearly tagged with its implementation milestone.

---

## 5. Features Not Yet Implemented (Scheduled Milestones)

| Feature | Target Milestone | Description |
| :--- | :--- | :--- |
| **Cognito User Authentication** | Milestone 1 | Sign in, registration, email confirmation, JWT session management |
| **S3 Presigned Direct Upload** | Milestone 2 | Generation of short-lived S3 PUT URLs and browser-to-bucket upload |
| **API Gateway Integration** | Milestone 3 | REST API routes with Cognito Authorizer and CORS |
| **Textract AnalyzeExpense** | Milestone 4 | Automatic invoice OCR extraction and normalization |
| **DynamoDB Persistence** | Milestone 5 | Document records storage and querying via user GSI index |
| **Human-in-the-Loop Corrections**| Milestone 6 | Editable form with confidence highlighting and separate correction storage |
| **Testing & Observability** | Milestone 7 | Automated pytest suite with Moto, CloudWatch log retention |
| **Cloud Deployment** | Milestone 8 | AWS production hosting and submission runbook |

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

### Step 4: Validate Production Build
To ensure that all components and CSS compile with zero warnings or errors:
```powershell
npm run build
```

---

## 8. AWS Security & Cost Principles

1. **Zero Secret Ingestion**: AWS access keys, passwords, and tokens are never embedded into frontend source code.
2. **Private S3 Buckets**: Public access block is strictly enabled. Client downloads and uploads use short-lived presigned URLs.
3. **Pay-Per-Request Serverless**: Zero fixed costs when idle; uses Lambda, S3, DynamoDB On-Demand, and API Gateway.
4. **Data Immutability Guard**: Original extraction snapshots from Textract are permanently stored in `rawExtraction` and never modified when users edit corrections.
