import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Files, 
  FileCheck, 
  Settings, 
  Cpu, 
  Layers,
  ExternalLink,
  ShieldAlert
} from 'lucide-react';
import './Sidebar.css';

export default function Sidebar() {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
    { to: '/documents', label: 'Documents', icon: Files },
    { to: '/review', label: 'Document Review', icon: FileCheck },
    { to: '/settings', label: 'Platform Settings', icon: Settings }
  ];

  return (
    <aside className="app-sidebar" id="app-sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo-icon">
          <Cpu className="brand-icon" size={24} />
        </div>
        <div className="brand-text">
          <span className="brand-title">DocuIntel</span>
          <span className="brand-subtitle">Serverless AI Platform</span>
        </div>
      </div>

      <div className="sidebar-section-title">Navigation</div>
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              id={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
              className={({ isActive }) => 
                `nav-link ${isActive ? 'nav-link-active' : ''}`
              }
            >
              <Icon size={18} className="nav-icon" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status-box">
          <div className="status-header">
            <span className="status-dot-active"></span>
            <span className="status-header-text">System Status</span>
          </div>
          <p className="status-desc">
            Enterprise cloud infrastructure 100% operational.
          </p>
          <div className="system-meta-tags">
            <span className="meta-tag">AWS ap-south-1</span>
            <span className="meta-tag">Textract AI</span>
            <span className="meta-tag">AES-256</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
