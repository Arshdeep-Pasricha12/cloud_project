import React, { useState } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AuthModal from './components/AuthModal';
import UploadPanel from './components/UploadPanel';
import { AuthProvider } from './context/AuthContext';
import { useDocuments } from './hooks/useDocuments';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentReviewPage from './pages/DocumentReviewPage';
import SettingsPage from './pages/SettingsPage';

function AppContent() {
  const { documents, metrics, isLoading, refreshDocuments } = useDocuments();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const handleOpenUpload = () => setIsUploadModalOpen(true);
  const handleCloseUpload = () => setIsUploadModalOpen(false);

  return (
    <div className="app-layout" id="app-root-layout">
      <Sidebar metrics={metrics} />
      <div className="main-content">
        <Header onOpenUpload={handleOpenUpload} />
        <main className="page-container">
          <Routes>
            <Route 
              path="/" 
              element={
                <DashboardPage 
                  documents={documents}
                  metrics={metrics}
                  isLoading={isLoading}
                  refreshDocuments={refreshDocuments}
                  onOpenUpload={handleOpenUpload}
                />
              } 
            />
            <Route 
              path="/documents" 
              element={
                <DocumentsPage 
                  documents={documents}
                  metrics={metrics}
                  isLoading={isLoading}
                  refreshDocuments={refreshDocuments}
                  onOpenUpload={handleOpenUpload}
                />
              } 
            />
            <Route path="/review" element={<DocumentReviewPage />} />
            <Route path="/review/:id" element={<DocumentReviewPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route 
              path="*" 
              element={
                <DashboardPage 
                  documents={documents}
                  metrics={metrics}
                  isLoading={isLoading}
                  refreshDocuments={refreshDocuments}
                  onOpenUpload={handleOpenUpload}
                />
              } 
            />
          </Routes>
        </main>
      </div>

      {/* Global Upload Modal */}
      <UploadPanel
        isModal={true}
        isOpen={isUploadModalOpen}
        onClose={handleCloseUpload}
        onUploadSuccess={refreshDocuments}
      />

      {/* Cognito Authentication Modal */}
      <AuthModal />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
