/**
 * S3 Document Upload Service
 * 
 * Handles client-side file validation, presigned PUT URL acquisition from Lambda,
 * and direct browser-to-S3 binary streaming with real-time progress tracking.
 * 
 * Never touches or exposes AWS access credentials.
 */

import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '../utils/constants.js';
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

const UPLOAD_API_URL = 
  getEnvVar('VITE_UPLOAD_API_URL') || 
  (getEnvVar('VITE_API_BASE_URL') ? `${getEnvVar('VITE_API_BASE_URL')}/documents/upload-url` : '');

/**
 * Check if the upload endpoint is explicitly configured with a non-placeholder URL.
 */
export function isUploadConfigured() {
  if (!UPLOAD_API_URL) return false;
  const isPlaceholder = 
    UPLOAD_API_URL.includes('your-api-id') || 
    UPLOAD_API_URL.includes('your-aws-region') ||
    UPLOAD_API_URL.includes('example.com');
  return !isPlaceholder;
}

/**
 * Get the configured upload API URL or empty string.
 */
export function getUploadApiUrl() {
  return UPLOAD_API_URL;
}

/**
 * Validate file against allowed MIME types and max size.
 * Returns { valid: boolean, error?: string }
 */
export function validateFile(file, maxSizeBytes = MAX_FILE_SIZE_BYTES) {
  if (!file) {
    return { valid: false, error: 'No file selected.' };
  }

  // Check file type
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    const typesList = 'PDF (.pdf), PNG (.png), and JPEG (.jpg, .jpeg)';
    return {
      valid: false,
      error: `Unsupported file type "${file.type || 'unknown'}". Allowed formats: ${typesList}.`
    };
  }

  // Check file size
  if (file.size <= 0) {
    return { valid: false, error: 'Selected file is empty (0 bytes).' };
  }

  if (file.size > maxSizeBytes) {
    const maxMb = (maxSizeBytes / (1024 * 1024)).toFixed(0);
    const actualMb = (file.size / (1024 * 1024)).toFixed(2);
    return {
      valid: false,
      error: `File size (${actualMb} MB) exceeds maximum allowed limit of ${maxMb} MB.`
    };
  }

  return { valid: true };
}

/**
 * Request a short-lived presigned PUT URL from the backend Lambda.
 * 
 * @param {File} file 
 * @returns {Promise<Object>} presigned upload descriptor
 */
export async function requestPresignedUrl(file) {
  if (!isUploadConfigured()) {
    throw new Error(
      'AWS Upload API is not yet configured. Please set VITE_UPLOAD_API_URL in your frontend .env file.'
    );
  }

  const payload = {
    fileName: file.name,
    contentType: file.type,
    fileSize: file.size
  };

  const headers = {
    'Content-Type': 'application/json'
  };

  let token = null;
  try {
    token = authService.getIdToken();
  } catch (e) {
    token = null;
  }

  if (!token) {
    throw new Error('Authentication required. Please sign in or register in the top-right header to upload documents.');
  }

  // AWS API Gateway Cognito User Pool Authorizer expects the raw JWT token
  headers['Authorization'] = token;

  let response;
  try {
    response = await fetch(UPLOAD_API_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
  } catch (netErr) {
    throw new Error(
      `Failed to connect to Upload API endpoint (${UPLOAD_API_URL}). Please verify backend is running and CORS is enabled: ${netErr.message}`
    );
  }

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMessage = result.message || result.error || `Server returned HTTP ${response.status} ${response.statusText}`;
    throw new Error(`Presigned URL request failed: ${errorMessage}`);
  }

  if (!result.uploadUrl || !result.s3Key) {
    throw new Error('Upload API response did not contain a valid presigned S3 upload URL.');
  }

  return result;
}

/**
 * Perform direct binary upload to S3 using the presigned PUT URL with progress reporting.
 * 
 * @param {string} uploadUrl 
 * @param {File} file 
 * @param {Function} onProgress callback receiving percentage (0-100)
 * @returns {Promise<Object>} upload confirmation
 */
export function uploadBinaryToS3(uploadUrl, file, onProgress = null) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.open('PUT', uploadUrl, true);
    // Crucial: Content-Type must strictly match what was signed in the presigned URL
    xhr.setRequestHeader('Content-Type', file.type);

    if (xhr.upload && typeof onProgress === 'function') {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.min(100, Math.round((event.loaded / event.total) * 100));
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      // S3 PUT returns 200 OK on success
      if (xhr.status >= 200 && xhr.status < 300) {
        const etag = xhr.getResponseHeader('ETag') || null;
        resolve({
          success: true,
          status: xhr.status,
          etag: etag ? etag.replace(/"/g, '') : null
        });
      } else if (xhr.status === 403) {
        reject(
          new Error(
            'S3 upload forbidden (HTTP 403). Verify that the S3 bucket CORS configuration permits PUT from this origin and that Content-Type matches the signed request.'
          )
        );
      } else {
        reject(
          new Error(
            `S3 upload failed with HTTP ${xhr.status}: ${xhr.statusText || 'Upload rejected'}`
          )
        );
      }
    };

    xhr.onerror = () => {
      reject(
        new Error(
          'Network error while uploading directly to S3. Ensure your S3 bucket has CORS enabled for PUT requests from http://localhost:5173.'
        )
      );
    };

    xhr.onabort = () => {
      reject(new Error('S3 document upload was cancelled.'));
    };

    xhr.send(file);
  });
}

/**
 * High-level orchestration for complete document upload lifecycle.
 * 
 * @param {File} file
 * @param {Object} options
 * @param {Function} options.onProgress (percent: number) => void
 * @param {Function} options.onStatusChange (status: 'validating'|'presigning'|'uploading'|'completed'|'failed') => void
 * @returns {Promise<Object>}
 */
export async function executeDocumentUpload(file, { onProgress = null, onStatusChange = null } = {}) {
  // 1. Client-side validation
  if (onStatusChange) onStatusChange('validating');
  const validation = validateFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  // 2. Request presigned URL from backend Lambda
  if (onStatusChange) onStatusChange('presigning');
  const presignData = await requestPresignedUrl(file);

  // 3. Upload binary to S3
  if (onStatusChange) onStatusChange('uploading');
  const s3Result = await uploadBinaryToS3(presignData.uploadUrl, file, onProgress);

  // 4. Return confirmed result
  if (onStatusChange) onStatusChange('completed');
  return {
    documentId: presignData.documentId,
    s3Key: presignData.s3Key,
    bucket: presignData.bucket,
    fileName: presignData.fileName || file.name,
    fileSizeBytes: file.size,
    contentType: file.type,
    etag: s3Result.etag,
    uploadedAt: new Date().toISOString()
  };
}
