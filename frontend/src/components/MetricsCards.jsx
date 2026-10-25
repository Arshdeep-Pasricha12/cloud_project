import React from 'react';
import { Files, Loader2, AlertCircle, CheckCircle2, ShieldCheck } from 'lucide-react';
import './MetricsCards.css';

export default function MetricsCards({ metrics = { total: 0, processing: 0, pendingReview: 0, reviewed: 0 } }) {
  const cards = [
    {
      id: 'metric-card-total',
      title: 'Total Documents',
      value: metrics.total,
      subtitle: 'Invoices ingested to S3',
      icon: Files,
      colorClass: 'metric-total',
      tag: 'Live Lake'
    },
    {
      id: 'metric-card-processing',
      title: 'In Processing',
      value: metrics.processing,
      subtitle: 'Textract AnalyzeExpense active',
      icon: Loader2,
      colorClass: 'metric-processing',
      tag: 'AI Pipeline'
    },
    {
      id: 'metric-card-pending',
      title: 'Pending Review',
      value: metrics.pendingReview,
      subtitle: 'Awaiting reviewer inspection',
      icon: AlertCircle,
      colorClass: 'metric-pending',
      tag: 'Review Queue'
    },
    {
      id: 'metric-card-reviewed',
      title: 'Reviewed & Saved',
      value: metrics.reviewed,
      subtitle: 'Verified with audit corrections',
      icon: CheckCircle2,
      colorClass: 'metric-reviewed',
      tag: 'Audit Sealed'
    }
  ];

  return (
    <div className="metrics-grid" id="metrics-cards-grid">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.id} id={card.id} className={`glass-card metric-card ${card.colorClass}`}>
            <div className="metric-header">
              <span className="metric-title">{card.title}</span>
              <div className="metric-icon-wrapper">
                <Icon size={18} className="metric-icon" />
              </div>
            </div>
            <div className="metric-value-row">
              <span className="metric-value">{card.value}</span>
              <span className="metric-unit">docs</span>
            </div>
            <div className="metric-footer">
              <span className="metric-subtitle">{card.subtitle}</span>
              <span className="metric-tag">{card.tag}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
