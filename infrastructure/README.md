# AWS Infrastructure & S3 Configuration Guide (Milestone 2)

This document provides instructions for configuring and provisioning the private Amazon S3 document storage bucket and IAM permissions for **Milestone 2: Real Document Uploads**.

> [!IMPORTANT]
> **No AWS charges are incurred automatically.** Follow these manual setup steps only when you are ready to test against your real AWS account.

---

## 1. Security Architecture & Invariants

| Security Control | Implementation |
| :--- | :--- |
| **S3 Public Access** | **All 4 Block Public Access settings enabled** (`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`). Anonymous reads/writes strictly rejected. |
| **Object Ownership** | **BucketOwnerEnforced** (ACLs disabled). All objects uploaded are owned exclusively by the bucket owner account. |
| **Encryption at Rest** | **Server-Side Encryption with Amazon S3 managed keys (`AES256`)** applied automatically to all objects. |
| **IAM Scope** | Execution role is strictly constrained to `s3:PutObject` on the `uploads/*` key prefix. |
| **Upload Keys** | Server-generated unique key path: `uploads/{random-uuid}/{sanitized-filename}` preventing collisions and path traversal. |
| **Presigned Expiration** | **300 seconds (5 minutes)** short-lived window. Content-Type is cryptographically bound to the URL signature. |

---

## 2. Step-by-Step AWS Setup Instructions

### Step 1: Set Variables in PowerShell or Bash
```powershell
# Set your chosen bucket name and region
$BUCKET_NAME="doc-intelligence-uploads-$(Get-Random)"
$AWS_REGION="us-east-1"
```

### Step 2: Create the Private S3 Bucket
```powershell
# Create the bucket (add LocationConstraint if outside us-east-1)
aws s3api create-bucket --bucket $BUCKET_NAME --region $AWS_REGION

# Enable strict Block Public Access
aws s3api put-public-access-block `
    --bucket $BUCKET_NAME `
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enforce BucketOwnerEnforced ownership (disables ACLs)
aws s3api put-bucket-ownership-controls `
    --bucket $BUCKET_NAME `
    --ownership-controls="Rules=[{ObjectOwnership=BucketOwnerEnforced}]"

# Enforce default encryption at rest (SSE-S3 AES256)
aws s3api put-bucket-encryption `
    --bucket $BUCKET_NAME `
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

### Step 3: Apply CORS Configuration
The bucket must accept `PUT` requests directly from your local React development server (`http://localhost:5173`).

Apply the provided configuration file ([s3-cors.json](file:///c:/Users/arshd/OneDrive%20-%20vit.ac.in/Desktop/cloud_project/infrastructure/s3-cors.json)):
```powershell
aws s3api put-bucket-cors `
    --bucket $BUCKET_NAME `
    --cors-configuration file://infrastructure/s3-cors.json
```

---

## 3. IAM Execution Role for Lambda

When deploying the Lambda function on AWS, create an execution role with the narrowly scoped policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3PresignedPutOnUploadsPrefix",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/uploads/*"
    },
    {
      "Sid": "AllowCloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/create-upload:*"
    }
  ]
}
```

---

## 4. Local Testing with Real AWS S3

You can test the full end-to-end upload flow locally using your real AWS S3 bucket:

1. **Configure Environment Variables**:
   ```powershell
   $env:DOCUMENTS_BUCKET_NAME="your-actual-bucket-name"
   $env:AWS_REGION="us-east-1"
   ```

2. **Start the Local Lambda Bridge**:
   ```powershell
   python scripts/run_local_backend.py
   ```
   This exposes `POST http://localhost:8000/documents/upload-url` executing your real `create-upload` handler.

3. **Configure the Frontend**:
   In `frontend/.env`:
   ```bash
   VITE_UPLOAD_API_URL=http://localhost:8000/documents/upload-url
   ```

4. **Upload a Real Invoice**:
   Open `http://localhost:5173`, choose a sample PDF or PNG invoice, and click **Upload to S3**.

5. **Verify the Object in S3**:
   ```powershell
   aws s3 ls s3://$BUCKET_NAME/uploads/ --recursive
   ```

---

## 5. Security Limitations (Development Milestone Notice)

> [!WARNING]
> **Pre-Authentication Security Limitations**:
> 1. **No User Authentication**: For Milestone 2, the endpoint assigns a placeholder identity (`dev-anonymous-user`). Anyone with network access to the endpoint can request a presigned PUT URL. Amazon Cognito User Pool authentication (Milestone 1/3) will restrict access in the next phase.
> 2. **Client-Declared Metadata**: A presigned PUT URL validates that the client's `Content-Type` header matches what was signed. However, S3 PUT URLs cannot verify file magic bytes or enforce strict file-size limits on S3 at the exact time of transfer. In subsequent milestones, an S3 event-driven Lambda will inspect uploaded files, verify file headers, and reject any spoofed files.

---

## 6. Resource Cleanup & Deletion

To prevent any ongoing storage charges after testing:

```powershell
# 1. Empty all objects in the bucket
aws s3 rm s3://$BUCKET_NAME --recursive

# 2. Delete the bucket
aws s3api delete-bucket --bucket $BUCKET_NAME --region $AWS_REGION
```
