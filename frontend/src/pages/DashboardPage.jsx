import React from 'react';
import { Link } from 'react-router-dom';
import MetricsCards from '../components/MetricsCards';
import StatusBadge from '../components/StatusBadge';
import { useDocuments } from '../hooks/useDocuments';
import { formatBytes, formatCurrency, formatRelativeTime } from '../utils/formatters';
import { 
  Plus, 
  Upload, 
  FileText, 
  AlertCircle, 
  ArrowRight, 
  CheckCircle2, 
  Inbox,
  ShieldCheck
} from 'lucide-react';
import './DashboardPage.css';

export default function DashboardPage({ 
  documents: propDocs, 
  metrics: propMetrics, 
  isLoading: propLoading, 
  refreshDocuments: propRefresh,
  onOpenUpload 
}) {
  const fallback = useDocuments();
  const documents = propDocs ?? fallback.documents;
  const metrics = propMetrics ?? fallback.metrics;
  const isLoading = propLoading ?? fallback.isLoading;
  const refreshDocuments = propRefresh ?? fallback.refreshDocuments;

  // Format today's date for top label: e.g. "SUNDAY, OCTOBER 25"
  const todayFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  }).format(new Date()).toUpperCase();

  // Documents needing attention
  const needsAttentionDocs = documents.filter((doc) => doc.status === 'PENDING_REVIEW');
  const recentDocs = documents.slice(0, 6);

  return (
    <div className="dashboard-page" id="dashboard-page">
      {/* Top Title Row */}
      <div className="dashboard-header-row">
        <div className="dashboard-title-group">
          <div className="dashboard-date-label">{todayFormatted}</div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">A clear view of your documents and what needs your attention.</p>
        </div>
        <div className="dashboard-header-actions">
          <button
            type="button"
            className="btn btn-primary"
            id="btn-overview-upload"
            onClick={onOpenUpload}
          >
            <Plus size={15} />
            <span>Upload document</span>
          </button>
        </div>
      </div>

      {/* 4 Compact Metric Cards */}
      <MetricsCards metrics={metrics} />

      {/* Main Two-Column Layout */}
      <div className="dashboard-content-grid">
        {/* Left Column: Recent documents */}
        <div className="dashboard-card recent-documents-panel">
          <div className="panel-header-row">
            <div>
              <h2 className="panel-title">Recent documents</h2>
              <p className="panel-desc">Your latest uploads and their current status.</p>
            </div>
            <Link to="/documents" className="panel-action-link" id="link-view-all-documents">
              <span>View all documents</span>
              <ArrowRight size={13} />
            </Link>
          </div>

          {recentDocs.length === 0 ? (
            <div className="panel-empty-state" id="recent-docs-empty">
              <div className="empty-state-icon-box">
                <Inbox size={28} />
              </div>
              <h3 className="empty-state-title">No documents received</h3>
              <p className="empty-state-desc">
                Upload your first invoice or receipt to see recent documents and line-item extraction here.
              </p>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onOpenUpload}
              >
                <Upload size={13} />
                <span>Upload document</span>
              </button>
            </div>
          ) : (
            <>
              <div className="recent-table-wrap">
                <table className="recent-table">
                  <thead>
                    <tr>
                      <th className="th-doc">DOCUMENT</th>
                      <th className="th-status">STATUS</th>
                      <th className="th-amount">AMOUNT</th>
                      <th className="th-time">UPLOADED</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentDocs.map((doc) => {
                      const amount = doc.totalAmount ?? doc.rawExtraction?.summaryFields?.totalAmount?.value;
                      const currency = doc.currency || doc.rawExtraction?.summaryFields?.currency?.value || 'USD';
                      return (
                        <tr key={doc.documentId} className="recent-table-row">
                          <td className="td-doc">
                            <Link to={`/review/${doc.documentId}`} className="doc-link-wrap">
                              <div className="doc-icon-box">
                                <FileText size={15} />
                              </div>
                              <div className="doc-meta-wrap">
                                <span className="doc-name" title={doc.fileName}>
                                  {doc.fileName}
                                </span>
                                <span className="doc-sub">
                                  {doc.fileName?.toLowerCase().endsWith('.pdf') ? 'PDF' : 'Image'} · {formatBytes(doc.fileSizeBytes || 0)}
                                </span>
                              </div>
                            </Link>
                          </td>
                          <td className="td-status">
                            <StatusBadge status={doc.status} />
                          </td>
                          <td className="td-amount tabular-nums">
                            {amount !== undefined && amount !== null && amount !== '' ? (
                              formatCurrency(amount, currency)
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </td>
                          <td className="td-time">
                            {formatRelativeTime(doc.uploadedAt || doc.createdAt)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="panel-footer-count">
                Showing {recentDocs.length} of {documents.length} documents
              </div>
            </>
          )}
        </div>

        {/* Right Column: Needs your attention */}
        <div className="dashboard-side-col">
          <div className="dashboard-card attention-panel">
            <div className="panel-header-row">
              <div>
                <h2 className="panel-title">Needs your attention</h2>
                <p className="panel-desc">Pick up where you left off.</p>
              </div>
              <span className="attention-pending-pill">
                {needsAttentionDocs.length} pending
              </span>
            </div>

            {needsAttentionDocs.length === 0 ? (
              <div className="attention-empty-box">
                <CheckCircle2 size={20} className="all-clear-icon" />
                <div>
                  <h4 className="all-clear-title">All caught up</h4>
                  <p className="all-clear-desc">No invoices currently waiting for human review.</p>
                </div>
              </div>
            ) : (
              <div className="attention-items-list">
                {needsAttentionDocs.slice(0, 5).map((doc) => {
                  return (
                    <div key={doc.documentId} className="attention-item-row">
                      <div className="attention-icon-box">
                        <AlertCircle size={15} />
                      </div>
                      <div className="attention-item-info">
                        <Link to={`/review/${doc.documentId}`} className="attention-doc-title" title={doc.fileName}>
                          {doc.fileName}
                        </Link>
                        <span className="attention-doc-sub">
                          Needs review confirmation · {formatRelativeTime(doc.uploadedAt || doc.createdAt)}
                        </span>
                      </div>
                      <Link 
                        to={`/review/${doc.documentId}`} 
                        className="attention-review-link"
                      >
                        <span>Review</span>
                        <ArrowRight size={12} />
                      </Link>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Note on accuracy */}
            <div className="accuracy-note-card">
              <h4 className="accuracy-note-title">A note on accuracy</h4>
              <p className="accuracy-note-text">
                AI extraction can miss details on low-quality scans. Review flagged fields before marking an invoice complete.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quiet Footnote */}
      <div className="page-footnote">
        <CheckCircle2 size={13} className="page-footnote-icon" />
        <span>Original documents remain private. Only files you upload are processed.</span>
      </div>
    </div>
  );
}
