import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Search, Bell, User, LogIn, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Header.css';

export default function Header({ onSearch, onOpenUpload }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, openAuthModal, signOut } = useAuth();
  const [searchValue, setSearchValue] = useState('');

  // Extract initials
  const userInitial = user?.email 
    ? user.email.slice(0, 2).toUpperCase() 
    : 'AP';

  // Compute breadcrumb
  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path === '/') {
      return (
        <div className="breadcrumb-nav">
          <span className="breadcrumb-parent">Workspace</span>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">Overview</span>
        </div>
      );
    }
    if (path.startsWith('/documents')) {
      return (
        <div className="breadcrumb-nav">
          <Link to="/" className="breadcrumb-parent">Workspace</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">Documents</span>
        </div>
      );
    }
    if (path.startsWith('/review/')) {
      return (
        <div className="breadcrumb-nav">
          <Link to="/" className="breadcrumb-parent">Workspace</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">Review invoice</span>
        </div>
      );
    }
    if (path.startsWith('/review')) {
      return (
        <div className="breadcrumb-nav">
          <Link to="/" className="breadcrumb-parent">Workspace</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">Review queue</span>
        </div>
      );
    }
    if (path.startsWith('/settings')) {
      return (
        <div className="breadcrumb-nav">
          <Link to="/" className="breadcrumb-parent">Workspace</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">Settings</span>
        </div>
      );
    }
    return (
      <div className="breadcrumb-nav">
        <span className="breadcrumb-parent">Workspace</span>
        <span className="breadcrumb-sep">/</span>
        <span className="breadcrumb-current">DocuIntel</span>
      </div>
    );
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      if (onSearch) {
        onSearch(searchValue);
      }
      if (location.pathname !== '/documents') {
        navigate(`/documents?search=${encodeURIComponent(searchValue)}`);
      }
    }
  };

  return (
    <header className="app-header" id="app-header">
      {/* Left Breadcrumb */}
      <div className="header-left">
        {getBreadcrumbs()}
      </div>

      {/* Right Controls */}
      <div className="header-right">
        {/* Search Bar */}
        <div className="header-search-wrap">
          <Search size={14} className="header-search-icon" />
          <input
            type="text"
            className="header-search-input"
            placeholder="Search documents or vendors"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            aria-label="Search documents or vendors"
          />
          <kbd className="header-search-shortcut">⌘K</kbd>
        </div>

        {/* Notifications Icon Button */}
        <button
          type="button"
          className="header-icon-btn"
          title="Notifications"
          aria-label="Notifications"
        >
          <Bell size={16} />
        </button>

        {/* User Profile Pill / Auth Button */}
        <button
          type="button"
          className="header-avatar-btn"
          id={isAuthenticated ? "user-profile-badge" : "btn-open-auth-modal"}
          onClick={() => isAuthenticated ? signOut() : openAuthModal('signin')}
          title={isAuthenticated ? `Signed in as ${user.email} (Click to sign out)` : 'Sign In / Register'}
          aria-label="User account"
        >
          <span className="header-avatar-initials">{userInitial}</span>
        </button>
      </div>
    </header>
  );
}
