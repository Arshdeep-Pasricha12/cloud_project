import React, { useState } from 'react';
import DocumentsTable from '../components/DocumentsTable';
import { useDocuments } from '../hooks/useDocuments';
import { Search, Filter, Layers, Database } from 'lucide-react';
import './DocumentsPage.css';

export default function DocumentsPage() {
  const { documents, isLoading, refreshDocuments } = useDocuments();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.fileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          doc.vendor?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || doc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="documents-page" id="documents-page">
      <div className="page-header-row">
        <div>
          <h2 className="page-title">Document Repository</h2>
          <p className="page-desc">Browse, search, and manage invoices stored across Amazon S3 & DynamoDB.</p>
        </div>
        <span className="phase-badge badge-active">Cloud Encrypted Repository</span>
      </div>

      <div className="glass-card filter-toolbar">
        <div className="search-box">
          <Search size={16} className="search-icon" />
          <input
            id="input-document-search"
            type="text"
            className="search-input"
            placeholder="Search by invoice name or vendor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <Filter size={15} className="filter-icon" />
          <select
            id="select-status-filter"
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            <option value="UPLOADED">Uploaded</option>
            <option value="PROCESSING">Processing</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="REVIEWED">Reviewed</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      <DocumentsTable 
        documents={filteredDocuments} 
        isLoading={isLoading} 
        onRefresh={refreshDocuments} 
      />
    </div>
  );
}
