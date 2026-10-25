/**
 * Document processing lifecycle statuses and UI metadata
 */
export const DOCUMENT_STATUSES = {
  UPLOADED: {
    key: 'UPLOADED',
    label: 'Uploaded',
    description: 'Stored in S3; awaiting analysis',
    className: 'uploaded'
  },
  PROCESSING: {
    key: 'PROCESSING',
    label: 'Processing',
    description: 'Amazon Textract analyzing invoice data',
    className: 'processing'
  },
  PENDING_REVIEW: {
    key: 'PENDING_REVIEW',
    label: 'Needs review',
    description: 'Extracted; human review required',
    className: 'needs-review'
  },
  REVIEWED: {
    key: 'REVIEWED',
    label: 'Reviewed',
    description: 'Verified and corrections saved',
    className: 'reviewed'
  },
  FAILED: {
    key: 'FAILED',
    label: 'Failed',
    description: 'Extraction failed or unreadable file',
    className: 'failed'
  }
};

export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png'
];

export const MAX_FILE_SIZE_MB = 10;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export const SYSTEM_SERVICES = {
  AUTH: 'Amazon Cognito User Pool',
  S3_UPLOAD: 'Amazon S3 Encrypted Lake (AES-256)',
  API_GW: 'Amazon API Gateway REST API',
  TEXTRACT: 'Amazon Textract AnalyzeExpense AI',
  DYNAMODB: 'Amazon DynamoDB Document Store',
  CORRECTIONS: 'Audit & Human Verification Engine',
  MONITORING: 'Amazon CloudWatch Observability'
};

// Backward-compatible alias
export const IMPLEMENTATION_PHASES = SYSTEM_SERVICES;

