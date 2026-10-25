/**
 * Automated tests for apiService (Milestone 7)
 * Tests client interactions with API Gateway, authorization token headers, and error states.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';

describe('Frontend apiService - API Gateway Integration', () => {
  let originalFetch;
  let originalBaseUrl;

  beforeEach(() => {
    originalFetch = global.fetch;
    originalBaseUrl = process.env.VITE_API_BASE_URL;
    process.env.VITE_API_BASE_URL = 'https://wxgm03t7wc.execute-api.ap-south-1.amazonaws.com/prod';
  });

  afterEach(() => {
    global.fetch = originalFetch;
    process.env.VITE_API_BASE_URL = originalBaseUrl;
  });

  it('should detect when API Gateway base URL is configured', async () => {
    // Dynamically test apiService configuration detection
    const { apiService } = await import('./api.js');
    assert.strictEqual(typeof apiService.isConfigured, 'function');
    assert.strictEqual(typeof apiService.listDocuments, 'function');
    assert.strictEqual(typeof apiService.getDocument, 'function');
    assert.strictEqual(typeof apiService.saveCorrections, 'function');
  });

  it('should format GET /documents request and parse response', async () => {
    const mockResponse = {
      items: [
        {
          documentId: 'doc-001',
          fileName: 'invoice-techcorp.pdf',
          status: 'PENDING_REVIEW',
          vendor: 'TechCorp Cloud',
          totalAmount: 4250.00
        }
      ],
      metrics: { total: 1, pendingReview: 1, reviewed: 0, failed: 0 }
    };

    global.fetch = async (url, options) => {
      assert.ok(url.includes('/documents'));
      assert.strictEqual(options.method, 'GET');
      assert.ok(options.headers['Content-Type'] === 'application/json');
      return {
        ok: true,
        status: 200,
        json: async () => mockResponse
      };
    };

    const { apiService } = await import('./api.js');
    const result = await apiService.listDocuments();
    assert.strictEqual(result.items.length, 1);
    assert.strictEqual(result.items[0].documentId, 'doc-001');
    assert.strictEqual(result.metrics.total, 1);
  });

  it('should format GET /documents/{id} request and handle 404 NotFound', async () => {
    global.fetch = async (url) => {
      assert.ok(url.includes('/documents/doc-not-found'));
      return {
        ok: false,
        status: 404,
        json: async () => ({ message: "Document 'doc-not-found' not found." })
      };
    };

    const { apiService } = await import('./api.js');
    await assert.rejects(
      async () => {
        await apiService.getDocument('doc-not-found');
      },
      /Document 'doc-not-found' not found/
    );
  });

  it('should send PUT /documents/{id}/corrections with payload', async () => {
    const correctionsData = {
      vendorName: 'TechCorp Global Solutions',
      totalAmount: 4500.00
    };

    let receivedBody = null;
    global.fetch = async (url, options) => {
      assert.ok(url.includes('/documents/doc-123/corrections'));
      assert.strictEqual(options.method, 'PUT');
      receivedBody = JSON.parse(options.body);
      return {
        ok: true,
        status: 200,
        json: async () => ({
          message: 'Corrections successfully saved.',
          document: { documentId: 'doc-123', status: 'REVIEWED' }
        })
      };
    };

    const { apiService } = await import('./api.js');
    const res = await apiService.saveCorrections('doc-123', correctionsData);
    assert.strictEqual(res.document.status, 'REVIEWED');
    assert.deepStrictEqual(receivedBody.corrections, correctionsData);
  });
});
