# Serverless Document Intelligence Platform - Implementation Plan

This roadmap defines the ordered milestones to transition this project from the initial frontend shell into a production-grade, end-to-end AWS serverless application.

---

## Milestone Overview

| Milestone | Focus Area | Key AWS Services | Status |
| :--- | :--- | :--- | :--- |
| **Milestone 0** | Project Shell & Foundation | Local Vite React, Directory Structure, Documentation | **COMPLETED** |
| **Milestone 1** | Cognito User Authentication | Amazon Cognito User Pools, App Client | **COMPLETED** |
| **Milestone 2** | S3 Private Storage & Presigned Uploads | Amazon S3, Lambda (`create-upload`), IAM | **COMPLETED** |
| **Milestone 3** | API Gateway Integration & Routing | Amazon API Gateway, Cognito Authorizer, CORS | **COMPLETED** |
| **Milestone 4** | Textract AI Invoice Extraction Pipeline | Amazon Textract (`AnalyzeExpense`), Lambda (`process-document`) | **COMPLETED** |
| **Milestone 5** | DynamoDB Persistence & Query APIs | Amazon DynamoDB, Lambda (`get-document`, `list-documents`) | **COMPLETED** |
| **Milestone 6** | Human-in-the-Loop Corrections & Review UI | Lambda (`save-corrections`), React Review Dashboard | **COMPLETED** |
| **Milestone 7** | End-to-End Testing, Validation & Diagnostics | Moto/Pytest, Frontend Testing, CloudWatch Dashboards | **COMPLETED** |
| **Milestone 8** | Cloud Deployment & College Presentation Prep | S3 Website Hosting, Demo Runbook, Production URLs | **COMPLETED** |

---

## Detailed Milestone Execution

### Milestone 0: Foundation & Shell
- [x] Workspace verification and Git repository initialization.
- [x] Standard serverless directory layout (`frontend`, `backend`, `infrastructure`, `docs`, `scripts`).
- [x] React + Vite application shell with dark-mode aesthetic, navigation sidebar, upload area, metrics counters, empty states, and document review placeholder.
- [x] `.env.example`, `.gitignore`, `backend/requirements.txt`, and architecture documentation.
- [x] Client build verification (`npm run build`).

---

### Milestone 1: User Authentication (Amazon Cognito - Completed)
**Objective**: Secure the application with user accounts, email verification, and JWT session management.
- [x] Created Amazon Cognito User Pool `ap-south-1_ZIRwwnB44` in Mumbai (`ap-south-1`) with email sign-in attribute and password rules.
- [x] Configured Public SPA App Client `4ai8598ftdkf0fc2hm4bd1v75k` with `ALLOW_USER_PASSWORD_AUTH` and token refresh (no client secret).
- [x] Implemented zero-dependency `frontend/src/services/authService.js` communicating directly with Cognito IDP JSON 1.1 endpoints (`SignUp`, `ConfirmSignUp`, `InitiateAuth`, `ResendConfirmationCode`).
- [x] Built React `AuthContext` and `useAuth` hook managing user profiles, JWT tokens, and session expiration.
- [x] Built dark glassmorphic `AuthModal.jsx` supporting Sign In, Account Registration, and 6-digit confirmation code verification.
- [x] Updated application Header with dynamic user avatar, email badge, "Cognito Verified" indicator, and sign out controls.
- [x] Attached `Authorization: Bearer <token>` to upload requests in `uploadService.js`.
- [x] Automated frontend unit tests passing (14 tests in total).

---

### Milestone 2: S3 Document Storage & Presigned Uploads (Completed)
**Objective**: Enable browser-to-S3 direct uploads without routing large binary files through API Gateway.
- [x] Implemented `backend/functions/create-upload/handler.py` generating short-lived S3 presigned PUT URLs with Boto3.
- [x] Strict input validation for filename, MIME type (`application/pdf`, `image/jpeg`, `image/png`), and file size (10 MB limit).
- [x] Server-generated unique object keys: `uploads/{uuid}/{sanitized-filename}` with path-traversal prevention.
- [x] Pre-signed `Content-Type` header binding to ensure client cannot modify MIME type on PUT.
- [x] Created `frontend/src/services/uploadService.js` handling client validation, presigned URL acquisition, and direct binary S3 upload via XHR with progress tracking.
- [x] Enhanced `UploadPanel.jsx` with real progress bar, retry state on failure, unconfigured endpoint warning, and S3-confirmed success card.
- [x] Prepared infrastructure specifications in `infrastructure/` (`s3-cors.json`, `iam-lambda-upload-policy.json`, S3 setup runbook).
- [x] Unit test suites with 100% pass rate: 17 backend tests using `moto[s3]` and 14 frontend tests using Node test runner.
- [x] Created local Lambda HTTP bridge (`scripts/run_local_backend.py`) for live local testing.

---

### Milestone 3: Amazon API Gateway & Cognito Authorization
**Objective**: Expose REST endpoints with centralized CORS and token-based authorization.
1. Define API Gateway REST API with resources:
   - `POST /documents/upload-url`
   - `GET /documents`
   - `GET /documents/{id}`
   - `POST /documents/{id}/process`
   - `PUT /documents/{id}/corrections`
2. Configure Cognito User Pool Authorizer to inspect `Authorization: Bearer <token>` on all routes.
3. Configure API Gateway Gateway Responses for default CORS headers on 4xx/5xx responses.
4. Update frontend `services/api.js` to automatically attach current Cognito JWT tokens.
5. **Verification**: Unauthenticated requests receive HTTP 401; authenticated requests route successfully to Lambda handlers.

---

### Milestone 4: Textract Invoice Extraction Pipeline
**Objective**: Extract structured invoice data from uploaded documents using Amazon Textract `AnalyzeExpense`.
1. Configure IAM permissions for Lambda `process-document` allowing `textract:AnalyzeExpense` and `s3:GetObject`.
2. Implement Textract response parser to extract and normalize:
   - Vendor Name, Address, and Contact
   - Invoice Number, Invoice Date, Due Date
   - Subtotal, Tax Amount, Total Amount, Currency
   - Line Items (Description, Quantity, Unit Price, Total Price)
   - Field-level confidence scores (0-100%)
3. Create fallback/retry handling for multi-page documents or low-confidence scans.
4. **Verification**: Run real multi-vendor sample invoices through Textract and log normalized JSON extractions with confidence metrics.

---

### Milestone 5: DynamoDB Persistence & Listing API
**Objective**: Persist document metadata and normalized extractions; display them on the dashboard.
1. Create Amazon DynamoDB `Documents` table (Partition Key: `documentId`, GSI: `userId` + `createdAt`).
2. Persist document metadata upon upload with status `UPLOADED`.
3. Update record with `rawExtraction` and transition status to `PENDING_REVIEW` upon Textract completion.
4. Implement `backend/functions/list-documents/handler.py` and `get-document/handler.py`.
5. Connect frontend Dashboard recent documents table and summary metric cards to live DynamoDB queries.
6. **Verification**: Dashboard shows real document count, status badges, upload dates, and vendors without hardcoded mock data.

---

### Milestone 6: Editable Fields & Correction Workflow
**Objective**: Implement human-in-the-loop review, editable fields, confidence highlights, and separate correction persistence.
1. Build `pages/DocumentReview.jsx` with split-screen layout:
   - Left pane: Original document viewer (via short-lived presigned S3 GET URL).
   - Right pane: Form fields populated with extracted values, confidence indicators (<80% highlighted in amber/warning).
2. Allow editing of header fields and line items (add, edit, remove line items).
3. Implement `backend/functions/save-corrections/handler.py`:
   - Enforce immutability of `rawExtraction`.
   - Store edits in `correctedData` attribute.
   - Record `reviewedAt` timestamp and reviewer identity.
   - Update status to `REVIEWED`.
4. **Verification**: Correct a misread invoice field, save, reload page, and verify that `correctedData` holds new values while `rawExtraction` remains intact.

---

### Milestone 7: Testing, Diagnostics & Observability (COMPLETED)
**Objective**: Complete automated unit/integration tests and CloudWatch monitoring.
- [x] Comprehensive backend pytest suite using `moto` for S3, DynamoDB, and Textract mocking (`backend/tests/test_e2e_pipeline.py`).
- [x] Configured Amazon CloudWatch Logs with 14-day log retention across all 5 deployed Lambdas.
- [x] Created CloudWatch Metric Filters for tracking processing failures (`DocumentProcessingErrors`) and upload errors.
- [x] Configured CloudWatch Metric Alarms (`doc-intelligence-processing-errors-alarm`, `doc-intelligence-api-5xx-alarm`).
- [x] Enabled detailed CloudWatch metrics on Amazon API Gateway `prod` stage.
- [x] Deployed Executive CloudWatch Operations Dashboard (`doc-intelligence-dashboard`) in `ap-south-1`.
- [x] Frontend test suite expanded to 18 unit tests passing (100% pass rate).
- [x] End-to-end cloud health diagnostic script (`scripts/run_e2e_live_test.py`) with all green verification checks.
- [x] **Verification**: 36/36 backend tests and 18/18 frontend tests passing; clean CloudWatch logs.

---

### Milestone 8: Deployment & Project Documentation (COMPLETED)
**Objective**: Deploy the full solution and prepare submission artifacts.
- [x] Automated hosting deployment script (`scripts/deploy_milestone8_hosting.py`).
- [x] Deployed frontend SPA production bundle to Amazon S3 Static Website Hosting (`http://doc-intelligence-frontend-399383129700.s3-website.ap-south-1.amazonaws.com`).
- [x] Configured SPA client-side routing fallback (`IndexDocument: index.html`, `ErrorDocument: index.html`) and optimized Cache-Control headers.
- [x] Updated Amazon S3 document uploads bucket CORS with live website origins.
- [x] Updated master `README.md` with live production endpoints, full ASCII + Mermaid architecture diagrams, cost evaluation table, and evaluation presentation script.
- [x] Created `docs/college-presentation-guide.md` with evaluator walkthrough, defense talking points, and live demonstration sequence.
