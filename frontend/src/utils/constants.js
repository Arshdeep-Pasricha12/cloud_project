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
    label: 'Pending Review',
    description: 'Extracted; human review required',
    className: 'pending-review'
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

export const IMPLEMENTATION_PHASES = {
  AUTH: 'Amazon Cognito (Milestone 1)',
  S3_UPLOAD: 'Amazon S3 Presigned URL (Milestone 2)',
  API_GW: 'Amazon API Gateway (Milestone 3)',
  TEXTRACT: 'Amazon Textract AnalyzeExpense (Milestone 4)',
  DYNAMODB: 'Amazon DynamoDB Persistence (Milestone 5)',
  CORRECTIONS: 'Human-in-the-Loop Corrections (Milestone 6)'
};
