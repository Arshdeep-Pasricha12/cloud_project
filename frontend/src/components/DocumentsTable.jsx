import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  MoreHorizontal, 
  ArrowRight, 
  Inbox,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import { formatBytes, formatDate, formatCurrency } from '../utils/formatters';
import './DocumentsTable.css';

export default function DocumentsTable({ 
  documents = [], 
  isLoading = false, 
  onRefresh, 
  onOpenUpload,
  pageSize = 10 
}) {
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState(new Set());

  // Pagination calculation
  const totalDocs = documents.length;
  const totalPages = Math.ceil(totalDocs / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const currentDocs = documents.slice(startIndex, startIndex + pageSize);

  const toggleSelectAll = () => {
    if (selectedIds.size === currentDocs.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(currentDocs.map(d => d.documentId)));
    }
  };

  const toggleSelectDoc = (id) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  if (totalDocs === 0 && !isLoading) {
    return (
      <div className="table-empty-box" id="documents-empty-state">
        <div className="empty-icon-wrap">
          <Inbox size={32} />
        </div>
        <h3 className="empty-box-title">No documents found</h3>
        <p className="empty-box-desc">
          No invoices match your current filter, or your repository is empty.
        </p>
        {onOpenUpload && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={onOpenUpload}
          >
            Upload document
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="documents-table-wrapper" id="documents-table-container">
      <div className="table-scroll-container">
        <table className="documents-data-table" id="data-table">
          <thead>
            <tr>
              <th className="th-checkbox">
                <input
                  type="checkbox"
                  className="table-checkbox"
                  checked={currentDocs.length > 0 && selectedIds.size === currentDocs.length}
                  onChange={toggleSelectAll}
                  aria-label="Select all documents"
                />
              </th>
              <th className="th-doc">DOCUMENT</th>
              <th className="th-vendor">VENDOR</th>
              <th className="th-inv-num">INVOICE NUMBER</th>
              <th className="th-date">INVOICE DATE</th>
              <th className="th-amount">AMOUNT</th>
              <th className="th-status">STATUS</th>
              <th className="th-actions"></th>
            </tr>
          </thead>
          <tbody>
            {currentDocs.map((doc) => {
              const vendor = doc.vendor || doc.rawExtraction?.summaryFields?.vendorName?.value || '—';
              const invoiceNum = doc.invoiceNumber || doc.rawExtraction?.summaryFields?.invoiceNumber?.value || '—';
              const invoiceDate = doc.invoiceDate || doc.rawExtraction?.summaryFields?.invoiceDate?.value;
              const amount = doc.totalAmount ?? doc.rawExtraction?.summaryFields?.totalAmount?.value;
              const currency = doc.currency || doc.rawExtraction?.summaryFields?.currency?.value || 'USD';
              const isSelected = selectedIds.has(doc.documentId);

              return (
                <tr key={doc.documentId} className={`table-row ${isSelected ? 'row-selected' : ''}`}>
                  <td className="cell-checkbox">
                    <input
                      type="checkbox"
                      className="table-checkbox"
                      checked={isSelected}
                      onChange={() => toggleSelectDoc(doc.documentId)}
                      aria-label={`Select ${doc.fileName}`}
                    />
                  </td>

                  <td className="cell-doc">
                    <Link to={`/review/${doc.documentId}`} className="doc-item-link">
                      <div className="doc-icon-square">
                        <FileText size={15} />
                      </div>
                      <div className="doc-meta-info">
                        <span className="doc-filename" title={doc.fileName}>
                          {doc.fileName}
                        </span>
                        <span className="doc-details">
                          {doc.fileName?.toLowerCase().endsWith('.pdf') ? 'PDF' : 'Image'} · {formatBytes(doc.fileSizeBytes || 0)}
                        </span>
                      </div>
                    </Link>
                  </td>

                  <td className="cell-vendor">
                    <span className="text-cell" title={vendor}>{vendor}</span>
                  </td>

                  <td className="cell-inv-num tabular-nums">
                    <span className="text-cell">{invoiceNum}</span>
                  </td>

                  <td className="cell-date">
                    <span className="text-cell">
                      {invoiceDate ? formatDate(invoiceDate) : (doc.uploadedAt ? formatDate(doc.uploadedAt) : '—')}
                    </span>
                  </td>

                  <td className="cell-amount tabular-nums">
                    {amount !== undefined && amount !== null && amount !== '' ? (
                      formatCurrency(amount, currency)
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>

                  <td className="cell-status">
                    <StatusBadge status={doc.status} />
                  </td>

                  <td className="cell-actions">
                    <Link 
                      to={`/review/${doc.documentId}`} 
                      className="btn-table-action"
                      title="Review document"
                      aria-label="Review document"
                    >
                      <MoreHorizontal size={15} />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="table-pagination-footer">
        <div className="pagination-count-label">
          Showing {totalDocs > 0 ? startIndex + 1 : 0}–{Math.min(startIndex + pageSize, totalDocs)} of {totalDocs} documents
        </div>

        <div className="pagination-controls-row">
          <span className="pagination-page-size-label">Rows per page: {pageSize}</span>
          <div className="pagination-page-buttons">
            <button
              type="button"
              className="btn-page-nav"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              aria-label="Previous page"
            >
              ‹
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                type="button"
                className={`btn-page-number ${currentPage === page ? 'btn-page-active' : ''}`}
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </button>
            ))}
            <button
              type="button"
              className="btn-page-nav"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              aria-label="Next page"
            >
              ›
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
