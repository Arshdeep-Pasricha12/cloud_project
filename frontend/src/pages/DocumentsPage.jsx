import React, { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import DocumentsTable from '../components/DocumentsTable';
import { useDocuments } from '../hooks/useDocuments';
import { useAuth } from '../context/AuthContext';
import { exportDocumentsToCsv } from '../utils/exportUtils';
import { 
  Plus, 
  Search, 
  Filter, 
  ChevronDown,
  CheckCircle2,
  Calendar,
  Download,
  LogIn,
  DollarSign,
  TrendingUp
} from 'lucide-react';
import { formatCurrency } from '../utils/formatters';
import './DocumentsPage.css';

export default function DocumentsPage({ 
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

  const { isAuthenticated, openAuthModal } = useAuth();

  const [searchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || '';

  const [searchTerm, setSearchTerm] = useState(initialSearch);
  const [statusTab, setStatusTab] = useState('ALL'); // ALL | PENDING_REVIEW | PROCESSING | REVIEWED | FAILED
  const [vendorFilter, setVendorFilter] = useState('ALL');

  // Total spend calculation for real-world financial KPI
  const totalSpend = useMemo(() => {
    return documents.reduce((sum, d) => {
      const val = parseFloat(d.totalAmount ?? d.rawExtraction?.summaryFields?.totalAmount?.value) || 0;
      return sum + val;
    }, 0);
  }, [documents]);

  // Extract unique vendors for filter dropdown
  const uniqueVendors = useMemo(() => {
    const set = new Set();
    documents.forEach((doc) => {
      const v = doc.vendor || doc.rawExtraction?.summaryFields?.vendorName?.value;
      if (v && typeof v === 'string' && v.trim()) {
        set.add(v.trim());
      }
    });
    return Array.from(set).sort();
  }, [documents]);

  // Compute status counts
  const counts = useMemo(() => {
    const c = {
      ALL: documents.length,
      PENDING_REVIEW: 0,
      PROCESSING: 0,
      REVIEWED: 0,
      FAILED: 0
    };
    documents.forEach((doc) => {
      if (c[doc.status] !== undefined) {
        c[doc.status]++;
      }
    });
    return c;
  }, [documents]);

  // Filtered documents
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Status filter
      if (statusTab !== 'ALL' && doc.status !== statusTab) {
        return false;
      }

      // Vendor filter
      if (vendorFilter !== 'ALL') {
        const docVendor = doc.vendor || doc.rawExtraction?.summaryFields?.vendorName?.value || '';
        if (docVendor !== vendorFilter) return false;
      }

      // Search term filter
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const fileName = (doc.fileName || '').toLowerCase();
        const vendor = (doc.vendor || doc.rawExtraction?.summaryFields?.vendorName?.value || '').toLowerCase();
        const invoiceNum = (doc.invoiceNumber || doc.rawExtraction?.summaryFields?.invoiceNumber?.value || '').toLowerCase();
        if (!fileName.includes(query) && !vendor.includes(query) && !invoiceNum.includes(query)) {
          return false;
        }
      }

      return true;
    });
  }, [documents, statusTab, vendorFilter, searchTerm]);

  return (
    <div className="documents-page" id="documents-page">
      {/* Header Row */}
      <div className="documents-header-row">
        <div>
          <h1 className="page-title">Documents</h1>
          <p className="page-subtitle">All your invoices and receipts in one place.</p>
        </div>
        <div className="documents-header-actions-group">
          <button
            type="button"
            className="btn btn-secondary"
            id="btn-documents-export-csv"
            onClick={() => exportDocumentsToCsv(filteredDocuments)}
            title="Download CSV report of documents"
          >
            <Download size={14} />
            <span>Export CSV</span>
          </button>
          <button
            type="button"
            className="btn btn-primary"
            id="btn-documents-upload"
            onClick={onOpenUpload}
          >
            <Plus size={15} />
            <span>Upload document</span>
          </button>
        </div>
      </div>

      {/* Unauthenticated Workspace Session Banner */}
      {!isAuthenticated && (
        <div className="documents-auth-notice" id="documents-auth-notice">
          <div className="auth-notice-text">
            <strong>Workspace Session Notice:</strong> You are currently viewing in guest mode. Sign in to your verified account (arshdeepforwork@gmail.com) to access all cloud invoices and your review queue.
          </div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => openAuthModal('signin')}
            id="btn-documents-signin"
          >
            <LogIn size={13} />
            <span>Sign In</span>
          </button>
        </div>
      )}

      {/* Main Working Panel */}
      <div className="documents-working-card">
        {/* Status Filter Tabs */}
        <div className="status-tabs-row">
          <button
            type="button"
            className={`tab-btn ${statusTab === 'ALL' ? 'tab-btn-active' : ''}`}
            onClick={() => setStatusTab('ALL')}
          >
            All documents <span className="tab-count">{counts.ALL}</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${statusTab === 'PENDING_REVIEW' ? 'tab-btn-active' : ''}`}
            onClick={() => setStatusTab('PENDING_REVIEW')}
          >
            Needs review <span className="tab-count">{counts.PENDING_REVIEW}</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${statusTab === 'PROCESSING' ? 'tab-btn-active' : ''}`}
            onClick={() => setStatusTab('PROCESSING')}
          >
            Processing <span className="tab-count">{counts.PROCESSING}</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${statusTab === 'REVIEWED' ? 'tab-btn-active' : ''}`}
            onClick={() => setStatusTab('REVIEWED')}
          >
            Reviewed <span className="tab-count">{counts.REVIEWED}</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${statusTab === 'FAILED' ? 'tab-btn-active' : ''}`}
            onClick={() => setStatusTab('FAILED')}
          >
            Failed <span className="tab-count">{counts.FAILED}</span>
          </button>
        </div>

        {/* Search & Filter Controls Toolbar */}
        <div className="table-filter-toolbar">
          <div className="table-search-box">
            <Search size={14} className="search-icon" />
            <input
              id="input-document-search"
              type="text"
              className="table-search-input"
              placeholder="Search by filename, vendor or invoice number"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="table-filter-dropdowns">
            {/* Vendor select */}
            <div className="select-wrap">
              <select
                id="select-vendor-filter"
                className="filter-select"
                value={vendorFilter}
                onChange={(e) => setVendorFilter(e.target.value)}
              >
                <option value="ALL">All vendors</option>
                {uniqueVendors.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
              <ChevronDown size={13} className="select-arrow" />
            </div>

            {/* Date filter placeholder dropdown */}
            <div className="select-wrap">
              <select
                id="select-date-filter"
                className="filter-select"
                defaultValue="ANY"
              >
                <option value="ANY">Any date</option>
                <option value="TODAY">Today</option>
                <option value="WEEK">This week</option>
                <option value="MONTH">This month</option>
              </select>
              <ChevronDown size={13} className="select-arrow" />
            </div>

            <button
              type="button"
              className="btn btn-secondary btn-sm btn-filter-pill"
              title="Filter"
            >
              <Filter size={13} />
              <span>Filter</span>
            </button>
          </div>
        </div>

        {/* Data Table */}
        <DocumentsTable 
          documents={filteredDocuments} 
          isLoading={isLoading} 
          onRefresh={refreshDocuments}
          onOpenUpload={onOpenUpload}
        />
      </div>

      {/* Footnote */}
      <div className="page-footnote">
        <CheckCircle2 size={13} className="page-footnote-icon" />
        <span>Open any document to view the source file alongside its extracted fields.</span>
      </div>
    </div>
  );
}
