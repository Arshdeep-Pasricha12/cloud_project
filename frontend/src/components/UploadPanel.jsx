import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '../utils/constants';
import { formatBytes } from '../utils/formatters';
import './UploadPanel.css';

export default function UploadPanel() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadNotice, setUploadNotice] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const validateAndSelectFile = (file) => {
    setUploadNotice(null);
    if (!file) return;

    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setUploadNotice({
        type: 'error',
        message: `Unsupported file type: ${file.type || 'unknown'}. Please upload PDF, JPG, or PNG invoices.`
      });
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setUploadNotice({
        type: 'error',
        message: `File exceeds maximum allowed size of ${MAX_FILE_SIZE_MB}MB (${formatBytes(file.size)}).`
      });
      return;
    }

    setSelectedFile(file);
    setUploadNotice({
      type: 'info',
      message: `File ready: "${file.name}" (${formatBytes(file.size)}). Presigned S3 upload will be active in Milestone 2.`
    });
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
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
    setUploadNotice(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    // Explicit disclosure: not yet connected to AWS
    setUploadNotice({
      type: 'warning',
      message: 'AWS S3 presigned upload is scheduled for Milestone 2. No documents are transferred to the cloud in this initial UI shell.'
    });
  };

  return (
    <div className="glass-card upload-panel" id="upload-panel">
      <div className="upload-header">
        <div>
          <h2 className="upload-title">Ingest Document</h2>
          <p className="upload-subtitle">
            Upload real invoices and business receipts for serverless Textract processing.
          </p>
        </div>
        <span className="phase-badge">AWS S3 · Phase 2</span>
      </div>

      <div
        id="upload-dropzone"
        className={`dropzone ${isDragging ? 'dropzone-active' : ''} ${selectedFile ? 'dropzone-has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          id="file-upload-input"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          style={{ display: 'none' }}
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
                Supports PDF, PNG, JPG up to 10 MB
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
                <span className="file-size">{formatBytes(selectedFile.size)} · {selectedFile.type || 'Document'}</span>
              </div>
            </div>
            <button
              type="button"
              id="btn-remove-selected-file"
              className="btn-icon-remove"
              onClick={(e) => {
                e.stopPropagation();
                handleClearSelection();
              }}
              title="Remove file"
            >
              <X size={16} />
            </button>
          </div>
        )}
      </div>

      {uploadNotice && (
        <div className={`upload-notice notice-${uploadNotice.type}`} id="upload-notice-box">
          {uploadNotice.type === 'error' && <AlertTriangle size={16} className="notice-icon" />}
          {uploadNotice.type === 'warning' && <AlertTriangle size={16} className="notice-icon" />}
          {uploadNotice.type === 'info' && <ShieldCheck size={16} className="notice-icon" />}
          <span className="notice-text">{uploadNotice.message}</span>
        </div>
      )}

      <div className="upload-actions">
        <button
          type="button"
          id="btn-trigger-upload"
          className="btn btn-primary"
          disabled={!selectedFile}
          onClick={handleUploadClick}
        >
          <UploadCloud size={16} />
          <span>Upload & Analyze</span>
        </button>

        <span className="upload-security-note">
          <ShieldCheck size={14} />
          <span>Direct browser-to-S3 upload via short-lived presigned URLs (Private SSE-S3)</span>
        </span>
      </div>
    </div>
  );
}
