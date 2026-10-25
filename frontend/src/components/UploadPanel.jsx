import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  X, 
  AlertTriangle, 
  ShieldCheck, 
  CheckCircle2, 
  RefreshCw, 
  ExternalLink,
  Layers,
  Server,
  Cpu
} from 'lucide-react';
import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '../utils/constants';
import { formatBytes, formatDate } from '../utils/formatters';
import { 
  validateFile, 
  executeDocumentUpload, 
  isUploadConfigured,
  getUploadApiUrl
} from '../services/uploadService';
import './UploadPanel.css';

export default function UploadPanel({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState('idle'); // idle | presigning | uploading | success | error
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [validationError, setValidationError] = useState(null);

  const fileInputRef = useRef(null);
  const isConfigured = isUploadConfigured();
  const configuredEndpoint = getUploadApiUrl();

  const handleDragOver = (e) => {
    e.preventDefault();
    if (uploadState === 'presigning' || uploadState === 'uploading') return;
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const validateAndSelectFile = (file) => {
    setValidationError(null);
    setErrorMessage(null);
    setUploadResult(null);
    setUploadState('idle');
    setUploadProgress(0);

    if (!file) return;

    const validation = validateFile(file, MAX_FILE_SIZE_BYTES);
    if (!validation.valid) {
      setValidationError(validation.error);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (uploadState === 'presigning' || uploadState === 'uploading') return;
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  const handleClearSelection = () => {
    setSelectedFile(null);
    setValidationError(null);
    setErrorMessage(null);
    setUploadResult(null);
    setUploadState('idle');
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = async () => {
    if (!selectedFile) return;

    // Strict configuration check: never fake upload or switch to mock
    if (!isConfigured) {
      setUploadState('error');
      setErrorMessage(
        'Upload API endpoint is not yet configured. Set VITE_UPLOAD_API_URL in frontend/.env to your deployed API Gateway or Lambda URL.'
      );
      return;
    }

    setErrorMessage(null);
    setValidationError(null);
    setUploadProgress(0);

    try {
      const result = await executeDocumentUpload(selectedFile, {
        onProgress: (percent) => {
          setUploadProgress(percent);
        },
        onStatusChange: (status) => {
          if (status === 'presigning' || status === 'uploading') {
            setUploadState(status);
          }
        }
      });

      // Confirmed only after S3 HTTP 200 response
      setUploadResult(result);
      setUploadState('success');
      setUploadProgress(100);
      if (typeof onUploadSuccess === 'function') {
        onUploadSuccess(result);
      }
    } catch (err) {
      setUploadState('error');
      setErrorMessage(err.message || 'An unexpected error occurred during document upload.');
    }
  };

  const isUploading = uploadState === 'presigning' || uploadState === 'uploading';

  return (
    <div className="glass-card upload-panel" id="upload-panel">
      <div className="upload-header">
        <div>
          <h2 className="upload-title">Ingest Document</h2>
          <p className="upload-subtitle">
            Upload invoices and receipts directly to private Amazon S3 storage using short-lived presigned PUT URLs.
          </p>
        </div>
        <span className="phase-badge badge-active">AES-256 S3 Ingestion</span>
      </div>

      {/* Backend Configuration Notice if endpoint is not set */}
      {!isConfigured && (
        <div className="upload-config-notice" id="upload-config-notice">
          <Server size={16} className="config-icon" />
          <div className="config-text">
            <strong>AWS Endpoint Required:</strong> Configure <code>VITE_UPLOAD_API_URL</code> in <code>frontend/.env</code> to point to your API Gateway or local Lambda invocation bridge to enable live S3 uploads.
          </div>
        </div>
      )}

      {/* Drag & Drop Zone */}
      {uploadState !== 'success' && (
        <div
          id="upload-dropzone"
          className={`dropzone ${isDragging ? 'dropzone-active' : ''} ${selectedFile ? 'dropzone-has-file' : ''} ${isUploading ? 'dropzone-uploading' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !selectedFile && !isUploading && fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            id="file-upload-input"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            style={{ display: 'none' }}
            disabled={isUploading}
            onChange={handleFileChange}
          />

          {!selectedFile ? (
            <div className="dropzone-content">
              <div className="dropzone-icon-circle">
                <UploadCloud size={32} className="dropzone-icon" />
              </div>
              <div className="dropzone-instructions">
                <span className="dropzone-primary-text">
                  <strong>Click to browse</strong> or drag & drop invoice
                </span>
                <span className="dropzone-secondary-text">
                  Supports PDF, PNG, JPG up to {MAX_FILE_SIZE_MB} MB
                </span>
              </div>
            </div>
          ) : (
            <div className="file-preview-box">
              <div className="file-preview-info">
                <div className="file-icon-box">
                  <FileText size={24} />
                </div>
                <div className="file-meta">
                  <span className="file-name" title={selectedFile.name}>{selectedFile.name}</span>
                  <span className="file-size">
                    {formatBytes(selectedFile.size)} · {selectedFile.type || 'Document'}
                  </span>
                </div>
              </div>
              {!isUploading && (
                <button
                  type="button"
                  id="btn-remove-selected-file"
                  className="btn-icon-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearSelection();
                  }}
                  title="Remove selected file"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Upload Progress Bar */}
      {isUploading && (
        <div className="upload-progress-container" id="upload-progress-box">
          <div className="progress-status-row">
            <span className="progress-status-label">
              {uploadState === 'presigning' ? (
                <>
                  <RefreshCw size={14} className="spin-icon" />
                  <span>Requesting secure presigned S3 URL from Lambda...</span>
                </>
              ) : (
                <>
                  <UploadCloud size={14} className="pulse-icon" />
                  <span>Uploading directly to private Amazon S3 bucket ({uploadProgress}%)...</span>
                </>
              )}
            </span>
            <span className="progress-percentage">{uploadProgress}%</span>
          </div>
          <div className="progress-bar-track">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${Math.max(8, uploadProgress)}%` }}
            />
          </div>
        </div>
      )}

      {/* Validation Error Banner */}
      {validationError && (
        <div className="upload-notice notice-error" id="validation-error-box">
          <AlertTriangle size={16} className="notice-icon" />
          <span className="notice-text">{validationError}</span>
        </div>
      )}

      {/* Network or S3 Upload Error Banner with Retry */}
      {uploadState === 'error' && errorMessage && (
        <div className="upload-error-card" id="upload-error-box">
          <div className="error-header">
            <AlertTriangle size={18} className="error-icon" />
            <span className="error-title">Upload Failed</span>
          </div>
          <p className="error-message">{errorMessage}</p>
          <div className="error-actions">
            <button
              type="button"
              id="btn-retry-upload"
              className="btn btn-secondary btn-sm"
              onClick={handleUploadClick}
              disabled={isUploading}
            >
              <RefreshCw size={14} />
              <span>Retry Upload</span>
            </button>
            <button
              type="button"
              className="btn-text-dim btn-sm"
              onClick={handleClearSelection}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Success Card Confirmed by S3 */}
      {uploadState === 'success' && uploadResult && (
        <div className="upload-success-card" id="upload-success-card">
          <div className="success-header">
            <div className="success-icon-badge">
              <CheckCircle2 size={22} className="success-icon" />
            </div>
            <div>
              <h3 className="success-title">Document Upload Confirmed</h3>
              <p className="success-subtitle">
                Successfully uploaded binary directly to Amazon S3 via presigned PUT.
              </p>
            </div>
          </div>

          <div className="success-meta-grid">
            <div className="meta-item">
              <span className="meta-label">Document ID</span>
              <span className="meta-value code-font">{uploadResult.documentId}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">S3 Object Key</span>
              <span className="meta-value code-font" title={uploadResult.s3Key}>
                {uploadResult.s3Key}
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Target Bucket</span>
              <span className="meta-value">{uploadResult.bucket || 'Configured S3 Bucket'}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">File Details</span>
              <span className="meta-value">
                {uploadResult.fileName} ({formatBytes(uploadResult.fileSizeBytes)})
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Uploaded At</span>
              <span className="meta-value">{formatDate(uploadResult.uploadedAt)}</span>
            </div>
            {uploadResult.etag && (
              <div className="meta-item">
                <span className="meta-label">S3 ETag</span>
                <span className="meta-value code-font">{uploadResult.etag}</span>
              </div>
            )}
          </div>

          <div className="success-pipeline-note">
            <Cpu size={14} />
            <span>Document dispatched to Amazon Textract serverless pipeline for automated OCR extraction.</span>
          </div>

          <div className="success-actions">
            <button
              type="button"
              id="btn-upload-another"
              className="btn btn-secondary btn-sm"
              onClick={handleClearSelection}
            >
              <UploadCloud size={14} />
              <span>Upload Another Document</span>
            </button>
          </div>
        </div>
      )}

      {/* Action Controls for Idle State */}
      {uploadState !== 'success' && (
        <div className="upload-actions">
          <button
            type="button"
            id="btn-trigger-upload"
            className="btn btn-primary"
            disabled={!selectedFile || isUploading}
            onClick={handleUploadClick}
          >
            {isUploading ? (
              <>
                <RefreshCw size={16} className="spin-icon" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <UploadCloud size={16} />
                <span>Upload to S3</span>
              </>
            )}
          </button>

          <span className="upload-security-note">
            <ShieldCheck size={14} />
            <span>Direct browser-to-S3 upload via short-lived presigned URLs (Private SSE-S3 · 300s expiry)</span>
          </span>
        </div>
      )}
    </div>
  );
}
