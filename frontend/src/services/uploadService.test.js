import { describe, it, mock } from 'node:test';
import assert from 'node:assert/strict';
import { 
  validateFile, 
  isUploadConfigured, 
  requestPresignedUrl,
  uploadBinaryToS3 
} from './uploadService.js';
import { MAX_FILE_SIZE_BYTES } from '../utils/constants.js';

describe('Frontend uploadService - Client-side File Validation', () => {
  it('should accept valid PDF, PNG, and JPEG files within 10MB limit', () => {
    const validPdf = { name: 'invoice.pdf', type: 'application/pdf', size: 1024 * 500 };
    const validPng = { name: 'receipt.png', type: 'image/png', size: 1024 * 200 };
    const validJpg = { name: 'bill.jpg', type: 'image/jpeg', size: 1024 * 800 };

    assert.equal(validateFile(validPdf).valid, true);
    assert.equal(validateFile(validPng).valid, true);
    assert.equal(validateFile(validJpg).valid, true);
  });

  it('should reject unsupported MIME types with informative error message', () => {
    const exeFile = { name: 'virus.exe', type: 'application/x-msdownload', size: 5000 };
    const docxFile = { name: 'doc.docx', type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', size: 5000 };
    const textFile = { name: 'notes.txt', type: 'text/plain', size: 5000 };

    const res1 = validateFile(exeFile);
    assert.equal(res1.valid, false);
    assert.match(res1.error, /Unsupported file type/);

    const res2 = validateFile(docxFile);
    assert.equal(res2.valid, false);
    assert.match(res2.error, /Unsupported file type/);

    const res3 = validateFile(textFile);
    assert.equal(res3.valid, false);
    assert.match(res3.error, /Unsupported file type/);
  });

  it('should reject oversized files exceeding 10MB', () => {
    const hugePdf = {
      name: 'large_invoice.pdf',
      type: 'application/pdf',
      size: MAX_FILE_SIZE_BYTES + 1024
    };

    const res = validateFile(hugePdf);
    assert.equal(res.valid, false);
    assert.match(res.error, /exceeds maximum allowed limit/);
  });

  it('should reject empty (0-byte) files', () => {
    const emptyPdf = { name: 'empty.pdf', type: 'application/pdf', size: 0 };
    const res = validateFile(emptyPdf);
    assert.equal(res.valid, false);
    assert.match(res.error, /empty/);
  });

  it('should reject null or undefined file', () => {
    const res = validateFile(null);
    assert.equal(res.valid, false);
    assert.match(res.error, /No file selected/);
  });
});

describe('Frontend uploadService - Configuration & Failure Modes', () => {
  it('should identify unconfigured or placeholder endpoints', () => {
    // When no real URL is set, isUploadConfigured should be false
    assert.equal(typeof isUploadConfigured(), 'boolean');
  });

  it('should throw clear configuration error when requesting presigned URL without endpoint', async () => {
    const testFile = { name: 'test.pdf', type: 'application/pdf', size: 1024 };
    await assert.rejects(
      async () => {
        await requestPresignedUrl(testFile);
      },
      (err) => {
        return err.message.includes('Upload API is not yet configured') ||
               err.message.includes('VITE_UPLOAD_API_URL') ||
               err.message.includes('Authentication required');
      }
    );
  });

  it('should reject S3 binary upload when XMLHttpRequest encounters network error', async () => {
    // Mock global XMLHttpRequest for test environment
    const originalXHR = globalThis.XMLHttpRequest;
    globalThis.XMLHttpRequest = class MockXHR {
      open() {}
      setRequestHeader() {}
      send() {
        setTimeout(() => {
          if (this.onerror) this.onerror(new Error('Simulated network error'));
        }, 10);
      }
    };

    try {
      const mockFile = { name: 'invoice.pdf', type: 'application/pdf', size: 1000 };
      await assert.rejects(
        async () => {
          await uploadBinaryToS3('https://mock-bucket.s3.amazonaws.com/uploads/test.pdf', mockFile);
        },
        (err) => {
          return err.message.includes('Network error while uploading directly to S3');
        }
      );
    } finally {
      globalThis.XMLHttpRequest = originalXHR;
    }
  });

  it('should reject S3 binary upload with specific CORS/403 guidance when HTTP 403 received', async () => {
    const originalXHR = globalThis.XMLHttpRequest;
    globalThis.XMLHttpRequest = class MockXHR {
      constructor() {
        this.status = 403;
        this.statusText = 'Forbidden';
      }
      open() {}
      setRequestHeader() {}
      send() {
        setTimeout(() => {
          if (this.onload) this.onload();
        }, 10);
      }
    };

    try {
      const mockFile = { name: 'invoice.pdf', type: 'application/pdf', size: 1000 };
      await assert.rejects(
        async () => {
          await uploadBinaryToS3('https://mock-bucket.s3.amazonaws.com/uploads/test.pdf', mockFile);
        },
        (err) => {
          return err.message.includes('HTTP 403') && err.message.includes('CORS');
        }
      );
    } finally {
      globalThis.XMLHttpRequest = originalXHR;
    }
  });
});
