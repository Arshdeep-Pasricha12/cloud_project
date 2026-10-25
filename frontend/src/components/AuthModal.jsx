import React, { useState, useEffect } from 'react';
import { 
  X, 
  Lock, 
  Mail, 
  KeyRound, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  ShieldCheck, 
  UserPlus, 
  LogIn,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AuthModal.css';

export default function AuthModal() {
  const { 
    isAuthModalOpen, 
    authModalTab, 
    closeAuthModal, 
    setAuthModalTab, 
    pendingEmail,
    signIn, 
    signUp, 
    confirmSignUp, 
    resendCode 
  } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (pendingEmail) {
      setEmail(pendingEmail);
    }
  }, [pendingEmail, authModalTab]);

  useEffect(() => {
    setErrorMessage('');
    setSuccessMessage('');
  }, [authModalTab]);

  if (!isAuthModalOpen) return null;

  const handleSignInSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!email || !password) {
      setErrorMessage('Please provide both email and password.');
      return;
    }

    setIsLoading(true);
    try {
      await signIn(email, password);
    } catch (err) {
      if (err.code === 'UserNotConfirmedException') {
        setErrorMessage('Your email is not yet confirmed. Please enter the verification code sent to your inbox.');
        setAuthModalTab('confirm');
      } else if (err.code === 'NotAuthorizedException') {
        setErrorMessage('Incorrect email or password. Please try again.');
      } else if (err.code === 'UserNotFoundException') {
        setErrorMessage('No user account found with this email address.');
      } else {
        setErrorMessage(err.message || 'Failed to sign in. Please check your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUpSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!email || !password) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await signUp(email, password);
      setSuccessMessage(`Account created! A 6-digit confirmation code was sent to ${email}.`);
    } catch (err) {
      if (err.code === 'UsernameExistsException') {
        setErrorMessage('An account with this email already exists. Try signing in or verifying.');
      } else if (err.code === 'InvalidPasswordException') {
        setErrorMessage('Password must contain at least 8 characters with uppercase, lowercase, and numbers.');
      } else {
        setErrorMessage(err.message || 'Failed to register account.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!email || !verificationCode) {
      setErrorMessage('Please enter both email and your 6-digit verification code.');
      return;
    }

    setIsLoading(true);
    try {
      await confirmSignUp(email, verificationCode);
      setSuccessMessage('Email confirmed successfully! You can now sign in.');
    } catch (err) {
      if (err.code === 'CodeMismatchException') {
        setErrorMessage('Invalid verification code. Please check your email and try again.');
      } else if (err.code === 'ExpiredCodeException') {
        setErrorMessage('Verification code has expired. Click below to request a new one.');
      } else {
        setErrorMessage(err.message || 'Failed to verify account code.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) {
      setErrorMessage('Please enter your email to resend the code.');
      return;
    }
    setErrorMessage('');
    try {
      await resendCode(email);
      setSuccessMessage(`New verification code sent to ${email}.`);
    } catch (err) {
      setErrorMessage(err.message || 'Failed to resend code.');
    }
  };

  return (
    <div className="auth-modal-backdrop" onClick={closeAuthModal}>
      <div className="auth-modal-card glass-card" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="auth-modal-header">
          <div className="auth-header-title-box">
            <div className="auth-icon-circle">
              <ShieldCheck size={22} className="shield-icon" />
            </div>
            <div>
              <h2 className="auth-title">Workspace Authentication</h2>
              <p className="auth-subtitle">Secure access to your document workspace</p>
            </div>
          </div>
          <button 
            type="button" 
            className="btn-modal-close" 
            onClick={closeAuthModal} 
            title="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Controls */}
        <div className="auth-tabs-row">
          <button 
            type="button" 
            className={`auth-tab-btn ${authModalTab === 'signin' ? 'auth-tab-active' : ''}`}
            onClick={() => setAuthModalTab('signin')}
          >
            <LogIn size={15} />
            <span>Sign In</span>
          </button>
          <button 
            type="button" 
            className={`auth-tab-btn ${authModalTab === 'signup' ? 'auth-tab-active' : ''}`}
            onClick={() => setAuthModalTab('signup')}
          >
            <UserPlus size={15} />
            <span>Register</span>
          </button>
          <button 
            type="button" 
            className={`auth-tab-btn ${authModalTab === 'confirm' ? 'auth-tab-active' : ''}`}
            onClick={() => setAuthModalTab('confirm')}
          >
            <KeyRound size={15} />
            <span>Verify Code</span>
          </button>
        </div>

        {/* Messages */}
        {errorMessage && (
          <div className="auth-alert alert-error">
            <AlertTriangle size={16} className="alert-icon" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="auth-alert alert-success">
            <CheckCircle2 size={16} className="alert-icon" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* SIGN IN FORM */}
        {authModalTab === 'signin' && (
          <form onSubmit={handleSignInSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="signin-email">Email Address</label>
              <div className="input-with-icon">
                <Mail size={16} className="input-icon" />
                <input
                  id="signin-email"
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="signin-password">Password</label>
              <div className="input-with-icon">
                <Lock size={16} className="input-icon" />
                <input
                  id="signin-password"
                  type="password"
                  required
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary auth-submit-btn" 
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw size={16} className="spin-icon" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>

            <div className="auth-footer-links">
              <span>Don't have an account? </span>
              <button 
                type="button" 
                className="btn-link" 
                onClick={() => setAuthModalTab('signup')}
              >
                Create one now
              </button>
            </div>
          </form>
        )}

        {/* REGISTER FORM */}
        {authModalTab === 'signup' && (
          <form onSubmit={handleSignUpSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="signup-email">Email Address</label>
              <div className="input-with-icon">
                <Mail size={16} className="input-icon" />
                <input
                  id="signup-email"
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="signup-password">Password</label>
              <div className="input-with-icon">
                <Lock size={16} className="input-icon" />
                <input
                  id="signup-password"
                  type="password"
                  required
                  placeholder="At least 8 chars (Uppercase + Numbers)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="signup-confirm-password">Confirm Password</label>
              <div className="input-with-icon">
                <Lock size={16} className="input-icon" />
                <input
                  id="signup-confirm-password"
                  type="password"
                  required
                  placeholder="Confirm password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary auth-submit-btn" 
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw size={16} className="spin-icon" />
                  <span>Creating Account...</span>
                </>
              ) : (
                <>
                  <span>Register & Send Code</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>

            <div className="auth-footer-links">
              <span>Already registered? </span>
              <button 
                type="button" 
                className="btn-link" 
                onClick={() => setAuthModalTab('signin')}
              >
                Sign in to your account
              </button>
            </div>
          </form>
        )}

        {/* VERIFY CODE FORM */}
        {authModalTab === 'confirm' && (
          <form onSubmit={handleConfirmSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="confirm-email">Email Address</label>
              <div className="input-with-icon">
                <Mail size={16} className="input-icon" />
                <input
                  id="confirm-email"
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirm-code">6-Digit Verification Code</label>
              <div className="input-with-icon">
                <KeyRound size={16} className="input-icon" />
                <input
                  id="confirm-code"
                  type="text"
                  maxLength={6}
                  required
                  placeholder="e.g. 123456"
                  className="code-input"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                />
              </div>
              <span className="form-hint">Check your email inbox (and spam folder) for the confirmation code.</span>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary auth-submit-btn" 
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw size={16} className="spin-icon" />
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <span>Verify & Activate Account</span>
                  <CheckCircle2 size={16} />
                </>
              )}
            </button>

            <div className="auth-resend-row">
              <button 
                type="button" 
                className="btn-link" 
                onClick={handleResend}
              >
                Didn't receive code? Resend
              </button>
              <button 
                type="button" 
                className="btn-link" 
                onClick={() => setAuthModalTab('signin')}
              >
                Back to Sign In
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
