import React from 'react';
import { ShieldCheck, User, LogIn, LogOut, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Header.css';

export default function Header({ title = 'Dashboard' }) {
  const { user, isAuthenticated, openAuthModal, signOut } = useAuth();

  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : 'U';

  return (
    <header className="app-header" id="app-header">
      <div className="header-left">
        <h1 className="header-title" id="page-title">{title}</h1>
        <span className="env-badge enterprise-badge">Enterprise Edition</span>
      </div>

      <div className="header-right">
        {/* AWS Backend Status Pill */}
        <div className="aws-connection-status conn-active" id="aws-status-indicator" title="AWS Serverless Infrastructure Active">
          <CheckCircle2 size={15} className="status-icon-active" />
          <div className="connection-text">
            <span className="conn-title-active">AWS Operational</span>
            <span className="conn-state">ap-south-1 (Mumbai)</span>
          </div>
        </div>

        {/* User Profile Pill / Auth Button */}
        {!isAuthenticated ? (
          <button
            type="button"
            className="user-profile-pill user-profile-interactive"
            id="btn-open-auth-modal"
            onClick={() => openAuthModal('signin')}
            title="Sign in with your Amazon Cognito account"
          >
            <div className="user-avatar avatar-signin">
              <LogIn size={15} />
            </div>
            <div className="user-info">
              <span className="user-name">Sign In / Register</span>
              <span className="user-role">Single Sign-On / IAM</span>
            </div>
          </button>
        ) : (
          <div className="user-profile-wrapper">
            <div className="user-profile-pill pill-logged-in" id="user-profile-badge">
              <div className="user-avatar avatar-authenticated">
                <span>{userInitial}</span>
              </div>
              <div className="user-info">
                <span className="user-name" title={user.email}>{user.email}</span>
                <span className="user-role user-role-verified">
                  <ShieldCheck size={11} />
                  <span>Cognito Verified</span>
                </span>
              </div>
            </div>
            <button
              type="button"
              className="btn-signout"
              onClick={signOut}
              title="Sign Out"
              id="btn-user-signout"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
