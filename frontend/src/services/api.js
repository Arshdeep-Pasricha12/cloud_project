/**
 * API Service Client for Serverless Document Intelligence Platform
 * Handles communication with Amazon API Gateway, Cognito, DynamoDB, and direct S3 presigned URLs.
 */

import { 
  isUploadConfigured, 
  requestPresignedUrl, 
  uploadBinaryToS3, 
  executeDocumentUpload 
} from './uploadService.js';
import { authService } from './authService.js';

const getEnvVar = (key) => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[key]) {
    return import.meta.env[key];
  }
  if (typeof process !== 'undefined' && process.env && process.env[key]) {
    return process.env[key];
  }
  return '';
};

const API_BASE_URL = getEnvVar('VITE_API_BASE_URL') || '';
const AWS_REGION = getEnvVar('VITE_AWS_REGION') || '';

const getAuthHeaders = () => {
  const headers = { 'Content-Type': 'application/json' };
  try {
    const token = authService.getIdToken();
    if (token) {
      headers['Authorization'] = token;
    }
  } catch (e) {
    // continue unauthenticated if token not available
  }
  return headers;
};

export const apiService = {
  isConfigured() {
    return Boolean(API_BASE_URL && !API_BASE_URL.includes('your-api-id'));
  },

  isUploadConfigured() {
    return isUploadConfigured();
  },

  /**
   * Request a short-lived presigned PUT URL from Lambda create-upload
   */
  async requestUploadUrl(fileName, contentType, fileSize = 1024) {
    return requestPresignedUrl({ name: fileName, type: contentType, size: fileSize });
  },

  /**
   * Direct binary upload to Amazon S3 via presigned PUT URL
   */
  async uploadFileToS3(uploadUrl, file, onProgress) {
    return uploadBinaryToS3(uploadUrl, file, onProgress);
  },

  /**
   * Complete document upload flow
   */
  async executeUpload(file, options) {
    return executeDocumentUpload(file, options);
  },

  /**
   * Fetch documents list from DynamoDB via list-documents Lambda
   * Milestone 5: Real AWS DynamoDB Query
   */
  async listDocuments() {
    if (!this.isConfigured()) {
      return {
        items: [],
        metrics: { total: 0, processing: 0, pendingReview: 0, reviewed: 0 }
      };
    }
    const response = await fetch(`${API_BASE_URL}/documents`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.message || `Failed to fetch documents (HTTP ${response.status})`);
    }
    return response.json();
  },

  /**
   * Fetch single document detail from DynamoDB
   * Milestone 5: Real AWS DynamoDB Item Retrieval
   */
  async getDocument(documentId) {
    if (!this.isConfigured()) {
      return null;
    }
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.message || `Failed to fetch document (HTTP ${response.status})`);
    }
    return response.json();
  },

  /**
   * Save human-in-the-loop corrections to DynamoDB audit store
   */
  async saveCorrections(documentId, corrections) {
    if (!this.isConfigured()) {
      throw new Error('API Gateway base URL is not configured.');
    }
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/corrections`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ corrections })
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.message || 'Failed to save corrections');
    }
    return response.json();
  }
};

export { isUploadConfigured, requestPresignedUrl, uploadBinaryToS3, executeDocumentUpload };
