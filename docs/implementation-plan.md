# Serverless Document Intelligence Platform - Implementation Plan

This roadmap defines the ordered milestones to transition this project from the initial frontend shell into a production-grade, end-to-end AWS serverless application.

---

## Milestone Overview

| Milestone | Focus Area | Key AWS Services | Status |
| :--- | :--- | :--- | :--- |
| **Milestone 0** | Project Shell & Foundation | Local Vite React, Directory Structure, Documentation | **COMPLETED** |
| **Milestone 1** | Cognito User Authentication | Amazon Cognito User Pools, App Client | *Pending Approval* |
| **Milestone 2** | S3 Private Storage & Presigned Uploads | Amazon S3, Lambda (`create-upload`), IAM | *Upcoming* |
| **Milestone 3** | API Gateway Integration & Routing | Amazon API Gateway, Cognito Authorizer, CORS | *Upcoming* |
| **Milestone 4** | Textract AI Invoice Extraction Pipeline | Amazon Textract (`AnalyzeExpense`), Lambda (`process-document`) | *Upcoming* |
| **Milestone 5** | DynamoDB Persistence & Query APIs | Amazon DynamoDB, Lambda (`get-document`, `list-documents`) | *Upcoming* |
| **Milestone 6** | Human-in-the-Loop Corrections & Review UI | Lambda (`save-corrections`), React Review Dashboard | *Upcoming* |
| **Milestone 7** | End-to-End Testing, Validation & Diagnostics | Moto/Pytest, Frontend Testing, CloudWatch Dashboards | *Upcoming* |
| **Milestone 8** | Cloud Deployment & College Presentation Prep | S3 + CloudFront Hosting or AWS Amplify, Demo Runbook | *Upcoming* |

---

## Detailed Milestone Execution

### Milestone 0: Foundation & Shell (Current)
- [x] Workspace verification and Git repository initialization.
- [x] Standard serverless directory layout (`frontend`, `backend`, `infrastructure`, `docs`, `scripts`).
- [x] React + Vite application shell with dark-mode aesthetic, navigation sidebar, upload area, metrics counters, empty states, and document review placeholder.
- [x] `.env.example`, `.gitignore`, `backend/requirements.txt`, and architecture documentation.
- [x] Client build verification (`npm run build`).

---

### Milestone 1: User Authentication (Amazon Cognito)
**Objective**: Secure the application with user accounts, email verification, and JWT session management.
1. Create Amazon Cognito User Pool with email sign-in attribute and password complexity rules.
2. Configure App Client for SPA authentication (no client secret, SRP flow).
3. Implement lightweight authentication state provider in React (`useAuth` hook).
4. Build Sign In, Sign Up, and Confirm Account dialogs.
5. Store JWT access/id tokens in memory/secure storage for API authorization headers.
6. **Verification**: User can register an account, confirm email via verification code, sign in, and view their user profile in the dashboard header.

---

### Milestone 2: S3 Document Storage & Presigned Uploads
**Objective**: Enable browser-to-S3 direct uploads without routing large binary files through API Gateway.
1. Create private S3 bucket with strict Public Access Block and SSE-S3 encryption.
2. Configure bucket CORS for PUT/GET from frontend origin.
3. Implement `backend/functions/create-upload/handler.py` using Boto3 `generate_presigned_url('put_object', ...)`.
4. Enforce file size limit (10MB) and allowed MIME types (`application/pdf`, `image/jpeg`, `image/png`).
5. Wire frontend upload panel with drag-and-drop, progress bar, and presigned upload request.
6. **Verification**: Upload real PDF and image invoices directly to S3 and verify object creation in S3 private prefix.

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

### Milestone 7: Testing, Diagnostics & Observability
**Objective**: Complete automated unit/integration tests and CloudWatch monitoring.
1. Write backend pytest suite using `moto` for S3, DynamoDB, and Textract mocking.
2. Configure Amazon CloudWatch Logs with 14-day log retention.
3. Create CloudWatch Metric Filter to alert on `FAILED` processing events.
4. Frontend build optimization and responsive cross-browser testing.
5. **Verification**: 100% passing backend tests and clean CloudWatch log streams.

---

### Milestone 8: Deployment & Project Documentation
**Objective**: Deploy the full solution and prepare submission artifacts.
1. Script deployment using AWS CLI / SAM template.
2. Deploy frontend to S3 website bucket or AWS Amplify hosting.
3. Update README with live URLs, architecture diagram, cost breakdown, and video demonstration link.
4. Document test cases with real invoices demonstrating Textract extraction accuracy and reviewer correction tracking.
