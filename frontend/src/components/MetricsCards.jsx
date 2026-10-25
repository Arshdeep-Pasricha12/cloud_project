import React from 'react';
import { FileText, Clock, AlertCircle, Check } from 'lucide-react';
import './MetricsCards.css';

export default function MetricsCards({ metrics = { total: 0, processing: 0, pendingReview: 0, reviewed: 0 } }) {
  const cards = [
    {
      id: 'metric-card-total',
      title: 'Documents received',
      value: metrics.total ?? 0,
      subtitle: metrics.total > 0 ? `${metrics.total} total · across all uploads` : 'Across all uploads',
      icon: FileText,
      iconClass: 'icon-box-neutral'
    },
    {
      id: 'metric-card-processing',
      title: 'Processing',
      value: metrics.processing ?? 0,
      subtitle: 'Usually takes under a minute',
      icon: Clock,
      iconClass: 'icon-box-blue'
    },
    {
      id: 'metric-card-pending',
      title: 'Needs review',
      value: metrics.pendingReview ?? 0,
      subtitle: 'Fields waiting for confirmation',
      icon: AlertCircle,
      iconClass: 'icon-box-amber'
    },
    {
      id: 'metric-card-reviewed',
      title: 'Reviewed',
      value: metrics.reviewed ?? 0,
      subtitle: 'Saved with verified details',
      icon: Check,
      iconClass: 'icon-box-green'
    }
  ];

  return (
    <div className="metrics-grid" id="metrics-cards-grid">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.id} id={card.id} className="metric-card">
            <div className="metric-header">
              <span className="metric-title">{card.title}</span>
              <div className={`metric-icon-box ${card.iconClass}`}>
                <Icon size={15} />
              </div>
            </div>
            <div className="metric-value">{card.value}</div>
            <div className="metric-subtitle">{card.subtitle}</div>
          </div>
        );
      })}
    </div>
  );
}
