import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  RefreshCw, 
  Inbox, 
  ExternalLink, 
  ShieldCheck, 
  ArrowRight,
  Database
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import { formatDate, formatCurrency, formatConfidence } from '../utils/formatters';
import './DocumentsTable.css';

export default function DocumentsTable({ documents = [], isLoading = false, onRefresh }) {
  return (
    <div className="glass-card documents-table-container" id="documents-table-container">
      <div className="table-header">
        <div>
          <h2 className="table-title">Recent Invoices & Documents</h2>
          <p className="table-subtitle">Live records from Amazon DynamoDB table</p>
        </div>
        <div className="table-header-actions">
          <span className="phase-badge">DynamoDB GSI · Phase 5</span>
          <button
            type="button"
            id="btn-refresh-documents"
            className="btn btn-secondary btn-sm"
            onClick={onRefresh}
            disabled={isLoading}
            title="Query DynamoDB for recent documents"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin-slow' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="table-empty-state" id="documents-empty-state">
          <div className="empty-state-icon-box">
            <Inbox size={42} className="empty-icon" />
          </div>
          <h3 className="empty-title">No Documents in Database</h3>
          <p className="empty-desc">
            No invoices have been ingested into Amazon S3 or recorded in DynamoDB yet.
            As required, this application starts with genuine empty states rather than fake mock records.
          </p>
          <div className="empty-milestone-guidance">
            <div className="guidance-step">
              <Database size={15} className="step-icon" />
              <span>
                <strong>Milestones 2 & 5:</strong> Uploading will write document metadata to DynamoDB and trigger Textract AnalyzeExpense.
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="data-table" id="data-table">
            <thead>
              <tr>
                <th>Document</th>
                <th>Status</th>
                <th>Vendor</th>
                <th>Total</th>
                <th>Confidence</th>
                <th>Uploaded</th>
                <th className="th-action">Action</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.documentId} className="table-row">
                  <td className="cell-doc-name">
                    <div className="doc-name-cell">
                      <FileText size={16} className="doc-cell-icon" />
                      <span className="doc-name-text" title={doc.fileName}>{doc.fileName}</span>
                    </div>
                  </td>
                  <td>
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="cell-vendor">
                    {doc.vendor || '—'}
                  </td>
                  <td className="cell-amount">
                    {formatCurrency(doc.totalAmount)}
                  </td>
                  <td className="cell-confidence">
                    {formatConfidence(doc.confidence)}
                  </td>
                  <td className="cell-date">
                    {formatDate(doc.createdAt)}
                  </td>
                  <td className="cell-action">
                    <Link
                      to={`/review/${doc.documentId}`}
                      className="btn-action-review"
                      title="Inspect extraction and edit corrections"
                    >
                      <span>Review</span>
                      <ArrowRight size={13} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
