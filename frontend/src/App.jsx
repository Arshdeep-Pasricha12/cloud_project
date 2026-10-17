import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentReviewPage from './pages/DocumentReviewPage';
import SettingsPage from './pages/SettingsPage';

function AppContent() {
  const location = useLocation();

  const getPageTitle = (pathname) => {
    if (pathname === '/') return 'Dashboard';
    if (pathname.startsWith('/documents')) return 'Documents';
    if (pathname.startsWith('/review')) return 'Document Review';
    if (pathname.startsWith('/settings')) return 'AWS Configuration';
    return 'Document Intelligence';
  };

  return (
    <div className="app-layout" id="app-root-layout">
      <Sidebar />
      <div className="main-content">
        <Header title={getPageTitle(location.pathname)} />
        <main className="page-container">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/review" element={<DocumentReviewPage />} />
            <Route path="/review/:id" element={<DocumentReviewPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<DashboardPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return <AppContent />;
}
