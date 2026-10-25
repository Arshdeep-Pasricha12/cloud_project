/**
 * Amazon Cognito Authentication Service
 * 
 * Direct, lightweight client communicating with AWS Cognito Identity Provider endpoints.
 * Handles sign-up, email verification, password authentication (USER_PASSWORD_AUTH),
 * token storage, and JWT session validation without heavy third-party SDK dependencies.
 */

const getEnvVar = (key) => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[key]) {
    return import.meta.env[key];
  }
  if (typeof process !== 'undefined' && process.env && process.env[key]) {
    return process.env[key];
  }
  return '';
};

const AWS_REGION = getEnvVar('VITE_AWS_REGION') || 'ap-south-1';
const USER_POOL_ID = getEnvVar('VITE_COGNITO_USER_POOL_ID') || '';
const CLIENT_ID = getEnvVar('VITE_COGNITO_CLIENT_ID') || '';
const COGNITO_ENDPOINT = `https://cognito-idp.${AWS_REGION}.amazonaws.com`;

const STORAGE_KEYS = {
  ID_TOKEN: 'doc_intel_id_token',
  ACCESS_TOKEN: 'doc_intel_access_token',
  REFRESH_TOKEN: 'doc_intel_refresh_token',
  USER_DATA: 'doc_intel_user'
};

/**
 * Decode JWT token payload without verifying cryptographic signature (client-side decoding).
 */
export function decodeJwt(token) {
  try {
    if (!token || typeof token !== 'string') return null;
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

/**
 * Execute a low-level Cognito IDP JSON 1.1 request.
 */
async function callCognito(target, payload) {
  if (!CLIENT_ID) {
    throw new Error('Cognito Client ID is not configured. Set VITE_COGNITO_CLIENT_ID in frontend/.env.');
  }

  const response = await fetch(COGNITO_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-amz-json-1.1',
      'X-Amz-Target': `AWSCognitoIdentityProviderService.${target}`
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorType = data.__type ? data.__type.split('#').pop() : 'CognitoError';
    const message = data.message || data.Message || `Cognito operation failed (${response.status})`;
    const error = new Error(message);
    error.code = errorType;
    throw error;
  }

  return data;
}

export const authService = {
  isConfigured() {
    return Boolean(USER_POOL_ID && CLIENT_ID && !CLIENT_ID.includes('your-cognito'));
  },

  /**
   * Register a new user with email and password.
   */
  async signUp(email, password) {
    const payload = {
      ClientId: CLIENT_ID,
      Username: email,
      Password: password,
      UserAttributes: [
        { Name: 'email', Value: email }
      ]
    };

    const result = await callCognito('SignUp', payload);
    return {
      userSub: result.UserSub,
      userConfirmed: result.UserConfirmed,
      codeDeliveryDetails: result.CodeDeliveryDetails
    };
  },

  /**
   * Confirm account using the 6-digit verification code sent to email.
   */
  async confirmSignUp(email, code) {
    const payload = {
      ClientId: CLIENT_ID,
      Username: email,
      ConfirmationCode: code.trim()
    };

    await callCognito('ConfirmSignUp', payload);
    return { success: true };
  },

  /**
   * Resend the verification code to the user's email.
   */
  async resendConfirmationCode(email) {
    const payload = {
      ClientId: CLIENT_ID,
      Username: email
    };

    const result = await callCognito('ResendConfirmationCode', payload);
    return result.CodeDeliveryDetails;
  },

  /**
   * Authenticate user via USER_PASSWORD_AUTH flow.
   */
  async signIn(email, password) {
    const payload = {
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: CLIENT_ID,
      AuthParameters: {
        USERNAME: email,
        PASSWORD: password
      }
    };

    const result = await callCognito('InitiateAuth', payload);
    const authResult = result.AuthenticationResult;

    if (!authResult || !authResult.IdToken) {
      throw new Error('Authentication succeeded but did not return JWT ID token.');
    }

    // Decode and save user session
    const idClaims = decodeJwt(authResult.IdToken);
    const user = {
      sub: idClaims.sub,
      email: idClaims.email || email,
      emailVerified: idClaims.email_verified || false,
      username: idClaims['cognito:username'] || email
    };

    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEYS.ID_TOKEN, authResult.IdToken);
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, authResult.AccessToken);
      if (authResult.RefreshToken) {
        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, authResult.RefreshToken);
      }
      localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
    }

    return {
      user,
      idToken: authResult.IdToken,
      accessToken: authResult.AccessToken
    };
  },

  /**
   * Sign out and clear stored tokens.
   */
  signOut() {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(STORAGE_KEYS.ID_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.USER_DATA);
    }
  },

  /**
   * Refresh current Cognito session using the stored refresh token.
   * Enables persistent login across browser reloads without re-entering credentials.
   */
  async refreshSession() {
    if (typeof localStorage === 'undefined') return null;
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    if (!refreshToken) return null;

    try {
      const payload = {
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        ClientId: CLIENT_ID,
        AuthParameters: {
          REFRESH_TOKEN: refreshToken
        }
      };

      const result = await callCognito('InitiateAuth', payload);
      const authResult = result.AuthenticationResult;

      if (authResult && authResult.IdToken) {
        localStorage.setItem(STORAGE_KEYS.ID_TOKEN, authResult.IdToken);
        if (authResult.AccessToken) {
          localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, authResult.AccessToken);
        }
        return authResult.IdToken;
      }
    } catch (err) {
      console.warn('Automatic session refresh failed:', err);
      // Only sign out if refresh token itself was revoked/invalid
      if (err.code === 'NotAuthorizedException') {
        this.signOut();
      }
    }
    return null;
  },

  /**
   * Retrieve current stored user profile.
   */
  getCurrentUser() {
    if (typeof localStorage === 'undefined') return null;

    const idToken = localStorage.getItem(STORAGE_KEYS.ID_TOKEN);
    const userJson = localStorage.getItem(STORAGE_KEYS.USER_DATA);
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);

    if (!idToken || !userJson) return null;

    const claims = decodeJwt(idToken);
    if (!claims || !claims.exp) {
      if (!refreshToken) this.signOut();
      return null;
    }

    // Check token expiration (exp is in seconds)
    const nowSeconds = Math.floor(Date.now() / 1000);
    if (claims.exp < nowSeconds) {
      // If no refresh token exists, auto-clean expired session
      if (!refreshToken) {
        this.signOut();
        return null;
      }
    }

    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  },

  /**
   * Get valid ID token string for API Gateway Authorization headers.
   */
  getIdToken() {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem(STORAGE_KEYS.ID_TOKEN);
  },

  /**
   * Async getter ensuring a valid (non-expired) ID token, refreshing automatically if needed.
   */
  async getValidIdToken() {
    if (typeof localStorage === 'undefined') return null;
    const token = localStorage.getItem(STORAGE_KEYS.ID_TOKEN);
    if (!token) return null;

    const claims = decodeJwt(token);
    const nowSeconds = Math.floor(Date.now() / 1000);

    // Refresh if token is expired or within 60 seconds of expiring
    if (!claims || !claims.exp || claims.exp <= nowSeconds + 60) {
      const refreshed = await this.refreshSession();
      if (refreshed) return refreshed;
    }

    return token;
  }
};
