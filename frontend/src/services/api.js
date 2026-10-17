/**
 * API Service Client for Serverless Document Intelligence Platform
 * Handles communication with Amazon API Gateway, Cognito, and direct S3 presigned URLs.
 * 
 * Note: Features will connect to real AWS endpoints once deployed in subsequent milestones.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const AWS_REGION = import.meta.env.VITE_AWS_REGION || '';

export const apiService = {
  isConfigured() {
    return Boolean(API_BASE_URL && !API_BASE_URL.includes('your-api-id'));
  },

  /**
   * Request a short-lived presigned PUT URL from Lambda create-upload
   * Scheduled: Milestone 2 & 3
   */
  async requestUploadUrl(fileName, contentType) {
    if (!this.isConfigured()) {
      throw new Error(
        'AWS API Gateway is not yet connected. Presigned upload URLs will be available in Milestone 2 & 3.'
      );
    }
    const response = await fetch(`${API_BASE_URL}/documents/upload-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fileName, contentType })
    });
    if (!response.ok) {
      throw new Error(`Failed to obtain upload URL: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Direct binary upload to Amazon S3 via presigned PUT URL
   * Scheduled: Milestone 2
   */
  async uploadFileToS3(uploadUrl, file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('PUT', uploadUrl, true);
      xhr.setRequestHeader('Content-Type', file.type);

      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            onProgress(percent);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(true);
        } else {
          reject(new Error(`S3 upload failed with status ${xhr.status}`));
        }
      };

      xhr.onerror = () => reject(new Error('Network error during S3 upload'));
      xhr.send(file);
    });
  },

  /**
   * Fetch documents list from DynamoDB via list-documents Lambda
   * Scheduled: Milestone 5
   */
  async listDocuments() {
    if (!this.isConfigured()) {
      // In initial phase: return genuine empty data state with 0 records
      return {
        items: [],
        metrics: {
          total: 0,
          processing: 0,
          pendingReview: 0,
          reviewed: 0
        }
      };
    }
    const response = await fetch(`${API_BASE_URL}/documents`);
    if (!response.ok) throw new Error('Failed to fetch documents');
    return response.json();
  },

  /**
   * Fetch single document detail from DynamoDB
   * Scheduled: Milestone 5
   */
  async getDocument(documentId) {
    if (!this.isConfigured()) {
      return null;
    }
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`);
    if (!response.ok) throw new Error('Failed to fetch document');
    return response.json();
  },

  /**
   * Save human-in-the-loop corrections to DynamoDB
   * Scheduled: Milestone 6
   */
  async saveCorrections(documentId, corrections) {
    if (!this.isConfigured()) {
      throw new Error('DynamoDB mutation service scheduled for Milestone 6.');
    }
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/corrections`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrections })
    });
    if (!response.ok) throw new Error('Failed to save corrections');
    return response.json();
  }
};
