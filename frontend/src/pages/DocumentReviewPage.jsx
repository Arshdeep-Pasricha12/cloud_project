import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  FileText, 
  Save, 
  RotateCcw, 
  AlertCircle, 
  ShieldCheck, 
  Eye, 
  ArrowLeft,
  Sparkles,
  HelpCircle,
  Clock
} from 'lucide-react';
import './DocumentReviewPage.css';

export default function DocumentReviewPage() {
  const { id } = useParams();

  return (
    <div className="review-page" id="document-review-page">
      {/* Top Navigation & Status */}
      <div className="review-header-bar">
        <div className="review-header-left">
          <Link to="/documents" className="btn-back" id="btn-back-to-documents">
            <ArrowLeft size={16} />
            <span>Back to Documents</span>
          </Link>
          <div className="review-title-group">
            <h2 className="review-page-title">Document Review & Verification</h2>
            <span className="doc-id-pill">
              ID: {id ? id : 'No Document Selected'}
            </span>
          </div>
        </div>
        <div className="review-header-right">
          <span className="phase-badge">Textract + DynamoDB · Phases 4 & 6</span>
        </div>
      </div>

      {/* Explicit Phase Disclosure Banner */}
      <div className="glass-card review-disclaimer-banner" id="review-phase-banner">
        <AlertCircle size={20} className="disclaimer-icon" />
        <div className="disclaimer-body">
          <h4 className="disclaimer-title">Workspace Structure Ready (AWS Integration Pending)</h4>
          <p className="disclaimer-text">
            This review page implements the dual-pane human-in-the-loop workstation structure.
            In compliance with project specifications, <strong>no fake invoice records, hardcoded vendor names, or simulated extractions</strong> are presented.
            Real values will be extracted using <strong>Amazon Textract AnalyzeExpense</strong> in Milestone 4, and corrections will be persisted to <strong>DynamoDB</strong> in Milestone 6.
          </p>
        </div>
      </div>

      {/* Dual Pane Layout: Left = Document Canvas; Right = Normalized Form */}
      <div className="review-workstation-grid">
        {/* Left Pane: S3 Document Viewer Placeholder */}
        <div className="glass-card viewer-pane" id="document-viewer-pane">
          <div className="pane-header">
            <div className="pane-title-group">
              <Eye size={18} className="pane-icon" />
              <h3 className="pane-title">Original Document Viewer</h3>
            </div>
            <span className="phase-badge info">S3 Presigned GET · Phase 5</span>
          </div>

          <div className="viewer-canvas-placeholder">
            <div className="viewer-placeholder-content">
              <div className="canvas-icon-box">
                <FileText size={48} />
              </div>
              <h4 className="canvas-placeholder-title">No Document Loaded</h4>
              <p className="canvas-placeholder-desc">
                When a document is selected, a secure, time-limited presigned GET URL will stream the original PDF or image directly from the private Amazon S3 bucket.
              </p>
              <div className="canvas-tech-tag">
                <span>Direct S3 Presigned GET · 15m Expiry</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Pane: Normalized Extraction & Corrections Form */}
        <div className="glass-card fields-pane" id="document-fields-pane">
          <div className="pane-header">
            <div className="pane-title-group">
              <Sparkles size={18} className="pane-icon" />
              <h3 className="pane-title">Extracted Invoice Fields</h3>
            </div>
            <span className="phase-badge ready">Separate Corrections Guard</span>
          </div>

          <p className="pane-instruction">
            Verify extracted fields against the original invoice. Low-confidence fields will be highlighted once Textract is active.
          </p>

          <form className="extraction-form" onSubmit={(e) => e.preventDefault()}>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="field-vendor" className="form-label">
                  Vendor Name
                  <span className="label-phase-hint">(Textract VENDOR_NAME)</span>
                </label>
                <input
                  id="field-vendor"
                  type="text"
                  className="form-input"
                  placeholder="Awaiting Textract extraction..."
                  disabled
                />
              </div>

              <div className="form-group">
                <label htmlFor="field-invoice-num" className="form-label">
                  Invoice Number
                  <span className="label-phase-hint">(Textract INVOICE_RECEIPT_ID)</span>
                </label>
                <input
                  id="field-invoice-num"
                  type="text"
                  className="form-input"
                  placeholder="Awaiting Textract extraction..."
                  disabled
                />
              </div>

              <div className="form-group">
                <label htmlFor="field-invoice-date" className="form-label">
                  Invoice Date
                  <span className="label-phase-hint">(Textract INVOICE_RECEIPT_DATE)</span>
                </label>
                <input
                  id="field-invoice-date"
                  type="text"
                  className="form-input"
                  placeholder="YYYY-MM-DD"
                  disabled
                />
              </div>

              <div className="form-group">
                <label htmlFor="field-due-date" className="form-label">
                  Payment Due Date
                  <span className="label-phase-hint">(Textract DUE_DATE)</span>
                </label>
                <input
                  id="field-due-date"
                  type="text"
                  className="form-input"
                  placeholder="YYYY-MM-DD"
                  disabled
                />
              </div>

              <div className="form-group">
                <label htmlFor="field-subtotal" className="form-label">
                  Subtotal Amount ($)
                  <span className="label-phase-hint">(Textract SUBTOTAL)</span>
                </label>
                <input
                  id="field-subtotal"
                  type="text"
                  className="form-input"
                  placeholder="0.00"
                  disabled
                />
              </div>

              <div className="form-group">
                <label htmlFor="field-tax" className="form-label">
                  Tax Amount ($)
                  <span className="label-phase-hint">(Textract TAX)</span>
                </label>
                <input
                  id="field-tax"
                  type="text"
                  className="form-input"
                  placeholder="0.00"
                  disabled
                />
              </div>

              <div className="form-group form-group-full">
                <label htmlFor="field-total" className="form-label highlight-label">
                  Total Amount ($)
                  <span className="label-phase-hint">(Textract TOTAL)</span>
                </label>
                <input
                  id="field-total"
                  type="text"
                  className="form-input total-input"
                  placeholder="0.00"
                  disabled
                />
              </div>
            </div>

            {/* Line Items Placeholder */}
            <div className="line-items-section">
              <div className="line-items-header">
                <h4 className="line-items-title">Extracted Line Items</h4>
                <span className="phase-badge info">LineItemGroup · Phase 4</span>
              </div>
              <div className="line-items-empty">
                <p>Line item table will populate with item descriptions, unit prices, and quantities from Textract.</p>
              </div>
            </div>

            {/* Form Action Controls */}
            <div className="form-actions-bar">
              <button
                type="button"
                id="btn-save-corrections"
                className="btn btn-primary"
                disabled
                title="DynamoDB persistence will be enabled in Milestone 6"
              >
                <Save size={16} />
                <span>Save Corrections (Phase 6)</span>
              </button>

              <button
                type="button"
                id="btn-discard-changes"
                className="btn btn-secondary"
                disabled
              >
                <RotateCcw size={16} />
                <span>Reset to Raw Extraction</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
