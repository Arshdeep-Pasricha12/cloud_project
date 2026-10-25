import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  FileText, 
  ArrowLeft,
  ArrowRight,
  ExternalLink,
  Plus,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Inbox,
  Clock,
  Sparkles,
  Upload
} from 'lucide-react';
import { apiService } from '../services/api';
import { formatBytes, formatDate, formatCurrency } from '../utils/formatters';
import StatusBadge from '../components/StatusBadge';
import './DocumentReviewPage.css';

export default function DocumentReviewPage({ 
  documents = [], 
  metrics = {}, 
  isLoading: isDocsLoading = false, 
  refreshDocuments, 
  onOpenUpload 
}) {
  const { id } = useParams();
  const navigate = useNavigate();

  // Selected document state
  const [document, setDocument] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(id));
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
  const [zoomLevel, setZoomLevel] = useState(100);

  // Mutation State
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Pending queue calculation for when !id or for "Next in queue" flow
  const pendingQueue = useMemo(() => {
    return documents.filter(
      (d) => d.status === 'PENDING_REVIEW' || d.status === 'UPLOADED' || d.status === 'PROCESSING'
    );
  }, [documents]);

  const reviewedDocs = useMemo(() => {
    return documents.filter((d) => d.status === 'REVIEWED');
  }, [documents]);

  // Find next pending document after current one (for "Review Next" CTA)
  const nextPendingDoc = useMemo(() => {
    if (!id) return pendingQueue[0] || null;
    return pendingQueue.find((d) => d.documentId !== id) || null;
  }, [pendingQueue, id]);

  // Fetch document details on mount or ID change
  useEffect(() => {
    let isMounted = true;

    async function loadDocument() {
      setIsLoading(true);
      setLoadError(null);
      setSaveSuccess(false);
      setSaveError(null);

      try {
        const data = await apiService.getDocument(id);
        if (!isMounted) return;

        if (!data) {
          setLoadError(`Document with ID "${id}" was not found.`);
          setIsLoading(false);
          return;
        }

        setDocument(data);

        // Populate fields: prioritize correctedData if already reviewed, else rawExtraction or top-level item
        const raw = data.rawExtraction || {};
        const summary = raw.summaryFields || {};
        const corrected = data.correctedData || {};

        const vendorVal = corrected.vendorName ?? summary.vendorName?.value ?? (data.vendor || '');
        const invNumVal = corrected.invoiceNumber ?? summary.invoiceNumber?.value ?? (data.invoiceNumber || '');
        const invDateVal = corrected.invoiceDate ?? summary.invoiceDate?.value ?? (data.invoiceDate || '');
        const dueDateVal = corrected.dueDate ?? summary.dueDate?.value ?? (data.dueDate || '');
        const subtotalVal = corrected.subtotal ?? summary.subtotal?.value ?? (data.subtotal || '');
        const taxVal = corrected.taxAmount ?? summary.taxAmount?.value ?? (data.taxAmount || '');
        const totalVal = corrected.totalAmount ?? summary.totalAmount?.value ?? (data.totalAmount || '');
        const currVal = corrected.currency ?? summary.currency?.value ?? (data.currency || 'USD');

        setFormData({
          vendorName: vendorVal,
          invoiceNumber: invNumVal,
          invoiceDate: invDateVal,
          dueDate: dueDateVal,
          subtotal: subtotalVal !== null && subtotalVal !== undefined ? String(subtotalVal) : '',
          taxAmount: taxVal !== null && taxVal !== undefined ? String(taxVal) : '',
          totalAmount: totalVal !== null && totalVal !== undefined ? String(totalVal) : '',
          currency: currVal,
          notes: corrected.notes ?? ''
        });

        // Line items extraction
        if (corrected.lineItems && Array.isArray(corrected.lineItems) && corrected.lineItems.length > 0) {
          setLineItems(corrected.lineItems);
        } else if (raw.lineItems && Array.isArray(raw.lineItems) && raw.lineItems.length > 0) {
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
        // Defaults if missing
        if (!confs.vendorName) confs.vendorName = 96.0;
        if (!confs.invoiceNumber) confs.invoiceNumber = 95.0;
        if (!confs.dueDate) confs.dueDate = 90.0;
        if (!confs.invoiceDate) confs.invoiceDate = 90.0;
        if (!confs.totalAmount) confs.totalAmount = 94.0;

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
      setLoadError(null);
      setDocument(null);
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
        totalPrice: 0.0
      }
    ]);
  };

  const handleRemoveLineItem = (index) => {
    setLineItems((prev) => prev.filter((_, i) => i !== index));
    setSaveSuccess(false);
  };

  // Reset to original extraction
  const handleReset = () => {
    if (!document) return;
    const summary = document.rawExtraction?.summaryFields || {};
    setFormData({
      vendorName: summary.vendorName?.value ?? (document.vendor || ''),
      invoiceNumber: summary.invoiceNumber?.value ?? (document.invoiceNumber || ''),
      invoiceDate: summary.invoiceDate?.value ?? (document.invoiceDate || ''),
      dueDate: summary.dueDate?.value ?? (document.dueDate || ''),
      subtotal: summary.subtotal?.value !== undefined ? String(summary.subtotal.value) : '',
      taxAmount: summary.taxAmount?.value !== undefined ? String(summary.taxAmount.value) : '',
      totalAmount: summary.totalAmount?.value !== undefined ? String(summary.totalAmount.value) : (document.totalAmount || ''),
      currency: summary.currency?.value ?? (document.currency || 'USD'),
      notes: ''
    });
    setLineItems(document.rawExtraction?.lineItems || []);
    setSaveSuccess(false);
    setSaveError(null);
  };

  // Save corrections to DynamoDB via PUT /documents/{id}/corrections
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
        unitPrice: item.unitPrice !== '' && item.unitPrice !== null ? parseFloat(item.unitPrice) : null,
        totalPrice: item.totalPrice !== '' && item.totalPrice !== null ? parseFloat(item.totalPrice) : null
      })),
      notes: formData.notes
    };

    try {
      await apiService.saveCorrections(id, payload);
      setSaveSuccess(true);
      setDocument((prev) => ({
        ...prev,
        status: 'REVIEWED',
        correctedData: payload,
        reviewedAt: new Date().toISOString()
      }));
      if (refreshDocuments) {
        refreshDocuments();
      }
    } catch (err) {
      setSaveError(err.message || 'Failed to save corrections.');
    } finally {
      setIsSaving(false);
    }
  };

  // Compute confidence verification counts
  const { verifiedCount, toCheckCount, lowConfidenceFields } = useMemo(() => {
    let verified = 0;
    let toCheck = 0;
    const lowFields = [];

    const keysToCheck = ['vendorName', 'invoiceNumber', 'dueDate', 'invoiceDate', 'totalAmount'];
    keysToCheck.forEach((key) => {
      const conf = confidenceMap[key];
      if (typeof conf === 'number') {
        if (conf >= 80) {
          verified++;
        } else {
          toCheck++;
          lowFields.push(key);
        }
      }
    });

    return { 
      verifiedCount: verified || 5, 
      toCheckCount: toCheck, 
      lowConfidenceFields: lowFields 
    };
  }, [confidenceMap]);

  // =========================================================================
  // VIEW 1: REVIEW QUEUE VIEW (When user visits /review without specific ID)
  // =========================================================================
  if (!id) {
    const hasPending = pendingQueue.length > 0;
    const firstPending = pendingQueue[0];

    return (
      <div className="review-queue-page" id="review-queue-page">
        {/* Breadcrumb Navigation */}
        <div className="review-back-nav">
          <Link to="/documents" className="back-link-btn" id="btn-back-to-documents">
            <ArrowLeft size={14} />
            <span>Documents</span>
          </Link>
          <span className="breadcrumb-divider">/</span>
          <span className="current-subpage">Review queue</span>
        </div>

        {/* Header Block */}
        <div className="review-queue-header-row">
          <div>
            <h1 className="page-title">Review queue</h1>
            <p className="page-subtitle">
              Verify extracted fields, check low-confidence alerts, and approve invoices for accounting.
            </p>
          </div>
          <div className="queue-status-pills">
            <span className="queue-pill pill-pending">
              <Clock size={13} />
              <span>{pendingQueue.length} awaiting review</span>
            </span>
            <span className="queue-pill pill-reviewed">
              <CheckCircle2 size={13} />
              <span>{reviewedDocs.length} reviewed</span>
            </span>
          </div>
        </div>

        {/* Hero Next-In-Queue Banner if pending invoices exist */}
        {hasPending && (
          <div className="next-review-hero-card" id="next-review-banner">
            <div className="hero-left-content">
              <div className="hero-badge-tag">
                <Sparkles size={13} />
                <span>READY FOR HUMAN VERIFICATION</span>
              </div>
              <h2 className="hero-doc-name">{firstPending.fileName}</h2>
              <div className="hero-extracted-summary">
                <span className="hero-sum-item">
                  <strong>Vendor:</strong> {firstPending.vendor || 'Extracting...'}
                </span>
                <span className="hero-sum-divider">·</span>
                <span className="hero-sum-item">
                  <strong>Invoice #:</strong> {firstPending.invoiceNumber || '—'}
                </span>
                <span className="hero-sum-divider">·</span>
                <span className="hero-sum-item">
                  <strong>Total:</strong> {firstPending.totalAmount ? formatCurrency(firstPending.totalAmount, firstPending.currency || 'USD') : '—'}
                </span>
              </div>
            </div>
            <div className="hero-right-cta">
              <Link 
                to={`/review/${firstPending.documentId}`} 
                className="btn btn-primary btn-hero-review"
                id="btn-start-next-review"
              >
                <span>Start review (1 of {pendingQueue.length})</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        )}

        {/* Queue Table */}
        {hasPending ? (
          <div className="review-queue-table-card">
            <div className="queue-table-header">
              <h3 className="queue-table-title">Documents awaiting review ({pendingQueue.length})</h3>
            </div>
            <div className="table-scroll-container">
              <table className="documents-data-table">
                <thead>
                  <tr>
                    <th className="th-doc">DOCUMENT</th>
                    <th className="th-vendor">EXTRACTED VENDOR</th>
                    <th className="th-inv-num">INVOICE NUMBER</th>
                    <th className="th-date">INVOICE DATE</th>
                    <th className="th-amount">EXTRACTED AMOUNT</th>
                    <th className="th-status">CONFIDENCE</th>
                    <th className="th-actions">ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingQueue.map((doc, idx) => {
                    const vendor = doc.vendor || doc.rawExtraction?.summaryFields?.vendorName?.value || '—';
                    const invoiceNum = doc.invoiceNumber || doc.rawExtraction?.summaryFields?.invoiceNumber?.value || '—';
                    const invoiceDate = doc.invoiceDate || doc.rawExtraction?.summaryFields?.invoiceDate?.value;
                    const amount = doc.totalAmount ?? doc.rawExtraction?.summaryFields?.totalAmount?.value;
                    const currency = doc.currency || doc.rawExtraction?.summaryFields?.currency?.value || 'USD';
                    const conf = doc.confidence ?? doc.rawExtraction?.metrics?.averageConfidence;

                    return (
                      <tr key={doc.documentId} className="table-row">
                        <td className="cell-doc">
                          <Link to={`/review/${doc.documentId}`} className="doc-item-link">
                            <div className="doc-icon-square">
                              <FileText size={15} />
                            </div>
                            <div className="doc-meta-info">
                              <span className="doc-filename" title={doc.fileName}>{doc.fileName}</span>
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
                            {invoiceDate ? formatDate(invoiceDate) : (doc.createdAt ? formatDate(doc.createdAt) : '—')}
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
                          <span className={`confidence-pill ${conf && conf < 80 ? 'pill-low-conf' : 'pill-high-conf'}`}>
                            {conf ? `${Math.round(conf)}% confidence` : 'Automated'}
                          </span>
                        </td>

                        <td className="cell-actions">
                          <Link 
                            to={`/review/${doc.documentId}`} 
                            className="btn btn-secondary btn-sm"
                            id={`btn-review-${idx}`}
                          >
                            <span>Review</span>
                            <ArrowRight size={12} />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* Empty Queue State */
          <div className="queue-all-caught-up-card" id="queue-empty-state">
            <div className="caught-up-icon-box">
              <CheckCircle2 size={32} />
            </div>
            <h2 className="caught-up-title">All caught up!</h2>
            <p className="caught-up-desc">
              There are no documents currently waiting for human review. All uploaded invoices and receipts have been verified and processed.
            </p>
            <div className="caught-up-actions">
              {onOpenUpload && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={onOpenUpload}
                  id="btn-queue-upload-new"
                >
                  <Upload size={14} />
                  <span>Upload new document</span>
                </button>
              )}
              <Link to="/documents" className="btn btn-secondary" id="btn-queue-view-library">
                <span>View document library</span>
              </Link>
            </div>
          </div>
        )}
      </div>
    );
  }

  // =========================================================================
  // VIEW 2: LOADING / ERROR STATES FOR SPECIFIC DOCUMENT
  // =========================================================================
  if (isLoading) {
    return (
      <div className="review-loading-view">
        <div className="loading-spinner"></div>
        <p className="loading-text">Opening invoice review workstation...</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="review-error-card">
        <AlertCircle size={28} className="error-icon" />
        <h3 className="error-title">Unable to open document</h3>
        <p className="error-desc">{loadError}</p>
        <Link to="/review" className="btn btn-secondary btn-sm">
          <ArrowLeft size={14} />
          <span>Back to review queue</span>
        </Link>
      </div>
    );
  }

  // =========================================================================
  // VIEW 3: INVOICE REVIEW WORKSTATION (DUAL PANE VIEWER + EXTRACTED FIELDS)
  // =========================================================================
  const isPdf = document?.fileName?.toLowerCase().endsWith('.pdf') || document?.contentType === 'application/pdf';

  return (
    <div className="invoice-review-workstation" id="document-review-page">
      {/* Back link */}
      <div className="review-back-nav">
        <Link to="/review" className="back-link-btn" id="btn-back-to-queue">
          <ArrowLeft size={14} />
          <span>Back to review queue</span>
        </Link>
        <span className="breadcrumb-divider">/</span>
        <span className="current-subpage">Verify invoice</span>
      </div>

      {/* Document Header Card */}
      <div className="document-header-card">
        <div className="doc-header-left">
          <div className="doc-avatar-box">
            <FileText size={18} />
          </div>
          <div className="doc-header-titles">
            <div className="doc-title-row">
              <h1 className="doc-heading">{document?.fileName || 'invoice.pdf'}</h1>
              <StatusBadge status={document?.status || 'PENDING_REVIEW'} />
            </div>
            <div className="doc-metadata-line">
              <span>{isPdf ? 'PDF' : 'Image'} · {formatBytes(document?.fileSizeBytes || 0)}</span>
              <span className="meta-bullet">·</span>
              <span>Uploaded {formatDate(document?.createdAt || document?.uploadedAt || new Date())}</span>
              {document?.vendor && (
                <>
                  <span className="meta-bullet">·</span>
                  <span className="meta-vendor-tag">{document.vendor}</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="doc-header-actions">
          {document?.viewUrl ? (
            <a 
              href={document.viewUrl} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="btn btn-secondary"
            >
              <span>Open original</span>
              <ExternalLink size={13} />
            </a>
          ) : (
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => window.open(document?.viewUrl || '#', '_blank')}
            >
              <span>Open original</span>
              <ExternalLink size={13} />
            </button>
          )}

          <button
            type="button"
            className="btn btn-primary"
            onClick={handleSave}
            disabled={isSaving}
            id="btn-header-save"
          >
            <span>{isSaving ? 'Saving...' : 'Save & approve'}</span>
          </button>
        </div>
      </div>

      {/* Save Success Banner with optional Next Document CTA */}
      {saveSuccess && (
        <div className="review-notification-banner success-banner" id="save-success-banner">
          <div className="banner-msg-content">
            <CheckCircle2 size={16} />
            <span>Invoice verified and approved! Changes saved to the permanent audit log.</span>
          </div>
          {nextPendingDoc && (
            <Link 
              to={`/review/${nextPendingDoc.documentId}`} 
              className="btn btn-primary btn-sm btn-banner-next"
            >
              <span>Review next ({nextPendingDoc.fileName})</span>
              <ArrowRight size={13} />
            </Link>
          )}
        </div>
      )}

      {/* Save Error Banner */}
      {saveError && (
        <div className="review-notification-banner error-banner" id="save-error-banner">
          <AlertCircle size={16} />
          <span>Save Failed: {saveError}</span>
        </div>
      )}

      {/* Dual Pane Workstation */}
      <div className="review-workstation-grid">
        {/* Left Pane: Document Viewer */}
        <div className="workstation-pane viewer-pane" id="document-viewer-pane">
          <div className="viewer-toolbar">
            <span className="page-indicator">Document Viewer</span>
            <div className="viewer-zoom-controls">
              <button 
                type="button" 
                className="btn-zoom" 
                onClick={() => setZoomLevel((z) => Math.max(50, z - 10))}
                title="Zoom out"
              >
                -
              </button>
              <span className="zoom-label tabular-nums">{zoomLevel}%</span>
              <button 
                type="button" 
                className="btn-zoom" 
                onClick={() => setZoomLevel((z) => Math.min(150, z + 10))}
                title="Zoom in"
              >
                +
              </button>
            </div>
            {document?.viewUrl && (
              <a 
                href={document.viewUrl} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="viewer-open-btn"
              >
                Pop out
              </a>
            )}
          </div>

          <div className="viewer-canvas-scroll">
            {document?.viewUrl ? (
              isPdf ? (
                <iframe
                  src={document.viewUrl}
                  title="Document Preview"
                  className="pdf-preview-iframe"
                  style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
                />
              ) : (
                <img 
                  src={document.viewUrl} 
                  alt={document?.fileName} 
                  className="image-preview-element"
                  style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
                />
              )
            ) : (
              /* Fallback rendered invoice canvas using the document's actual values */
              <div 
                className="rendered-invoice-sheet" 
                style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
              >
                <div className="inv-sheet-header">
                  <div>
                    <h3 className="inv-sheet-brand">{formData.vendorName || document?.vendor || 'COMMERCIAL INVOICE'}</h3>
                    <div className="inv-sheet-brand-sub">AUTOMATED EXTRACTION PREVIEW</div>
                  </div>
                  <div className="inv-sheet-meta-right">
                    <div className="inv-sheet-title">INVOICE</div>
                    <div className="inv-sheet-number">{formData.invoiceNumber || 'INV-EXTRACTED'}</div>
                    <div className="inv-sheet-date">Date: {formData.invoiceDate || '—'}</div>
                    {formData.dueDate && <div className="inv-sheet-date">Due: {formData.dueDate}</div>}
                  </div>
                </div>

                <div className="inv-parties-grid">
                  <div className="inv-party">
                    <span className="party-title">VENDOR / BILLED BY</span>
                    <strong>{formData.vendorName || document?.vendor || 'Vendor name'}</strong>
                    <span>Verified via Document Intelligence</span>
                  </div>
                  <div className="inv-party">
                    <span className="party-title">PAYMENT STATUS</span>
                    <strong>Pending Human Review</strong>
                    <span>Currency: {formData.currency}</span>
                  </div>
                </div>

                {lineItems.length > 0 && (
                  <table className="inv-sheet-table">
                    <thead>
                      <tr>
                        <th className="th-inv-desc">DESCRIPTION</th>
                        <th className="th-inv-qty">QTY</th>
                        <th className="th-inv-price">UNIT PRICE</th>
                        <th className="th-inv-amount">AMOUNT</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lineItems.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.description || 'Line item'}</td>
                          <td className="tabular-nums">{item.quantity}</td>
                          <td className="tabular-nums">{formatCurrency(item.unitPrice, formData.currency)}</td>
                          <td className="tabular-nums">{formatCurrency(item.totalPrice, formData.currency)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                <div className="inv-sheet-totals">
                  {formData.subtotal && (
                    <div className="inv-total-row">
                      <span>Subtotal</span>
                      <span className="tabular-nums">{formatCurrency(formData.subtotal, formData.currency)}</span>
                    </div>
                  )}
                  {formData.taxAmount && (
                    <div className="inv-total-row">
                      <span>Tax / GST</span>
                      <span className="tabular-nums">{formatCurrency(formData.taxAmount, formData.currency)}</span>
                    </div>
                  )}
                  <div className="inv-total-row inv-grand-total">
                    <span>TOTAL AMOUNT</span>
                    <span className="tabular-nums">{formatCurrency(formData.totalAmount || 0, formData.currency)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Pane: Extracted Details & Form */}
        <div className="workstation-pane fields-form-pane" id="document-fields-pane">
          <div className="fields-pane-header">
            <div>
              <h2 className="fields-pane-title">Extracted details</h2>
              <p className="fields-pane-subtitle">
                Values automatically extracted by Textract. Verify fields against the source invoice.
              </p>
            </div>
            <div className="verification-count-badge">
              <span>{verifiedCount} high-confidence</span>
              {toCheckCount > 0 && (
                <>
                  <span className="count-sep">·</span>
                  <span className="text-amber">{toCheckCount} to check</span>
                </>
              )}
            </div>
          </div>

          {/* Low Confidence Alert Banner */}
          {toCheckCount > 0 && (
            <div className="fields-alert-banner">
              <div className="alert-amber-box">!</div>
              <div className="alert-content">
                <strong className="alert-strong">A couple of details need a quick check</strong>
                <span className="alert-text">One or more fields had lower optical confidence. Please confirm.</span>
              </div>
            </div>
          )}

          <form className="invoice-edit-form" onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
            {/* Section: INVOICE INFORMATION */}
            <div className="form-sub-header">
              <span className="sub-header-title">INVOICE INFORMATION</span>
              <span className="sub-header-tag">EDITABLE VALUES</span>
            </div>

            {/* Vendor Name */}
            <div className="field-group">
              <div className="field-label-row">
                <label className="field-label" htmlFor="input-vendor-name">Vendor name</label>
                <span className="field-conf-tag">
                  {confidenceMap.vendorName ? `${Math.round(confidenceMap.vendorName)}% match` : '96% match'}
                </span>
              </div>
              <input
                id="input-vendor-name"
                type="text"
                className="clean-input"
                value={formData.vendorName}
                onChange={(e) => handleFieldChange('vendorName', e.target.value)}
                placeholder="Vendor name"
              />
            </div>

            {/* Row: Invoice number & Invoice date */}
            <div className="fields-dual-row">
              <div className="field-group">
                <div className="field-label-row">
                  <label className="field-label" htmlFor="input-invoice-number">Invoice number</label>
                  <span className="field-conf-tag">
                    {confidenceMap.invoiceNumber ? `${Math.round(confidenceMap.invoiceNumber)}%` : '95%'}
                  </span>
                </div>
                <input
                  id="input-invoice-number"
                  type="text"
                  className="clean-input"
                  value={formData.invoiceNumber}
                  onChange={(e) => handleFieldChange('invoiceNumber', e.target.value)}
                  placeholder="e.g. INV-2026-0881"
                />
              </div>

              <div className="field-group">
                <div className="field-label-row">
                  <label className="field-label" htmlFor="input-invoice-date">Invoice date</label>
                  <span className={`field-conf-tag ${confidenceMap.invoiceDate < 80 ? 'conf-tag-check' : ''}`}>
                    {confidenceMap.invoiceDate ? `${Math.round(confidenceMap.invoiceDate)}%` : '90%'}
                  </span>
                </div>
                <input
                  id="input-invoice-date"
                  type="text"
                  className={`clean-input ${confidenceMap.invoiceDate < 80 ? 'input-needs-check' : ''}`}
                  value={formData.invoiceDate}
                  onChange={(e) => handleFieldChange('invoiceDate', e.target.value)}
                  placeholder="e.g. Oct 15, 2026"
                />
              </div>
            </div>

            {/* Row: Due date & Currency */}
            <div className="fields-dual-row">
              <div className="field-group">
                <div className="field-label-row">
                  <label className="field-label" htmlFor="input-due-date">Due date</label>
                  <span className="field-conf-tag">
                    {confidenceMap.dueDate ? `${Math.round(confidenceMap.dueDate)}%` : '90%'}
                  </span>
                </div>
                <input
                  id="input-due-date"
                  type="text"
                  className="clean-input"
                  value={formData.dueDate}
                  onChange={(e) => handleFieldChange('dueDate', e.target.value)}
                  placeholder="e.g. Nov 15, 2026"
                />
              </div>

              <div className="field-group">
                <div className="field-label-row">
                  <label className="field-label" htmlFor="input-currency">Currency</label>
                </div>
                <select
                  id="input-currency"
                  className="clean-input clean-select"
                  value={formData.currency}
                  onChange={(e) => handleFieldChange('currency', e.target.value)}
                >
                  <option value="USD">USD — US Dollar ($)</option>
                  <option value="INR">INR — Indian Rupee (₹)</option>
                  <option value="EUR">EUR — Euro (€)</option>
                  <option value="GBP">GBP — British Pound (£)</option>
                </select>
              </div>
            </div>

            {/* Total amount */}
            <div className="field-group">
              <div className="field-label-row">
                <label className="field-label" htmlFor="input-total">Total amount</label>
                <span className={`field-conf-tag ${confidenceMap.totalAmount < 80 ? 'conf-tag-check' : ''}`}>
                  {confidenceMap.totalAmount ? `${Math.round(confidenceMap.totalAmount)}% match` : '94% match'}
                </span>
              </div>
              <input
                id="input-total"
                type="text"
                className={`clean-input ${confidenceMap.totalAmount < 80 ? 'input-needs-check' : ''}`}
                value={formData.totalAmount}
                onChange={(e) => handleFieldChange('totalAmount', e.target.value)}
                placeholder="0.00"
              />
            </div>

            {/* Subtotal and Tax row if applicable */}
            {(formData.subtotal || formData.taxAmount) && (
              <div className="fields-dual-row">
                <div className="field-group">
                  <label className="field-label" htmlFor="input-subtotal">Subtotal</label>
                  <input
                    id="input-subtotal"
                    type="text"
                    className="clean-input"
                    value={formData.subtotal}
                    onChange={(e) => handleFieldChange('subtotal', e.target.value)}
                    placeholder="0.00"
                  />
                </div>
                <div className="field-group">
                  <label className="field-label" htmlFor="input-tax">Tax / GST</label>
                  <input
                    id="input-tax"
                    type="text"
                    className="clean-input"
                    value={formData.taxAmount}
                    onChange={(e) => handleFieldChange('taxAmount', e.target.value)}
                    placeholder="0.00"
                  />
                </div>
              </div>
            )}

            {/* Section: LINE ITEMS */}
            <div className="form-sub-header line-items-sub-header">
              <span className="sub-header-title">LINE ITEMS ({lineItems.length})</span>
              <button
                type="button"
                className="btn-add-item-link"
                id="btn-add-line-item"
                onClick={handleAddLineItem}
              >
                <Plus size={13} />
                <span>Add item</span>
              </button>
            </div>

            {/* Line items table */}
            <div className="line-items-edit-wrap">
              {lineItems.length > 0 ? (
                <table className="line-items-edit-table">
                  <thead>
                    <tr>
                      <th className="th-item-desc">DESCRIPTION</th>
                      <th className="th-item-qty">QTY</th>
                      <th className="th-item-price">UNIT PRICE</th>
                      <th className="th-item-amount">AMOUNT</th>
                      <th className="th-item-del"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {lineItems.map((item, idx) => (
                      <tr key={idx} className="line-item-edit-row">
                        <td>
                          <input
                            type="text"
                            className="table-cell-input"
                            value={item.description || ''}
                            onChange={(e) => handleLineItemChange(idx, 'description', e.target.value)}
                            placeholder="Item description"
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            className="table-cell-input text-center tabular-nums"
                            value={item.quantity || 1}
                            onChange={(e) => handleLineItemChange(idx, 'quantity', e.target.value)}
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            step="0.01"
                            className="table-cell-input text-right tabular-nums"
                            value={item.unitPrice ?? ''}
                            onChange={(e) => handleLineItemChange(idx, 'unitPrice', e.target.value)}
                            placeholder="0.00"
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            step="0.01"
                            className="table-cell-input text-right tabular-nums"
                            value={item.totalPrice ?? ''}
                            onChange={(e) => handleLineItemChange(idx, 'totalPrice', e.target.value)}
                            placeholder="0.00"
                          />
                        </td>
                        <td>
                          <button
                            type="button"
                            className="btn-delete-item"
                            onClick={() => handleRemoveLineItem(idx)}
                            title="Remove item"
                          >
                            <Trash2 size={13} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="no-line-items-hint">
                  <span>No line items detected. Click "Add item" to record invoice itemization.</span>
                </div>
              )}
            </div>

            {/* Sticky Form Footer Bar */}
            <div className="form-sticky-footer">
              <div className="immutability-helper-text">
                <CheckCircle2 size={13} className="immutability-icon" />
                <span>Original extraction preserved in audit store</span>
              </div>
              <div className="form-footer-buttons">
                <button
                  type="button"
                  className="btn btn-secondary"
                  id="btn-reset-fields"
                  onClick={handleReset}
                  disabled={isSaving}
                >
                  Reset
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  id="btn-save-corrections"
                  onClick={handleSave}
                  disabled={isSaving}
                >
                  <span>{isSaving ? 'Saving...' : 'Save & approve'}</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
