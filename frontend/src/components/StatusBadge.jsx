import React from 'react';
import { Clock, Loader2, AlertCircle, CheckCircle2, XCircle, FileQuestion } from 'lucide-react';
import { DOCUMENT_STATUSES } from '../utils/constants';

export default function StatusBadge({ status }) {
  const meta = DOCUMENT_STATUSES[status] || {
    label: status || 'Unknown',
    className: 'uploaded'
  };

  const renderIcon = () => {
    switch (status) {
      case 'UPLOADED':
        return <Clock size={12} />;
      case 'PROCESSING':
        return <Loader2 size={12} className="animate-spin-slow" />;
      case 'PENDING_REVIEW':
        return <AlertCircle size={12} />;
      case 'REVIEWED':
        return <CheckCircle2 size={12} />;
      case 'FAILED':
        return <XCircle size={12} />;
      default:
        return <FileQuestion size={12} />;
    }
  };

  return (
    <span className={`status-pill ${meta.className}`} title={meta.description || meta.label}>
      {renderIcon()}
      <span>{meta.label}</span>
    </span>
  );
}
