# AWS Infrastructure Architecture & Deployment Guide

This directory will contain the Infrastructure-as-Code (IaC) templates and configuration scripts for deploying the Serverless Document Intelligence Platform onto Amazon Web Services.

> **Status Notice**: In compliance with the project rules, **NO AWS resources have been created or deployed yet**. All resources described below are specifications for future implementation phases.

---

## Target AWS Serverless Architecture

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

## AWS Resource Specifications

### 1. Amazon S3 (Document Storage)
- **Bucket Configuration**: Private bucket, `BlockPublicAcls: true`, `BlockPublicPolicy: true`, `IgnorePublicAcls: true`, `RestrictPublicBuckets: true`.
- **Encryption**: Server-side encryption with AWS KMS or AES-256 (`aws:kms` or `AES256`).
- **CORS Configuration**: Allow `PUT`, `GET`, `HEAD` methods from the frontend origin, exposing `ETag` header.
- **Lifecycle Policy**: Optional transition of old documents to S3 Glacier Flexible Retrieval for cost optimization.

### 2. Amazon Cognito (Authentication)
- **User Pool**: Self-service user registration with email verification.
- **App Client**: Public client for React SPA (no client secret, SRP auth flow enabled).
- **Token Verification**: API Gateway Cognito Authorizer validating JWT `id_token` or `access_token`.

### 3. Amazon DynamoDB (`Documents` Table)
- **Billing Mode**: On-Demand (`PAY_PER_REQUEST`) for zero idle cost.
- **Primary Key**:
  - Partition Key: `documentId` (String, UUID v4)
- **Global Secondary Index (GSI)**:
  - Name: `UserIdIndex`
  - Partition Key: `userId` (String)
  - Sort Key: `createdAt` (String, ISO 8601)
- **Attributes**:
  - `documentId`, `userId`, `fileName`, `s3Key`, `contentType`, `fileSizeBytes`
  - `status`: `UPLOADED` | `PROCESSING` | `PENDING_REVIEW` | `REVIEWED` | `FAILED`
  - `rawExtraction`: Immutable snapshot of Textract AnalyzeExpense normalized output
  - `correctedData`: User-edited invoice fields (never overwrites raw extraction)
  - `createdAt`, `updatedAt`, `reviewedAt`

### 4. AWS Lambda Functions (Python 3.12 Serverless)
- `create-upload`: Generates presigned S3 PUT URL for valid document mime types.
- `process-document`: Triggers Amazon Textract AnalyzeExpense, parses output, writes initial DynamoDB record.
- `get-document`: Fetches document extraction, corrections, and signed view URL.
- `list-documents`: Queries documents by user via GSI with status filters and summary counts.
- `save-corrections`: Validates and saves user corrections, updates document status to `REVIEWED`.

### 5. Amazon API Gateway
- REST API with CORS headers configured.
- Cognito User Pool Authorizer on all protected routes:
  - `POST /documents/upload-url`
  - `POST /documents/{id}/process`
  - `GET /documents`
  - `GET /documents/{id}`
  - `PUT /documents/{id}/corrections`

### 6. Amazon CloudWatch
- Dedicated Log Group per Lambda function with 14-day retention to prevent unbounded storage costs.
- Custom metric filters for extraction failures and latency diagnostics.
