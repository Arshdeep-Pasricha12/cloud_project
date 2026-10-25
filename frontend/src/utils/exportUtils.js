/**
 * Export Utilities for Accounting & ERP Integration
 * Supports exporting verified invoice records to standard CSV and ERP-compatible JSON.
 */

export function exportDocumentsToCsv(documents = []) {
  if (!documents || documents.length === 0) {
    alert('No documents available to export.');
    return;
  }

  const headers = [
    'Document ID',
    'File Name',
    'Vendor Name',
    'Invoice Number',
    'Invoice Date',
    'Due Date',
    'Currency',
    'Subtotal',
    'Tax Amount',
    'Total Amount',
    'Status',
    'Confidence (%)',
    'Created At'
  ];

  const rows = documents.map((doc) => {
    const raw = doc.rawExtraction?.summaryFields || {};
    const vendor = doc.vendor || raw.vendorName?.value || '';
    const invNum = doc.invoiceNumber || raw.invoiceNumber?.value || '';
    const invDate = doc.invoiceDate || raw.invoiceDate?.value || '';
    const dueDate = doc.dueDate || raw.dueDate?.value || '';
    const currency = doc.currency || raw.currency?.value || 'USD';
    const subtotal = raw.subtotal?.value ?? '';
    const tax = raw.taxAmount?.value ?? '';
    const total = doc.totalAmount ?? raw.totalAmount?.value ?? '';
    const status = doc.status || 'UPLOADED';
    const conf = doc.confidence ?? raw.metrics?.averageConfidence ?? '';

    return [
      `"${doc.documentId || ''}"`,
      `"${(doc.fileName || '').replace(/"/g, '""')}"`,
      `"${(vendor || '').replace(/"/g, '""')}"`,
      `"${(invNum || '').replace(/"/g, '""')}"`,
      `"${invDate}"`,
      `"${dueDate}"`,
      `"${currency}"`,
      subtotal,
      tax,
      total,
      `"${status}"`,
      conf,
      `"${doc.createdAt || ''}"`
    ].join(',');
  });

  const csvContent = [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `docuintel_invoices_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportInvoiceToJson(doc, formData, lineItems) {
  const exportPayload = {
    exportedAt: new Date().toISOString(),
    system: 'DocuIntel Document Intelligence Platform',
    documentId: doc?.documentId,
    fileName: doc?.fileName,
    invoiceMetadata: {
      vendor: formData.vendorName,
      invoiceNumber: formData.invoiceNumber,
      invoiceDate: formData.invoiceDate,
      dueDate: formData.dueDate,
      currency: formData.currency,
      subtotal: parseFloat(formData.subtotal) || null,
      taxAmount: parseFloat(formData.taxAmount) || null,
      totalAmount: parseFloat(formData.totalAmount) || null,
      notes: formData.notes
    },
    lineItems: lineItems.map((item) => ({
      description: item.description,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      totalPrice: item.totalPrice
    })),
    audit: {
      status: 'VERIFIED',
      verifiedByUser: doc?.userId,
      originalS3Key: doc?.s3Key
    }
  };

  const jsonStr = JSON.stringify(exportPayload, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `${(formData.invoiceNumber || 'invoice').toLowerCase()}_erp_export.json`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
