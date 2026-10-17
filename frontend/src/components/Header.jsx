import React from 'react';
import { CloudOff, Shield, Bell, User, Sparkles } from 'lucide-react';
import './Header.css';

export default function Header({ title = 'Dashboard' }) {
  return (
    <header className="app-header" id="app-header">
      <div className="header-left">
        <h1 className="header-title" id="page-title">{title}</h1>
        <span className="env-badge">Dev Shell</span>
      </div>

      <div className="header-right">
        {/* AWS Backend Status Pill */}
        <div className="aws-connection-status" id="aws-status-indicator" title="AWS Integration Pending Approval">
          <CloudOff size={15} className="status-icon-offline" />
          <div className="connection-text">
            <span className="conn-title">AWS Services</span>
            <span className="conn-state">Not Connected (Phases 1–6)</span>
          </div>
        </div>

        {/* User Profile Pill */}
        <div className="user-profile-pill" id="user-profile-badge" title="Authentication with Amazon Cognito coming in Milestone 1">
          <div className="user-avatar">
            <User size={16} />
          </div>
          <div className="user-info">
            <span className="user-name">Guest User</span>
            <span className="user-role">Cognito Auth · Phase 1</span>
          </div>
        </div>
      </div>
    </header>
  );
}
