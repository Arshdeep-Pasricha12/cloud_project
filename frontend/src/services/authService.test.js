import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { decodeJwt, authService } from './authService.js';

describe('Frontend authService - JWT Decoding & Session Validation', () => {
  it('should correctly decode base64url encoded JWT payload', () => {
    // Standard mock JWT: header.payload.signature
    // Payload: {"sub": "cognito-user-1234", "email": "test@example.com", "exp": 1999999999}
    const payloadObj = {
      sub: 'cognito-user-1234',
      email: 'test@example.com',
      exp: 1999999999,
      'cognito:username': 'test@example.com'
    };
    const header = Buffer.from(JSON.stringify({ alg: 'RS256', typ: 'JWT' })).toString('base64url');
    const payload = Buffer.from(JSON.stringify(payloadObj)).toString('base64url');
    const mockJwt = `${header}.${payload}.mock-signature-part`;

    const decoded = decodeJwt(mockJwt);
    assert.ok(decoded);
    assert.equal(decoded.sub, 'cognito-user-1234');
    assert.equal(decoded.email, 'test@example.com');
  });

  it('should safely return null for invalid or corrupted JWT tokens', () => {
    assert.equal(decodeJwt(null), null);
    assert.equal(decodeJwt(''), null);
    assert.equal(decodeJwt('not.a.valid.jwt.string'), null);
    assert.equal(decodeJwt('single-part-token'), null);
  });

  it('should detect if Cognito user pool configuration is present', () => {
    const configured = authService.isConfigured();
    assert.equal(typeof configured, 'boolean');
  });

  it('should clear stored session data on signOut', () => {
    // Mock localStorage in Node environment
    const store = new Map();
    globalThis.localStorage = {
      getItem: (k) => store.get(k) || null,
      setItem: (k, v) => store.set(k, String(v)),
      removeItem: (k) => store.delete(k),
      clear: () => store.clear()
    };

    localStorage.setItem('doc_intel_id_token', 'mock-token');
    localStorage.setItem('doc_intel_user', JSON.stringify({ email: 'test@example.com' }));

    assert.ok(localStorage.getItem('doc_intel_id_token'));
    authService.signOut();
    assert.equal(localStorage.getItem('doc_intel_id_token'), null);
    assert.equal(localStorage.getItem('doc_intel_user'), null);
  });

  it('should return null for expired JWT token in getCurrentUser', () => {
    const store = new Map();
    globalThis.localStorage = {
      getItem: (k) => store.get(k) || null,
      setItem: (k, v) => store.set(k, String(v)),
      removeItem: (k) => store.delete(k),
      clear: () => store.clear()
    };

    // Expired token (exp in past)
    const expiredPayload = {
      sub: 'user-expired',
      email: 'expired@example.com',
      exp: Math.floor(Date.now() / 1000) - 3600 // 1 hour ago
    };
    const header = Buffer.from(JSON.stringify({ alg: 'RS256' })).toString('base64url');
    const payload = Buffer.from(JSON.stringify(expiredPayload)).toString('base64url');
    const expiredJwt = `${header}.${payload}.sig`;

    localStorage.setItem('doc_intel_id_token', expiredJwt);
    localStorage.setItem('doc_intel_user', JSON.stringify({ email: 'expired@example.com' }));

    const user = authService.getCurrentUser();
    assert.equal(user, null);
    // Should auto-clean expired tokens
    assert.equal(localStorage.getItem('doc_intel_id_token'), null);
  });
});
