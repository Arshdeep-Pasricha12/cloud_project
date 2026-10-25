# Serverless Document Intelligence Platform
## Comprehensive Academic Presentation & Evaluation Guide

This guide is designed for presentation, viva voce defense, and college project evaluation. It covers the technical architecture, problem statement, live demonstration script, and answers to expected evaluator questions.

---

## 1. Project Overview & Metadata

- **Project Title:** Serverless Document Intelligence Platform
- **Domain:** Cloud Computing, Serverless Microservices & Artificial Intelligence
- **Primary Cloud Provider:** Amazon Web Services (AWS)
- **Deployment Region:** Asia Pacific — Mumbai (`ap-south-1`)
- **AWS Account ID:** `399383129700`
- **Live Production URL:** [http://doc-intelligence-frontend-399383129700.s3-website.ap-south-1.amazonaws.com](http://doc-intelligence-frontend-399383129700.s3-website.ap-south-1.amazonaws.com)
- **CloudWatch Dashboard:** [Live Executive Dashboard](https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards/dashboard/doc-intelligence-dashboard)
- **API Gateway REST Endpoint:** `https://wxgm03t7wc.execute-api.ap-south-1.amazonaws.com/prod`

---

## 2. Problem Statement & Motivation

Traditional enterprise invoice and document processing suffers from significant operational bottlenecks:
1. **Manual Data Entry:** Accounts payable teams spend hours manually re-keying invoice numbers, line item prices, vendor details, and tax amounts into ERP systems.
2. **High Error Rates:** Manual entry introduces frequent transcription errors, resulting in payment discrepancies and audit compliance failures.
3. **Legacy Monolithic Infrastructure:** Traditional OCR systems run on continuously provisioned virtual machines (EC2), incurring substantial idle compute costs 24/7 even during zero-traffic windows.
4. **Lack of Auditability:** Most automated OCR tools directly overwrite extracted data upon user correction, destroying the historical extraction trail required for financial compliance.

### The Solution:
A **100% Serverless Cloud-Native Architecture** that ingests invoices, extracts structured financial entities using **Amazon Textract**, highlights low-confidence fields (<80%) for human verification, and persists corrections in **Amazon DynamoDB** while strictly guaranteeing **raw data immutability**.

---

## 3. High-Level Architecture & Data Flow

```
                                +-----------------------------------+
                                |    Amazon Cognito User Pool       |
                                |   (JWT User Auth & Isolation)     |
                                +-----------------+-----------------+
                                                  |
                                     Authorization| Token
                                                  v
[ SPA Client ] ====================> [ Amazon API Gateway ]
(S3 Static Web Hosting)                         |
      |                                         | Proxies authenticated requests
      | 1. Direct Presigned PUT                 v
      v                               [ AWS Lambda Functions ]
[ Amazon S3 Private Bucket ]                   | (Python 3.12 Microservices)
      |                                        |
      | 2. S3 ObjectCreated Trigger            +--------------------+--------------------+
      v                                        |                    |                    |
[ doc-intelligence-process-document ]          v                    v                    v
      |                              [ Amazon Textract ]   [ Amazon DynamoDB ]  [ Amazon CloudWatch ]
      +----------------------------> (AnalyzeExpense API)  (Documents Table)    (Dashboard & Alarms)
```

### End-to-End Workflow Stages:
1. **User Authentication:** User registers or logs in via Amazon Cognito User Pool. The client receives signed JWT ID and Access tokens.
2. **Presigned Upload (Zero Server Load):** The client requests a presigned PUT URL from `doc-intelligence-create-upload`. The Lambda binds the cryptographic signature to the file MIME type and sets a 5-minute expiration. The client streams binary bytes directly to Amazon S3 (bypassing API Gateway limits).
3. **Event-Driven AI Extraction:** S3 emits an `ObjectCreated` event that triggers `doc-intelligence-process-document`. The function calls Amazon Textract (`AnalyzeExpense`), parses line items, calculates average confidence metrics, flags low-confidence values (<80%), and updates DynamoDB to `PENDING_REVIEW`.
4. **Human-in-the-Loop Review:** The user views their documents via `GET /documents`, clicks on an invoice, and opens the split-screen verification workstation (embedded PDF preview on left, editable form on right).
5. **Immutable Persistence:** When corrections are submitted via `PUT /documents/{id}/corrections`, the Lambda records edits in `correctedData`, writes reviewer identity and timestamp, and transitions status to `REVIEWED` while preserving `rawExtraction` untouched.
6. **Centralized Observability:** CloudWatch Metric Filters track errors, alarms notify operators, and a unified executive dashboard monitors latency, throughput, and error rates.

---

## 4. Key Technical Innovations

| Innovation | Implementation Detail | Technical Advantage |
| :--- | :--- | :--- |
| **Direct S3 Presigned Uploads** | Short-lived (300s) presigned PUT URLs with cryptographic `Content-Type` binding | Completely eliminates API Gateway 10MB payload limit; reduces Lambda execution duration to <200ms; saves bandwidth. |
| **Data Immutability Guarantee** | Dual-attribute schema (`rawExtraction` vs `correctedData`) in DynamoDB | Preserves exact AI baseline for auditability and compliance; captures human changes separately with reviewer attribution. |
| **Event-Driven Asynchronous AI** | S3 `s3:ObjectCreated:*` event triggers Lambda | Fully decoupled; client does not hang waiting for ML processing; handles spikes in document uploads without server crashes. |
| **Multi-Tenant Security Isolation** | Cognito `sub` claims enforced at API Gateway and verified in every Lambda handler | Zero possibility of cross-tenant data leakage; User B cannot read or modify User A's uploaded documents. |
| **Adaptive Decimal Handling** | Custom `_to_dynamo_safe` recursive converter + `DecimalEncoder` | Resolves Boto3 DynamoDB float serialization constraints without precision loss on financial amounts. |
| **CloudWatch Observability Suite** | 14-day log retention, custom metric filters (`DocumentProcessingErrors`), and executive dashboard | Eliminates indefinite log storage costs; enables real-time operations monitoring and alert thresholds. |

---

## 5. Live Demonstration Script (Step-by-Step)

Follow this step-by-step sequence during your presentation:

### Step 1: Access the Production Website
- Open [http://doc-intelligence-frontend-399383129700.s3-website.ap-south-1.amazonaws.com](http://doc-intelligence-frontend-399383129700.s3-website.ap-south-1.amazonaws.com) in your browser.
- Point out the **dark glassmorphic design system**, custom typography, and zero-framework Vanilla CSS styling.

### Step 2: Demonstrate Cognito Authentication
- Click **Sign In** in the top navigation bar.
- Log in with verified credentials (`arshdeepforwork@gmail.com`).
- Highlight:
  - Dynamic user avatar and email badge.
  - "Cognito Verified" security indicator in the header.
  - Session tokens stored securely with automatic expiration handling.

### Step 3: Ingest a Real Invoice Document
- Navigate to the **Upload Document** card.
- Select a sample invoice (e.g., `sample_documents/sample_techcorp_invoice.pdf`).
- Click **Upload to S3**.
- Point out:
  - Real-time upload progress bar.
  - The direct browser-to-S3 binary transfer via cryptographic presigned PUT URL.
  - S3 ObjectCreated event triggering automated Textract processing in the background.

### Step 4: Explore the Real-Time Dashboard
- Navigate to the **Dashboard** page.
- Show the live metrics counters:
  - **Total Documents**, **Pending Review**, **Reviewed**, **Failed**.
- Point out that these counters are dynamically aggregated from Amazon DynamoDB via the Global Secondary Index (`UserDocumentsIndex`), with **zero hardcoded mock data**.

### Step 5: Conduct Human-in-the-Loop Review & Corrections
- Click **Review** on the uploaded invoice to launch the **Document Verification Workstation**.
- Point out the dual-pane interface:
  - **Left Pane:** Embedded document viewer rendering the original invoice via a short-lived presigned S3 GET URL (15-minute expiration).
  - **Right Pane:** Extracted summary fields (Vendor Name, Invoice #, Invoice Date, Due Date, Total Amount) and Line Items table.
  - **Confidence Badges:** Any field extracted with <80% confidence is highlighted with an amber alert badge.
- Edit a field (e.g., correct a vendor name or add a line item).
- Add an auditor note in the Reviewer Notes field.
- Click **Approve & Save Corrections**.
- Show the confirmed state transition to `REVIEWED`.

### Step 6: Verify Data Immutability
- Explain to the evaluators:
  - The `rawExtraction` attribute in DynamoDB still contains the original machine output.
  - The `correctedData` attribute contains the reviewer's approved edits.
  - The audit record includes `reviewedBy` and `reviewedAt` timestamps.

### Step 7: Showcase CloudWatch Observability
- Open the [CloudWatch Operations Dashboard](https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards/dashboard/doc-intelligence-dashboard).
- Show evaluators:
  - Live Lambda invocation and duration metrics across all 5 functions.
  - API Gateway request volume and error rates.
  - Custom application metrics (`ProcessDocumentErrors`) powered by Metric Filters.
  - Live exception and error log stream widget.

---

## 6. Expected Evaluator Questions & Model Answers

### Q1: Why did you choose Serverless over containerized services (ECS/EKS) or EC2?
> **Answer:**  
> For document processing workloads, traffic is inherently bursty—invoices arrive in batches at month-end or during business hours, followed by long periods of zero activity. An EC2 instance or ECS cluster would incur continuous 24/7 compute charges while sitting idle. Serverless (AWS Lambda + S3 + API Gateway) scales automatically to zero when idle ($0 cost) and scales instantaneously to handle hundreds of concurrent uploads without provisioning or operating system maintenance.

### Q2: Why don't you send the document directly through API Gateway in the POST request body?
> **Answer:**  
> API Gateway has a strict maximum payload size limit of 10 MB. In addition, routing large binary files through API Gateway and Lambda consumes Lambda execution memory and duration, incurring unnecessary compute and bandwidth costs. By using **Amazon S3 Presigned URLs**, the client obtains a signed temporary URL and streams binary data directly into S3 via HTTP PUT. The Lambda function merely generates the signed URL, taking less than 150 ms and keeping costs at a fraction of a cent.

### Q3: How do you guarantee multi-tenant security if all documents are stored in the same DynamoDB table?
> **Answer:**  
> We enforce multi-tenant isolation at three defense-in-depth levels:
> 1. **Authentication Level:** Amazon Cognito User Pool validates credentials and issues a cryptographically signed JWT token containing the user's immutable unique subject identifier (`sub`).
> 2. **API Gateway Level:** The Cognito Authorizer validates the JWT signature on every incoming HTTP request before passing it to Lambda.
> 3. **Application Level:** Each Lambda handler extracts `sub` directly from `requestContext.authorizer.claims`. Queries to DynamoDB use the Global Secondary Index (`UserDocumentsIndex`) partitioned strictly by `userId`. In `get-document` and `save-corrections`, if a user attempts to access a document where `item.userId != claims.sub`, the handler immediately aborts with `HTTP 403 Forbidden`.

### Q4: What happens if Textract misreads an invoice? How do you prevent data loss?
> **Answer:**  
> We implemented a **Human-in-the-Loop (HITL)** architecture:
> 1. Textract returns a confidence score (0–100%) for every detected field and line item. Our normalizer automatically flags any field below 80% confidence as `lowConfidence`.
> 2. In the UI, low-confidence fields are visually highlighted in amber with warning badges.
> 3. An auditor can manually correct any value in the review workstation.
> 4. To satisfy enterprise auditing standards, we maintain **data immutability**: the original OCR output is preserved in `rawExtraction`, and human corrections are stored separately in `correctedData` alongside the reviewer's identity and timestamp.

### Q5: How do you handle DynamoDB decimal serialization in Python?
> **Answer:**  
> Boto3's DynamoDB resource internally rejects Python `float` types to prevent floating-point rounding inaccuracies in financial calculations. We implemented a recursive converter (`_to_dynamo_safe`) that safely converts all Python floats into `decimal.Decimal(str(val))` before writing to DynamoDB, and a custom `DecimalEncoder` when serializing DynamoDB records back to JSON for HTTP responses.

---

## 7. Cost Analysis & AWS Free Tier Evaluation

This architecture is optimized to run entirely within the **AWS Free Tier** for academic projects and small business pilots:

| AWS Service | Free Tier Monthly Allowance | Project Usage Estimate | Estimated Monthly Cost |
| :--- | :--- | :--- | :--- |
| **Amazon Cognito** | 50,000 Monthly Active Users (MAU) | < 100 users | **$0.00** (Free) |
| **AWS Lambda** | 1,000,000 free requests + 3.2M sec compute | ~10,000 requests | **$0.00** (Free) |
| **Amazon S3** | 5 GB Standard Storage + 20,000 GETs | < 500 MB storage | **$0.00** (Free) |
| **Amazon DynamoDB** | 25 GB Storage + 25 WCU / 25 RCU (On-Demand) | < 10 MB storage | **$0.00** (Free) |
| **Amazon API Gateway** | 1,000,000 REST API calls | ~20,000 calls | **$0.00** (Free) |
| **Amazon CloudWatch** | 10 custom metrics + 5 GB log ingestion | 3 custom metrics, 14-day retention | **$0.00** (Free) |
| **Amazon Textract** | 1,000 pages / month (AnalyzeExpense free tier) | ~50 test invoices | **$0.00** (Free) |
| **Total Estimated Cost** | — | — | **$0.00 / month** |

---

## 8. Automated Test Verification Summary

The platform includes two automated test suites guaranteeing code quality and multi-service reliability:

1. **Backend Integration & Unit Tests:**
   - Framework: `pytest` + `moto` (S3, DynamoDB)
   - Test Count: **36 / 36 Passing**
   - Execution command: `pytest backend/tests/ -v`

2. **Frontend Unit Tests:**
   - Framework: Node.js Test Runner (`node --test`)
   - Test Count: **18 / 18 Passing**
   - Execution command: `cd frontend && npm test`

3. **Cloud Infrastructure Health Diagnostic:**
   - Live execution against AWS Mumbai (`ap-south-1`):
   - Command: `python scripts/run_e2e_live_test.py`
   - Result: **All 19 Cloud Checks Passed**.
