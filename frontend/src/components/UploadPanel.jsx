import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  X, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw, 
  Layers
} from 'lucide-react';
import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '../utils/constants';
import { formatBytes } from '../utils/formatters';
import { 
  validateFile, 
  executeDocumentUpload, 
  isUploadConfigured,
  getUploadApiUrl
} from '../services/uploadService';
import './UploadPanel.css';

export default function UploadPanel({ onUploadSuccess, isModal = false, isOpen = true, onClose }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState('idle'); // idle | presigning | uploading | success | error
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [validationError, setValidationError] = useState(null);

  const fileInputRef = useRef(null);
  const isConfigured = isUploadConfigured();

  if (isModal && !isOpen) return null;

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

    if (!isConfigured) {
      setUploadState('error');
      setErrorMessage(
        'Upload API endpoint is not configured. Set VITE_UPLOAD_API_URL in frontend/.env to your deployed API Gateway.'
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

  const content = (
    <div className={`upload-panel-container ${isModal ? 'upload-panel-modal' : ''}`} id="upload-panel">
      <div className="upload-header">
        <div>
          <h3 className="upload-title">Upload document</h3>
          <p className="upload-subtitle">
            Upload an invoice or receipt for automated line-item extraction and verification.
          </p>
        </div>
        {isModal && onClose && (
          <button
            type="button"
            className="btn-close-modal"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={16} />
          </button>
        )}
      </div>

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
              <div className="dropzone-icon-box">
                <UploadCloud size={24} className="dropzone-icon" />
              </div>
              <div className="dropzone-text">
                <span className="dropzone-title">
                  <strong>Click to browse</strong> or drag and drop
                </span>
                <span className="dropzone-hint">
                  PDF, PNG, JPG up to {MAX_FILE_SIZE_MB}MB
                </span>
              </div>
            </div>
          ) : (
            <div className="file-preview-row">
              <div className="file-preview-info">
                <div className="file-icon-box">
                  <FileText size={18} />
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
                  className="btn-remove-file"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearSelection();
                  }}
                  title="Remove selected file"
                >
                  <X size={15} />
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Upload Progress Bar */}
      {isUploading && (
        <div className="upload-progress-box" id="upload-progress-box">
          <div className="progress-label-row">
            <span className="progress-status-text">
              {uploadState === 'presigning' ? (
                <>
                  <RefreshCw size={13} className="spin-icon" />
                  <span>Preparing secure cloud upload...</span>
                </>
              ) : (
                <>
                  <UploadCloud size={13} />
                  <span>Uploading to storage ({uploadProgress}%)...</span>
                </>
              )}
            </span>
            <span className="progress-percent tabular-nums">{uploadProgress}%</span>
          </div>
          <div className="progress-bar-track">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${Math.max(6, uploadProgress)}%` }}
            />
          </div>
        </div>
      )}

      {/* Validation Error */}
      {validationError && (
        <div className="upload-alert alert-warning" id="upload-validation-error">
          <AlertTriangle size={15} className="alert-icon" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Upload Error */}
      {uploadState === 'error' && errorMessage && (
        <div className="upload-alert alert-error" id="upload-error-box">
          <AlertTriangle size={15} className="alert-icon" />
          <div className="alert-body">
            <strong>Upload Failed</strong>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Success State */}
      {uploadState === 'success' && uploadResult && (
        <div className="upload-success-box" id="upload-success-box">
          <div className="success-header-row">
            <CheckCircle2 size={18} className="success-icon" />
            <div>
              <h4 className="success-title">Document uploaded successfully</h4>
              <p className="success-desc">
                Your file is stored securely and queued for automated extraction.
              </p>
            </div>
          </div>

          <div className="success-meta-details">
            <div className="meta-detail-item">
              <span className="meta-label">File</span>
              <span className="meta-value">{uploadResult.fileName}</span>
            </div>
            <div className="meta-detail-item">
              <span className="meta-label">Size</span>
              <span className="meta-value">{formatBytes(uploadResult.fileSizeBytes)}</span>
            </div>
          </div>

          <div className="success-actions-row">
            <button
              type="button"
              id="btn-upload-another"
              className="btn btn-secondary btn-sm"
              onClick={handleClearSelection}
            >
              Upload another
            </button>
            {isModal && onClose && (
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={onClose}
              >
                Done
              </button>
            )}
          </div>
        </div>
      )}

      {/* Action Controls for Idle State */}
      {uploadState !== 'success' && (
        <div className="upload-actions-bar">
          <button
            type="button"
            id="btn-execute-upload"
            className="btn btn-primary"
            onClick={handleUploadClick}
            disabled={!selectedFile || isUploading}
          >
            <UploadCloud size={15} />
            <span>{isUploading ? 'Uploading...' : 'Upload document'}</span>
          </button>
          {selectedFile && !isUploading && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClearSelection}
            >
              Cancel
            </button>
          )}
        </div>
      )}
    </div>
  );

  if (isModal) {
    return (
      <div className="modal-backdrop" onClick={onClose}>
        <div className="modal-card" onClick={(e) => e.stopPropagation()}>
          {content}
        </div>
      </div>
    );
  }

  return content;
}
