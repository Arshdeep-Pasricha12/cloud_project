import React from 'react';
import { Settings, ShieldCheck, Database, Cloud, Key, CheckCircle, Clock } from 'lucide-react';
import './SettingsPage.css';

export default function SettingsPage() {
  const config = {
    awsRegion: import.meta.env.VITE_AWS_REGION || 'Not Configured (e.g. us-east-1)',
    cognitoPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || 'Pending Milestone 1',
    cognitoClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || 'Pending Milestone 1',
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'Pending Milestone 3',
    s3Bucket: import.meta.env.VITE_S3_DOCUMENT_BUCKET || 'Pending Milestone 2',
    appEnv: import.meta.env.VITE_APP_ENV || 'development'
  };

  const milestones = [
    { num: '0', title: 'React + Vite Application Shell & Local Foundation', status: 'completed' },
    { num: '1', title: 'Amazon Cognito User Pools Authentication', status: 'pending' },
    { num: '2', title: 'Private Amazon S3 Bucket & Presigned PUT Uploads', status: 'pending' },
    { num: '3', title: 'Amazon API Gateway REST API with Cognito Authorizer', status: 'pending' },
    { num: '4', title: 'Amazon Textract AnalyzeExpense Pipeline (Lambda)', status: 'pending' },
    { num: '5', title: 'Amazon DynamoDB Document Persistence & Listing Queries', status: 'pending' },
    { num: '6', title: 'Human-in-the-Loop Corrections & Separate Audit Storage', status: 'pending' },
    { num: '7', title: 'CloudWatch Logging, Metrics & Moto/Pytest Automation', status: 'pending' },
    { num: '8', title: 'Serverless Production Deployment & College Demo Runbook', status: 'pending' }
  ];

  return (
    <div className="settings-page" id="settings-page">
      <div className="settings-header">
        <div>
          <h2 className="settings-title">AWS Configuration & Platform Settings</h2>
          <p className="settings-desc">Manage environment variables, cloud endpoints, and serverless stack parameters.</p>
        </div>
        <span className="phase-badge info">Read-Only Shell</span>
      </div>

      <div className="settings-grid">
        {/* Environment Variables Card */}
        <div className="glass-card settings-card">
          <div className="card-header">
            <Cloud size={18} className="card-icon" />
            <h3 className="card-title">Cloud Environment Variables</h3>
          </div>
          <p className="card-subtitle">
            Values are sourced from <code>.env</code> file (see <code>.env.example</code> template).
          </p>

          <div className="config-list">
            <div className="config-item">
              <span className="config-key">VITE_AWS_REGION</span>
              <span className="config-val">{config.awsRegion}</span>
            </div>
            <div className="config-item">
              <span className="config-key">VITE_COGNITO_USER_POOL_ID</span>
              <span className="config-val">{config.cognitoPoolId}</span>
            </div>
            <div className="config-item">
              <span className="config-key">VITE_COGNITO_CLIENT_ID</span>
              <span className="config-val">{config.cognitoClientId}</span>
            </div>
            <div className="config-item">
              <span className="config-key">VITE_API_BASE_URL</span>
              <span className="config-val">{config.apiBaseUrl}</span>
            </div>
            <div className="config-item">
              <span className="config-key">VITE_S3_DOCUMENT_BUCKET</span>
              <span className="config-val">{config.s3Bucket}</span>
            </div>
            <div className="config-item">
              <span className="config-key">VITE_APP_ENV</span>
              <span className="config-val">{config.appEnv}</span>
            </div>
          </div>
        </div>

        {/* Security & Architecture Rules */}
        <div className="glass-card settings-card">
          <div className="card-header">
            <ShieldCheck size={18} className="card-icon" />
            <h3 className="card-title">Architecture & Cost Rules</h3>
          </div>
          <p className="card-subtitle">
            Strict constraints governing AWS resource provisioning.
          </p>

          <ul className="rules-list">
            <li>
              <strong>100% Serverless:</strong> No EC2, ALB, or idle compute instances. Pay only per request.
            </li>
            <li>
              <strong>Private S3 Only:</strong> Public access block active on all buckets. Access strictly via presigned URLs.
            </li>
            <li>
              <strong>Data Immutability:</strong> Original Textract extractions are never overwritten by user edits.
            </li>
            <li>
              <strong>Zero Secret Embedding:</strong> No AWS access keys or passwords stored in frontend bundles or code repository.
            </li>
            <li>
              <strong>Cognito Multi-Tenancy:</strong> Document queries strictly scoped to authenticated user sub ID.
            </li>
          </ul>
        </div>
      </div>

      {/* Implementation Roadmap */}
      <div className="glass-card roadmap-card">
        <h3 className="roadmap-title">Implementation Milestones Roadmap</h3>
        <p className="roadmap-desc">Step-by-step progress towards complete AWS cloud deployment.</p>

        <div className="milestones-timeline">
          {milestones.map((m) => (
            <div key={m.num} className={`timeline-item item-${m.status}`}>
              <div className="timeline-badge">
                {m.status === 'completed' ? (
                  <CheckCircle size={15} className="badge-icon-completed" />
                ) : (
                  <Clock size={15} className="badge-icon-pending" />
                )}
              </div>
              <div className="timeline-content">
                <span className="timeline-milestone">Milestone {m.num}</span>
                <span className="timeline-task">{m.title}</span>
              </div>
              <span className={`status-pill ${m.status === 'completed' ? 'reviewed' : 'uploaded'}`}>
                {m.status === 'completed' ? 'Completed' : 'Upcoming'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
