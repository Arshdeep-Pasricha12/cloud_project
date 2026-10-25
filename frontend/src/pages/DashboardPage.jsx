import React from 'react';
import MetricsCards from '../components/MetricsCards';
import UploadPanel from '../components/UploadPanel';
import DocumentsTable from '../components/DocumentsTable';
import { useDocuments } from '../hooks/useDocuments';
import { Layers, ShieldCheck, Cpu, ArrowUpRight } from 'lucide-react';
import './DashboardPage.css';

export default function DashboardPage() {
  const { documents, metrics, isLoading, refreshDocuments } = useDocuments();

  return (
    <div className="dashboard-page" id="dashboard-page">
      {/* Platform Status Banner */}
      <div className="glass-card platform-banner">
        <div className="banner-content">
          <div className="banner-badge">
            <Cpu size={14} />
            <span>AI Document Intelligence Pipeline · ap-south-1</span>
          </div>
          <h2 className="banner-title">Intelligent Financial Document Automation</h2>
          <p className="banner-text">
            End-to-end serverless cloud pipeline: Ingest enterprise invoices into Amazon S3, extract structured line-items with Amazon Textract, and index records in Amazon DynamoDB with audit verification.
          </p>
        </div>
        <div className="banner-services">
          <div className="service-chip">
            <span className="dot dot-green"></span>
            <span>Cognito SSO</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-green"></span>
            <span>S3 Encrypted Lake</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-green"></span>
            <span>Textract AI</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-green"></span>
            <span>DynamoDB Core</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-green"></span>
            <span>CloudWatch Logs</span>
          </div>
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <MetricsCards metrics={metrics} />

      {/* Ingest Document Panel */}
      <UploadPanel onUploadSuccess={refreshDocuments} />

      {/* Recent Documents Table (Genuine Empty State) */}
      <DocumentsTable 
        documents={documents} 
        isLoading={isLoading} 
        onRefresh={refreshDocuments} 
      />
    </div>
  );
}
