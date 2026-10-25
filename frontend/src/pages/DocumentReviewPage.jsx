import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Save, 
  RotateCcw, 
  AlertTriangle, 
  CheckCircle2, 
  Eye, 
  ArrowLeft,
  Sparkles,
  ExternalLink,
  Plus,
  Trash2,
  Clock,
  ShieldCheck,
  Building2,
  Calendar,
  DollarSign,
  Layers,
  FileCheck
} from 'lucide-react';
import { apiService } from '../services/api';
import { formatBytes, formatDate, formatCurrency } from '../utils/formatters';
import StatusBadge from '../components/StatusBadge';
import './DocumentReviewPage.css';

export default function DocumentReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  // Editable Form State
  const [formData, setFormData] = useState({
    vendorName: '',
    invoiceNumber: '',
    invoiceDate: '',
    dueDate: '',
    subtotal: '',
    taxAmount: '',
    totalAmount: '',
    currency: 'USD',
    notes: ''
  });

  const [lineItems, setLineItems] = useState([]);
  const [confidenceMap, setConfidenceMap] = useState({});

  // Mutation State
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Fetch document details on mount
  useEffect(() => {
    let isMounted = true;

    async function loadDocument() {
      setIsLoading(true);
      setLoadError(null);
      try {
        const data = await apiService.getDocument(id);
        if (!isMounted) return;

        if (!data) {
          setLoadError(`Document with ID "${id}" was not found.`);
          setIsLoading(false);
          return;
        }

        setDocument(data);

        // Populate fields: prioritize correctedData if already reviewed, else rawExtraction
        const raw = data.rawExtraction || {};
        const summary = raw.summaryFields || {};
        const corrected = data.correctedData || {};

        setFormData({
          vendorName: corrected.vendorName ?? summary.vendorName?.value ?? '',
          invoiceNumber: corrected.invoiceNumber ?? summary.invoiceNumber?.value ?? '',
          invoiceDate: corrected.invoiceDate ?? summary.invoiceDate?.value ?? '',
          dueDate: corrected.dueDate ?? summary.dueDate?.value ?? '',
          subtotal: corrected.subtotal ?? summary.subtotal?.value ?? '',
          taxAmount: corrected.taxAmount ?? summary.taxAmount?.value ?? '',
          totalAmount: corrected.totalAmount ?? summary.totalAmount?.value ?? '',
          currency: corrected.currency ?? summary.currency?.value ?? 'USD',
          notes: corrected.notes ?? ''
        });

        // Line items
        if (corrected.lineItems && Array.isArray(corrected.lineItems) && corrected.lineItems.length > 0) {
          setLineItems(corrected.lineItems);
        } else if (raw.lineItems && Array.isArray(raw.lineItems)) {
          setLineItems(raw.lineItems);
        } else {
          setLineItems([]);
        }

        // Build confidence map from rawExtraction
        const confs = {};
        for (const [key, fieldObj] of Object.entries(summary)) {
          if (fieldObj && typeof fieldObj.confidence === 'number') {
            confs[key] = fieldObj.confidence;
          }
        }
        setConfidenceMap(confs);

      } catch (err) {
        if (!isMounted) return;
        setLoadError(err.message || 'Failed to load document details.');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    if (id) {
      loadDocument();
    } else {
      setIsLoading(false);
      setLoadError('No Document ID provided in route.');
    }

    return () => { isMounted = false; };
  }, [id]);

  // Form field change handler
  const handleFieldChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSaveSuccess(false);
  };

  // Line items handlers
  const handleLineItemChange = (index, field, value) => {
    setLineItems((prev) => {
      const updated = [...prev];
      const item = { ...updated[index], [field]: value };

      // Auto-recalculate line total if quantity or unitPrice changed
      if (field === 'quantity' || field === 'unitPrice') {
        const q = parseFloat(field === 'quantity' ? value : item.quantity) || 0;
        const p = parseFloat(field === 'unitPrice' ? value : item.unitPrice) || 0;
        item.totalPrice = Math.round(q * p * 100) / 100;
      }

      updated[index] = item;
      return updated;
    });
    setSaveSuccess(false);
  };

  const handleAddLineItem = () => {
    setLineItems((prev) => [
      ...prev,
      {
        description: '',
        quantity: 1,
        unitPrice: 0.0,
        totalPrice: 0.0,
        confidence: 100.0
      }
    ]);
  };

  const handleRemoveLineItem = (index) => {
    setLineItems((prev) => prev.filter((_, i) => i !== index));
    setSaveSuccess(false);
  };

  // Reset to original extraction
  const handleReset = () => {
    if (!document || !document.rawExtraction) return;
    const summary = document.rawExtraction.summaryFields || {};
    setFormData({
      vendorName: summary.vendorName?.value ?? '',
      invoiceNumber: summary.invoiceNumber?.value ?? '',
      invoiceDate: summary.invoiceDate?.value ?? '',
      dueDate: summary.dueDate?.value ?? '',
      subtotal: summary.subtotal?.value ?? '',
      taxAmount: summary.taxAmount?.value ?? '',
      totalAmount: summary.totalAmount?.value ?? '',
      currency: summary.currency?.value ?? 'USD',
      notes: ''
    });
    setLineItems(document.rawExtraction.lineItems || []);
    setSaveSuccess(false);
    setSaveError(null);
  };

  // Save corrections to DynamoDB via API Gateway PUT /documents/{id}/corrections
  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    setSaveError(null);

    const payload = {
      vendorName: formData.vendorName,
      invoiceNumber: formData.invoiceNumber,
      invoiceDate: formData.invoiceDate,
      dueDate: formData.dueDate,
      subtotal: formData.subtotal !== '' ? parseFloat(formData.subtotal) : null,
      taxAmount: formData.taxAmount !== '' ? parseFloat(formData.taxAmount) : null,
      totalAmount: formData.totalAmount !== '' ? parseFloat(formData.totalAmount) : null,
      currency: formData.currency,
      lineItems: lineItems.map((item) => ({
        description: item.description,
        quantity: parseInt(item.quantity, 10) || 1,
        unitPrice: item.unitPrice !== '' ? parseFloat(item.unitPrice) : null,
        totalPrice: item.totalPrice !== '' ? parseFloat(item.totalPrice) : null
      })),
      notes: formData.notes
    };

    try {
      const res = await apiService.saveCorrections(id, payload);
      setSaveSuccess(true);
      // Update local status badge
      setDocument((prev) => ({
        ...prev,
        status: 'REVIEWED',
        correctedData: payload,
        reviewedAt: new Date().toISOString()
      }));
    } catch (err) {
      setSaveError(err.message || 'Failed to persist corrections.');
    } finally {
      setIsSaving(false);
    }
  };

  // Helper to render confidence badges
  const renderConfidenceBadge = (fieldName) => {
    const conf = confidenceMap[fieldName];
    if (typeof conf !== 'number') return null;

    if (conf < 80) {
      return (
        <span className="conf-badge conf-low" title="Low OCR confidence. Please verify with document.">
          <AlertTriangle size={11} />
          <span>{conf.toFixed(1)}% Review</span>
        </span>
      );
    }
    return (
      <span className="conf-badge conf-high" title="High confidence extraction">
        <CheckCircle2 size={11} />
        <span>{conf.toFixed(1)}%</span>
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="review-loading-state">
        <div className="review-spinner"></div>
        <h3>Loading document details from DynamoDB...</h3>
        <p>Fetching extraction fields and secure presigned S3 view stream.</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="review-error-card glass-card">
        <AlertTriangle size={32} className="error-icon" />
        <h3>Unable to Load Document</h3>
        <p>{loadError}</p>
        <Link to="/documents" className="btn-back">
          <ArrowLeft size={16} />
          <span>Back to Documents</span>
        </Link>
      </div>
    );
  }

  const isPdf = document?.fileName?.toLowerCase().endsWith('.pdf') || document?.contentType === 'application/pdf';

  return (
    <div className="review-page" id="document-review-page">
      {/* Top Header Bar */}
      <div className="review-header-bar">
        <div className="review-header-left">
          <Link to="/documents" className="btn-back" id="btn-back-to-documents">
            <ArrowLeft size={16} />
            <span>Documents</span>
          </Link>
          <div className="review-title-group">
            <h2 className="review-page-title">{document?.fileName || 'Invoice Document'}</h2>
            <span className="doc-id-pill" title={document?.documentId}>
              ID: {id?.slice(0, 8)}...
            </span>
          </div>
        </div>
        <div className="review-header-right">
          <StatusBadge status={document?.status || 'PENDING_REVIEW'} />
          <span className="phase-badge badge-active">Audit Verification Mode</span>
        </div>
      </div>

      {/* Success Notification Banner */}
      {saveSuccess && (
        <div className="glass-card save-success-banner" id="save-success-banner">
          <CheckCircle2 size={18} className="banner-icon-success" />
          <div className="banner-success-text">
            <strong>Corrections Saved to DynamoDB!</strong> Document status updated to <code>REVIEWED</code>. Original extraction is safely preserved.
          </div>
        </div>
      )}

      {/* Save Error Banner */}
      {saveError && (
        <div className="glass-card save-error-banner" id="save-error-banner">
          <AlertTriangle size={18} className="banner-icon-error" />
          <div className="banner-error-text">
            <strong>Save Failed:</strong> {saveError}
          </div>
        </div>
      )}

      {/* Dual Pane Workstation */}
      <div className="review-workstation-grid">
        {/* Left Pane: S3 Document Viewer */}
        <div className="glass-card viewer-pane" id="document-viewer-pane">
          <div className="pane-header">
            <div className="pane-title-group">
              <Eye size={18} className="pane-icon" />
              <h3 className="pane-title">Original Invoice</h3>
            </div>
            {document?.viewUrl && (
              <a 
                href={document.viewUrl} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="btn-open-external"
                title="Open original document in new browser tab"
              >
                <ExternalLink size={14} />
                <span>Open Full</span>
              </a>
            )}
          </div>

          <div className="viewer-canvas-wrapper">
            {document?.viewUrl ? (
              isPdf ? (
                <iframe
                  src={document.viewUrl}
                  title="Document Preview"
                  className="pdf-preview-frame"
                />
              ) : (
                <div className="image-preview-container">
                  <img 
                    src={document.viewUrl} 
                    alt={document?.fileName} 
                    className="image-preview"
                  />
                </div>
              )
            ) : (
              <div className="viewer-canvas-placeholder">
                <div className="viewer-placeholder-content">
                  <div className="canvas-icon-box">
                    <FileText size={44} />
                  </div>
                  <h4 className="canvas-placeholder-title">No Document View Available</h4>
                  <p className="canvas-placeholder-desc">
                    S3 presigned view URL could not be generated for key: <code>{document?.s3Key || 'N/A'}</code>
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="viewer-footer-info">
            <span className="file-meta-tag">
              <FileCheck size={13} />
              <span>{document?.fileName}</span>
            </span>
            <span className="file-meta-tag">
              {formatBytes(document?.fileSizeBytes || 0)}
            </span>
            <span className="file-meta-tag s3-tag">
              S3 ap-south-1
            </span>
          </div>
        </div>

        {/* Right Pane: Normalized Form & Human Corrections */}
        <div className="glass-card fields-pane" id="document-fields-pane">
          <div className="pane-header">
            <div className="pane-title-group">
              <Sparkles size={18} className="pane-icon" />
              <h3 className="pane-title">Verified Invoice Fields</h3>
            </div>
            <span className="immutability-badge" title="Original rawExtraction is preserved permanently for compliance.">
              <ShieldCheck size={13} />
              <span>Audit Immutability Guard</span>
            </span>
          </div>

          <p className="pane-instruction">
            Verify the extracted invoice fields. Fields with low OCR confidence are highlighted in amber for human inspection.
          </p>

          <form className="extraction-form" onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
            <div className="form-grid">
              {/* Vendor Name */}
              <div className="form-group form-group-full">
                <label className="form-label" htmlFor="input-vendor-name">
                  <span>Vendor / Company Name</span>
                  {renderConfidenceBadge('vendorName')}
                </label>
                <div className="input-with-icon">
                  <Building2 size={15} className="input-icon" />
                  <input
                    id="input-vendor-name"
                    type="text"
                    className={`form-input has-icon ${confidenceMap.vendorName < 80 ? 'input-warning' : ''}`}
                    value={formData.vendorName}
                    onChange={(e) => handleFieldChange('vendorName', e.target.value)}
                    placeholder="Enter vendor name..."
                  />
                </div>
              </div>

              {/* Invoice Number */}
              <div className="form-group">
                <label className="form-label" htmlFor="input-invoice-number">
                  <span>Invoice Number</span>
                  {renderConfidenceBadge('invoiceNumber')}
                </label>
                <input
                  id="input-invoice-number"
                  type="text"
                  className={`form-input ${confidenceMap.invoiceNumber < 80 ? 'input-warning' : ''}`}
                  value={formData.invoiceNumber}
                  onChange={(e) => handleFieldChange('invoiceNumber', e.target.value)}
                  placeholder="e.g. INV-2026-001"
                />
              </div>

              {/* Invoice Date */}
              <div className="form-group">
                <label className="form-label" htmlFor="input-invoice-date">
                  <span>Invoice Date</span>
                  {renderConfidenceBadge('invoiceDate')}
                </label>
                <div className="input-with-icon">
                  <Calendar size={15} className="input-icon" />
                  <input
                    id="input-invoice-date"
                    type="text"
                    className={`form-input has-icon ${confidenceMap.invoiceDate < 80 ? 'input-warning' : ''}`}
                    value={formData.invoiceDate}
                    onChange={(e) => handleFieldChange('invoiceDate', e.target.value)}
                    placeholder="YYYY-MM-DD"
                  />
                </div>
              </div>

              {/* Payment Due Date */}
              <div className="form-group">
                <label className="form-label" htmlFor="input-due-date">
                  <span>Due Date</span>
                  {renderConfidenceBadge('dueDate')}
                </label>
                <input
                  id="input-due-date"
                  type="text"
                  className={`form-input ${confidenceMap.dueDate < 80 ? 'input-warning' : ''}`}
                  value={formData.dueDate}
                  onChange={(e) => handleFieldChange('dueDate', e.target.value)}
                  placeholder="YYYY-MM-DD"
                />
              </div>

              {/* Currency */}
              <div className="form-group">
                <label className="form-label" htmlFor="input-currency">
                  <span>Currency</span>
                  {renderConfidenceBadge('currency')}
                </label>
                <select
                  id="input-currency"
                  className="form-input form-select"
                  value={formData.currency}
                  onChange={(e) => handleFieldChange('currency', e.target.value)}
                >
                  <option value="USD">USD ($)</option>
                  <option value="INR">INR (₹)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>

              {/* Subtotal */}
              <div className="form-group">
                <label className="form-label" htmlFor="input-subtotal">
                  <span>Subtotal Amount</span>
                  {renderConfidenceBadge('subtotal')}
                </label>
                <input
                  id="input-subtotal"
                  type="number"
                  step="0.01"
                  className={`form-input ${confidenceMap.subtotal < 80 ? 'input-warning' : ''}`}
                  value={formData.subtotal}
                  onChange={(e) => handleFieldChange('subtotal', e.target.value)}
                  placeholder="0.00"
                />
              </div>

              {/* Tax Amount */}
              <div className="form-group">
                <label className="form-label" htmlFor="input-tax">
                  <span>Tax Amount</span>
                  {renderConfidenceBadge('taxAmount')}
                </label>
                <input
                  id="input-tax"
                  type="number"
                  step="0.01"
                  className={`form-input ${confidenceMap.taxAmount < 80 ? 'input-warning' : ''}`}
                  value={formData.taxAmount}
                  onChange={(e) => handleFieldChange('taxAmount', e.target.value)}
                  placeholder="0.00"
                />
              </div>

              {/* Total Amount */}
              <div className="form-group form-group-full">
                <label className="form-label" htmlFor="input-total">
                  <span>Total Due (Final)</span>
                  {renderConfidenceBadge('totalAmount')}
                </label>
                <div className="input-with-icon">
                  <DollarSign size={16} className="input-icon total-icon" />
                  <input
                    id="input-total"
                    type="number"
                    step="0.01"
                    className="form-input has-icon total-input"
                    value={formData.totalAmount}
                    onChange={(e) => handleFieldChange('totalAmount', e.target.value)}
                    placeholder="0.00"
                  />
                </div>
              </div>
            </div>

            {/* Line Items Table Section */}
            <div className="line-items-section">
              <div className="line-items-header">
                <h4 className="line-items-title">Invoice Line Items</h4>
                <button
                  type="button"
                  onClick={handleAddLineItem}
                  className="btn-add-item"
                  id="btn-add-line-item"
                >
                  <Plus size={14} />
                  <span>Add Line Item</span>
                </button>
              </div>

              {lineItems.length === 0 ? (
                <div className="line-items-empty">
                  No line items extracted. Click <strong>Add Line Item</strong> to add items manually.
                </div>
              ) : (
                <div className="line-items-table-wrapper">
                  <table className="line-items-table">
                    <thead>
                      <tr>
                        <th>Description</th>
                        <th style={{ width: '80px' }}>Qty</th>
                        <th style={{ width: '110px' }}>Unit Price</th>
                        <th style={{ width: '110px' }}>Total</th>
                        <th style={{ width: '40px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {lineItems.map((item, idx) => (
                        <tr key={idx}>
                          <td>
                            <input
                              type="text"
                              className="table-input"
                              value={item.description || ''}
                              onChange={(e) => handleLineItemChange(idx, 'description', e.target.value)}
                              placeholder="Item description..."
                            />
                          </td>
                          <td>
                            <input
                              type="number"
                              className="table-input"
                              value={item.quantity || 1}
                              onChange={(e) => handleLineItemChange(idx, 'quantity', e.target.value)}
                            />
                          </td>
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              className="table-input"
                              value={item.unitPrice ?? ''}
                              onChange={(e) => handleLineItemChange(idx, 'unitPrice', e.target.value)}
                              placeholder="0.00"
                            />
                          </td>
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              className="table-input"
                              value={item.totalPrice ?? ''}
                              onChange={(e) => handleLineItemChange(idx, 'totalPrice', e.target.value)}
                              placeholder="0.00"
                            />
                          </td>
                          <td className="cell-actions">
                            <button
                              type="button"
                              className="btn-remove-row"
                              onClick={() => handleRemoveLineItem(idx)}
                              title="Remove item"
                            >
                              <Trash2 size={14} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Auditor Notes */}
            <div className="form-group form-group-full notes-group">
              <label className="form-label" htmlFor="input-notes">
                <span>Auditor / Review Notes</span>
              </label>
              <textarea
                id="input-notes"
                className="form-input form-textarea"
                rows={2}
                value={formData.notes}
                onChange={(e) => handleFieldChange('notes', e.target.value)}
                placeholder="Optional review notes (e.g., matched with PO-2026-99)..."
              />
            </div>

            {/* Action Buttons */}
            <div className="form-actions-bar">
              <button
                type="button"
                className="btn-save-corrections"
                id="btn-save-corrections"
                onClick={handleSave}
                disabled={isSaving}
              >
                <Save size={16} />
                <span>{isSaving ? 'Persisting to DynamoDB...' : 'Save & Mark Reviewed'}</span>
              </button>

              <button
                type="button"
                className="btn-reset-fields"
                id="btn-reset-fields"
                onClick={handleReset}
                disabled={isSaving}
                title="Discard edits and reload original Textract extraction"
              >
                <RotateCcw size={15} />
                <span>Reset to OCR</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
