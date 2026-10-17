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
            <span>Milestone 0 · Architecture Foundation</span>
          </div>
          <h2 className="banner-title">Serverless Document Intelligence Dashboard</h2>
          <p className="banner-text">
            Ingest invoices via Amazon S3 presigned URLs, extract structured financial records using Amazon Textract AnalyzeExpense, and validate corrections with human-in-the-loop DynamoDB persistence.
          </p>
        </div>
        <div className="banner-services">
          <div className="service-chip">
            <span className="dot dot-amber"></span>
            <span>Cognito (Auth)</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-amber"></span>
            <span>S3 (Private Storage)</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-amber"></span>
            <span>Textract (AnalyzeExpense)</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-amber"></span>
            <span>DynamoDB (Records)</span>
          </div>
          <div className="service-chip">
            <span className="dot dot-amber"></span>
            <span>Lambda (Python 3.12)</span>
          </div>
        </div>
      </div>

      {/* Metrics Cards Grid (Empty States) */}
      <MetricsCards metrics={metrics} />

      {/* Ingest Document Panel */}
      <UploadPanel />

      {/* Recent Documents Table (Genuine Empty State) */}
      <DocumentsTable 
        documents={documents} 
        isLoading={isLoading} 
        onRefresh={refreshDocuments} 
      />
    </div>
  );
}
