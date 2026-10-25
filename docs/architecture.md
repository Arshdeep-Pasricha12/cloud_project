# Serverless Document Intelligence Platform - Architecture Design

## 1. System Overview

The Serverless Document Intelligence Platform is an end-to-end cloud-native system designed to ingest invoices and business documents, extract key financial metadata using machine learning (Amazon Textract), present extraction confidence to human reviewers in an interactive dashboard, and preserve audit-ready corrections in DynamoDB.

```
       +-------------------------------------------------------------+
       |                     Presentation Tier                       |
       |  React + Vite SPA Dashboard (HTML5 / Vanilla CSS / Router)  |
       +------------------------------+------------------------------+
                                      |
                         HTTP / REST  |  Bearer JWT (Cognito)
                                      v
       +-------------------------------------------------------------+
       |                        API Gateway                          |
       |  Amazon API Gateway REST API with Cognito Authorizer + CORS |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                      Application Tier                       |
       |         AWS Lambda Microservices (Python 3.12)              |
       |  - create-upload: S3 Presigned URL Generator                |
       |  - process-document: Textract Dispatcher & Normalizer       |
       |  - get-document: Document Record & Presigned GET View       |
       |  - list-documents: Query by User Index & Metrics            |
       |  - save-corrections: Reviewer Mutation & Immutability Guard |
       +----+--------------------+--------------------+--------------+
            |                    |                    |
            v                    v                    v
+-----------------------+ +-------------+ +--------------------------+
|      Storage Tier     | |   AI / ML   | |      Database Tier       |
|    Amazon S3 Bucket   | |   Textract  | |     Amazon DynamoDB      |
|  (Private, SSE-S3)    | |AnalyzeExpens| |   (PAY_PER_REQUEST, GSI) |
+-----------------------+ +-------------+ +--------------------------+
```

---

## 2. Document Lifecycle State Machine

Documents transition through 5 explicit lifecycle states:

```
  [ Client Selects File ]
             |
             v
        (UPLOADED)  ---------> File uploaded directly to S3 via Presigned URL
             |
             v
       (PROCESSING) ---------> Textract AnalyzeExpense triggered; asynchronous/synchronous analysis
             |
             +-----------------------+
             |                       |
             v (Success)             v (Error / Unreadable)
      (PENDING_REVIEW)            (FAILED)
             |
     [ User Review & Edit ]
             |
             v
        (REVIEWED)  ---------> Corrections saved to separate DynamoDB attribute;
                               original extraction preserved intact.
```

---

## 3. Data Invariant & Schema Separation

To maintain audit compliance and model evaluation accuracy:
- **Raw Extraction (`rawExtraction`)**: Immutable snapshot of Textract's normalized fields, confidence scores, and bounding box coordinates. **Never overwritten** by user actions.
- **User Corrections (`correctedData`)**: Explicitly stores reviewer modifications, reviewer identity, review timestamp, and review notes.
- **Confidence Scoring**: Each extracted summary field includes Textract's confidence percentage (`0 - 100%`) so the UI can highlight low-confidence items for human inspection.

### Normalized Invoice Schema
```json
{
  "documentId": "uuid-v4",
  "userId": "cognito-sub-id",
  "fileName": "invoice-sample.pdf",
  "fileSizeBytes": 245120,
  "contentType": "application/pdf",
  "s3Key": "documents/usr-123/uuid-v4/invoice-sample.pdf",
  "status": "PENDING_REVIEW",
  "createdAt": "2026-10-17T10:00:00Z",
  "updatedAt": "2026-10-17T10:00:15Z",
  "rawExtraction": {
    "vendorName": { "value": "Acme Tools LLC", "confidence": 98.4 },
    "invoiceNumber": { "value": "INV-2026-09", "confidence": 95.1 },
    "invoiceDate": { "value": "2026-10-12", "confidence": 92.0 },
    "dueDate": { "value": "2026-11-12", "confidence": 88.5 },
    "totalAmount": { "value": 1420.50, "confidence": 99.1 },
    "taxAmount": { "value": 120.50, "confidence": 85.0 },
    "subtotal": { "value": 1300.00, "confidence": 91.2 },
    "lineItems": [
      {
        "description": "Enterprise Cloud Subscription",
        "quantity": 1,
        "unitPrice": 1300.00,
        "totalPrice": 1300.00,
        "confidence": 94.2
      }
    ]
  },
  "correctedData": null,
  "reviewedAt": null
}
```

---

## 4. Security & Least Privilege

1. **Authentication**: All endpoints require valid Amazon Cognito User Pool JWT Bearer tokens.
2. **Data Isolation**: Multi-tenant isolation enforced at the database query layer (`userId = requestContext.authorizer.claims.sub`). Users can never query or mutate documents belonging to another user.
3. **Private S3**: Bucket is strictly private with public access blocks. Clients only interact with S3 via time-limited (5-15 minute) presigned URLs generated on demand.
4. **IAM Least Privilege**: Each Lambda execution role possesses permissions only for its specific operation (e.g. `create-upload` only has `s3:PutObject` on user prefixes; `get-document` only has `dynamodb:GetItem` and `s3:GetObject`).

---

## 5. Production End-to-End Pipeline & Security Hardening

```
[ Browser / React SPA ] 
(Hosted on S3 Static Website)
      |
      | 1. Authenticate with Amazon Cognito User Pool (ap-south-1_ZIRwwnB44)
      |    Receives signed JWT ID & Access Tokens
      v
[ POST /documents/upload-url ] ----> [ Amazon API Gateway (wxgm03t7wc) ]
(Guarded by Cognito Authorizer)             |
                                            | 2. Validates JWT signature & extracts sub
                                            v
                                    [ Lambda: create-upload ]
                                            |
                                            | 3. Validates file metadata & sanitizes filename
                                            | 4. Boto3 generate_presigned_url('put_object')
                                            | 5. Persists initial record (status: UPLOADED) to DynamoDB
                                            v
[ Presigned PUT URL ] <---------------------+
      |
      | 6. Direct binary PUT with Content-Type header
      v
[ Amazon S3 Private Bucket ] (doc-intelligence-uploads-399383129700)
      |  - SSE-S3 AES-256 encryption at rest
      |  - Block Public Access strictly enabled
      |  - CORS enabled for frontend web origins
      |
      | 7. S3 ObjectCreated Event Notification
      v
[ Lambda: process-document ]
      |
      | 8. Calls Amazon Textract AnalyzeExpense
      | 9. Normalizes financial entities, computes line items & field confidence
      | 10. Updates DynamoDB document to PENDING_REVIEW (preserves original userId)
      v
[ Amazon DynamoDB ] (doc-intelligence-documents)
      |
      +-----> [ Lambda: list-documents ]  ---> GET /documents (User metrics & dashboard items)
      +-----> [ Lambda: get-document ]    ---> GET /documents/{id} (Presigned GET viewer URL)
      +-----> [ Lambda: save-corrections] ---> PUT /documents/{id}/corrections (Status: REVIEWED)
```

### Production Security Invariants
- **Cryptographic Content-Type Binding**: By including `ContentType` in the Boto3 presigned URL generation parameters, S3 verifies the client's `Content-Type` header against the URL signature. Any attempt to change the MIME type during upload is rejected with `HTTP 403 Forbidden` (`SignatureDoesNotMatch`).
- **Server-Generated Sanitized Keys**: The S3 key is constructed strictly as `uploads/{random-uuid}/{sanitized-filename}`. Path traversal characters (`../`, `..\`, `/`, `\`) and non-alphanumeric characters are stripped on the server side.
- **Short-Lived Expiration Windows**: Presigned PUT URLs expire after 300 seconds (5 minutes); presigned view GET URLs expire after 900 seconds (15 minutes).
- **Multi-Tenant JWT Scoping**: Every API request is verified by the API Gateway Cognito Authorizer. Handlers strictly isolate queries to the caller's unique `userId` (`requestContext.authorizer.claims.sub`).
- **Raw Data Immutability Guarantee**: AI extractions are stored permanently in `rawExtraction`. User modifications are stored in `correctedData` alongside `reviewer` and `reviewedAt` attributes.
- **Automated CloudWatch Observability**: 14-day log retention across all 5 Lambdas, custom Metric Filters for tracking processing failures, and unified operational dashboard.
