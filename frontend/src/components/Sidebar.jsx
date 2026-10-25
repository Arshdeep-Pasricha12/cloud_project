import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutGrid, 
  FileText, 
  CheckCircle2, 
  SlidersHorizontal,
  LogIn,
  LogOut
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

export default function Sidebar({ metrics = { total: 0, pendingReview: 0 } }) {
  const { user, isAuthenticated, openAuthModal, signOut } = useAuth();

  // Extract initials and display name
  const displayName = user?.email 
    ? user.email.split('@')[0] 
    : 'Arshdeep Pasricha';

  const userInitial = user?.email 
    ? user.email.slice(0, 2).toUpperCase() 
    : 'AP';

  return (
    <aside className="app-sidebar" id="app-sidebar">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-logo-mark">D</div>
        <div className="brand-text">
          <span className="brand-title">DocuIntel</span>
          <span className="brand-subtitle">Document workspace</span>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">WORKSPACE</div>
        <nav className="sidebar-nav">
          <NavLink
            to="/"
            end
            id="nav-overview"
            className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
          >
            <LayoutGrid size={16} className="nav-icon" />
            <span className="nav-label">Overview</span>
          </NavLink>

          <NavLink
            to="/documents"
            id="nav-documents"
            className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
          >
            <FileText size={16} className="nav-icon" />
            <span className="nav-label">Documents</span>
            {metrics?.total > 0 && (
              <span className="nav-count-badge" id="nav-count-documents">
                {metrics.total}
              </span>
            )}
          </NavLink>

          <NavLink
            to="/review"
            id="nav-review-queue"
            className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
          >
            <CheckCircle2 size={16} className="nav-icon" />
            <span className="nav-label">Review queue</span>
            {metrics?.pendingReview > 0 && (
              <span className="nav-count-badge" id="nav-count-pending">
                {metrics.pendingReview}
              </span>
            )}
          </NavLink>
        </nav>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-title">PREFERENCES</div>
        <nav className="sidebar-nav">
          <NavLink
            to="/settings"
            id="nav-settings"
            className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
          >
            <SlidersHorizontal size={16} className="nav-icon" />
            <span className="nav-label">Settings</span>
          </NavLink>
        </nav>
      </div>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        {/* Workspace Status Card */}
        <div className="workspace-status-card" id="workspace-status-box">
          <div className="status-label">WORKSPACE STATUS</div>
          <div className="status-indicator-row">
            <span className="status-dot-pulse"></span>
            <span className="status-text">All systems operational</span>
          </div>
          <div className="status-timestamp">Last checked just now</div>
        </div>

        {/* User Account / Workspace Row */}
        <div className="user-workspace-row">
          <button
            type="button"
            className="user-workspace-btn"
            id={isAuthenticated ? "user-profile-badge" : "btn-open-auth-modal"}
            onClick={() => isAuthenticated ? signOut() : openAuthModal('signin')}
            title={isAuthenticated ? `Signed in as ${user.email} (Click to sign out)` : 'Sign in to workspace'}
          >
            <div className="user-avatar-circle">
              {userInitial}
            </div>
            <div className="user-text-info">
              <span className="user-display-name" title={user?.email || displayName}>
                {displayName}
              </span>
              <span className="user-workspace-label">
                {isAuthenticated ? 'Cognito verified' : 'Personal workspace'}
              </span>
            </div>
            <div className="user-action-icon">
              {isAuthenticated ? <LogOut size={13} /> : <LogIn size={13} />}
            </div>
          </button>
        </div>
      </div>
    </aside>
  );
}
