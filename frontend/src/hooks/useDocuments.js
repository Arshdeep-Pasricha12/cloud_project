import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [metrics, setMetrics] = useState({
    total: 0,
    processing: 0,
    pendingReview: 0,
    reviewed: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.listDocuments();
      setDocuments(data.items || []);
      setMetrics(data.metrics || {
        total: 0,
        processing: 0,
        pendingReview: 0,
        reviewed: 0
      });
    } catch (err) {
      setError(err.message || 'Error loading documents');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents,
    metrics,
    isLoading,
    error,
    refreshDocuments: fetchDocuments
  };
}
