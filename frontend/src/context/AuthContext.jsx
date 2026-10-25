import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState('signin'); // 'signin' | 'signup' | 'confirm'
  const [pendingEmail, setPendingEmail] = useState('');

  // Check stored session on mount and ensure token is fresh
  useEffect(() => {
    async function restoreSession() {
      try {
        const currentUser = authService.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
          // Refresh expired tokens transparently using refresh token
          await authService.getValidIdToken();
        }
      } catch (e) {
        console.warn('Failed to restore auth session:', e);
      } finally {
        setIsLoading(false);
      }
    }
    restoreSession();
  }, []);

  const openAuthModal = (tab = 'signin', email = '') => {
    setAuthModalTab(tab);
    if (email) setPendingEmail(email);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const handleSignIn = async (email, password) => {
    const result = await authService.signIn(email, password);
    setUser(result.user);
    closeAuthModal();
    return result;
  };

  const handleSignUp = async (email, password) => {
    const result = await authService.signUp(email, password);
    setPendingEmail(email);
    setAuthModalTab('confirm');
    return result;
  };

  const handleConfirmSignUp = async (email, code) => {
    const result = await authService.confirmSignUp(email, code);
    setAuthModalTab('signin');
    return result;
  };

  const handleResendCode = async (email) => {
    return authService.resendConfirmationCode(email);
  };

  const handleSignOut = () => {
    authService.signOut();
    setUser(null);
  };

  const value = {
    user,
    isAuthenticated: Boolean(user),
    isLoading,
    isConfigured: authService.isConfigured(),
    isAuthModalOpen,
    authModalTab,
    pendingEmail,
    setPendingEmail,
    openAuthModal,
    closeAuthModal,
    setAuthModalTab,
    signIn: handleSignIn,
    signUp: handleSignUp,
    confirmSignUp: handleConfirmSignUp,
    resendCode: handleResendCode,
    signOut: handleSignOut
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
