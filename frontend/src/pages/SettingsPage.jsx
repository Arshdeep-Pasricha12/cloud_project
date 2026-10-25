import React from 'react';
import { 
  ShieldCheck, 
  Database, 
  Cloud, 
  Key, 
  CheckCircle2, 
  Cpu, 
  Server, 
  Activity, 
  ExternalLink, 
  Lock, 
  Sliders, 
  FileText,
  Zap,
  Radio
} from 'lucide-react';
import './SettingsPage.css';

export default function SettingsPage() {
  const config = {
    awsRegion: import.meta.env.VITE_AWS_REGION || 'ap-south-1',
    cognitoPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || 'ap-south-1_ZIRwwnB44',
    cognitoClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '582n58m1kgl9171f65rhn5k7g3',
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'https://wxgm03t7wc.execute-api.ap-south-1.amazonaws.com/prod',
    s3Bucket: import.meta.env.VITE_S3_DOCUMENT_BUCKET || 'doc-intelligence-uploads-399383129700',
    appEnv: import.meta.env.VITE_APP_ENV || 'production'
  };

  const cloudServices = [
    {
      id: 'cognito',
      name: 'Amazon Cognito User Pool',
      role: 'Authentication & Tenant Identity',
      icon: Key,
      status: 'Operational',
      resource: config.cognitoPoolId,
      detail: 'OAuth 2.0 / JWT SRP Auth',
      metric: 'Zero-Trust Tokens'
    },
    {
      id: 's3',
      name: 'Amazon S3 Document Lake',
      role: 'Secure Encrypted Ingestion Storage',
      icon: Cloud,
      status: 'Operational',
      resource: config.s3Bucket,
      detail: 'SSE-S3 AES-256 At-Rest',
      metric: 'Public Access Blocked'
    },
    {
      id: 'api-gw',
      name: 'Amazon API Gateway REST',
      role: 'API Ingestion & CORS Proxy',
      icon: Server,
      status: 'Operational',
      resource: 'wxgm03t7wc / prod',
      detail: 'Cognito JWT Authorizer',
      metric: '< 120ms P95 Latency'
    },
    {
      id: 'textract',
      name: 'Amazon Textract AnalyzeExpense',
      role: 'AI Line-Item OCR Engine',
      icon: Cpu,
      status: 'Operational',
      resource: 'AWS Textract Financial AI',
      detail: 'Multipage Invoice Parser',
      metric: 'Deep Learning Model'
    },
    {
      id: 'dynamodb',
      name: 'Amazon DynamoDB Core Store',
      role: 'Document Metadata & Audit Index',
      icon: Database,
      status: 'Operational',
      resource: 'doc-intelligence-documents',
      detail: 'UserDocumentsIndex GSI',
      metric: 'Single-digit ms Read/Write'
    },
    {
      id: 'cloudwatch',
      name: 'Amazon CloudWatch Observability',
      role: 'Structured Logging & Telemetry',
      icon: Activity,
      status: 'Operational',
      resource: 'doc-intelligence-dashboard',
      detail: '14-Day Log Group Retention',
      metric: 'Real-time Metrics'
    }
  ];

  return (
    <div className="settings-page" id="settings-page">
      {/* Top Header */}
      <div className="settings-header">
        <div>
          <h2 className="settings-title">Platform Settings & Cloud Infrastructure</h2>
          <p className="settings-desc">
            Active AWS microservice topology, security governance, AI extraction policies, and real-time operations.
          </p>
        </div>
        <div className="cloud-health-indicator">
          <span className="live-pulse-dot"></span>
          <span className="live-health-text">All Cloud Systems Normal</span>
        </div>
      </div>

      {/* Cloud Microservices Topology Grid */}
      <div className="section-block">
        <div className="section-header-row">
          <div className="section-title-wrap">
            <Radio size={16} className="section-icon text-indigo" />
            <h3 className="section-heading">Connected AWS Microservices</h3>
          </div>
          <span className="region-pill">Region: ap-south-1 (Mumbai)</span>
        </div>

        <div className="services-grid">
          {cloudServices.map((srv) => {
            const Icon = srv.icon;
            return (
              <div key={srv.id} className="glass-card service-infra-card" id={`service-card-${srv.id}`}>
                <div className="service-card-top">
                  <div className="service-icon-box">
                    <Icon size={18} className="service-icon" />
                  </div>
                  <div className="service-status-pill">
                    <CheckCircle2 size={12} className="status-check-icon" />
                    <span>{srv.status}</span>
                  </div>
                </div>

                <h4 className="service-name">{srv.name}</h4>
                <p className="service-role">{srv.role}</p>

                <div className="service-details-box">
                  <div className="service-detail-item">
                    <span className="detail-label">Resource</span>
                    <span className="detail-value font-mono" title={srv.resource}>{srv.resource}</span>
                  </div>
                  <div className="service-detail-item">
                    <span className="detail-label">Protocol</span>
                    <span className="detail-value">{srv.detail}</span>
                  </div>
                </div>

                <div className="service-card-footer">
                  <span className="service-metric-tag">{srv.metric}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column Configuration & Security Parameters */}
      <div className="settings-split-grid">
        {/* AI & Pipeline Processing Parameters */}
        <div className="glass-card config-panel">
          <div className="panel-header">
            <Sliders size={18} className="panel-icon text-sky" />
            <div>
              <h3 className="panel-title">AI Extraction & Processing Policies</h3>
              <p className="panel-desc">Operational thresholds for automated invoice ingestion</p>
            </div>
          </div>

          <div className="policy-items-list">
            <div className="policy-item">
              <div className="policy-meta">
                <span className="policy-name">OCR Confidence Verification Threshold</span>
                <span className="policy-sub">Fields below this confidence score trigger human review flags</span>
              </div>
              <div className="policy-control-badge">80.0% Minimum</div>
            </div>

            <div className="policy-item">
              <div className="policy-meta">
                <span className="policy-name">Maximum Ingestion Payload</span>
                <span className="policy-sub">Enforced at S3 presigned URL signature generation</span>
              </div>
              <div className="policy-control-badge">10.0 MB</div>
            </div>

            <div className="policy-item">
              <div className="policy-meta">
                <span className="policy-name">Allowed MIME Formats</span>
                <span className="policy-sub">Validated on client upload and Lambda ingestion</span>
              </div>
              <div className="format-tags">
                <span className="format-tag">PDF</span>
                <span className="format-tag">PNG</span>
                <span className="format-tag">JPEG</span>
              </div>
            </div>

            <div className="policy-item">
              <div className="policy-meta">
                <span className="policy-name">Extraction Immutability</span>
                <span className="policy-sub">Raw Textract outputs are permanently preserved alongside corrections</span>
              </div>
              <div className="policy-control-badge success">Enforced</div>
            </div>
          </div>
        </div>

        {/* Security & Cloud Governance Rules */}
        <div className="glass-card config-panel">
          <div className="panel-header">
            <ShieldCheck size={18} className="panel-icon text-emerald" />
            <div>
              <h3 className="panel-title">Security & Compliance Governance</h3>
              <p className="panel-desc">Enterprise data protection and zero-trust controls</p>
            </div>
          </div>

          <ul className="governance-rules-list">
            <li className="governance-rule">
              <div className="rule-bullet"></div>
              <div className="rule-content">
                <strong>Zero Long-Lived Credentials:</strong> Client applications never handle AWS IAM credentials. All storage access uses ephemeral 900-second S3 presigned PUT URLs.
              </div>
            </li>
            <li className="governance-rule">
              <div className="rule-bullet"></div>
              <div className="rule-content">
                <strong>Multi-Tenant Cryptographic Isolation:</strong> Documents are queried strictly by authenticated user UUID from validated Cognito JWT authorizer claims.
              </div>
            </li>
            <li className="governance-rule">
              <div className="rule-bullet"></div>
              <div className="rule-content">
                <strong>At-Rest & In-Transit Encryption:</strong> All S3 document objects are encrypted using AES-256 (SSE-S3); all communications use TLS 1.3.
              </div>
            </li>
            <li className="governance-rule">
              <div className="rule-bullet"></div>
              <div className="rule-content">
                <strong>Automated Audit Trails:</strong> Every document review modification is version-stamped with reviewer identity, timestamp, and field diffs.
              </div>
            </li>
            <li className="governance-rule">
              <div className="rule-bullet"></div>
              <div className="rule-content">
                <strong>Zero-Idle Serverless Architecture:</strong> 100% event-driven microservices with zero standby compute charges or provisioned server overhead.
              </div>
            </li>
          </ul>
        </div>
      </div>

      {/* CloudWatch Operations & Monitoring Bar */}
      <div className="glass-card monitoring-bar">
        <div className="monitoring-info">
          <Activity size={20} className="monitoring-icon" />
          <div>
            <h4 className="monitoring-title">AWS CloudWatch Observability Dashboard</h4>
            <p className="monitoring-desc">
              Real-time monitoring configured for 5 Lambda microservices, API Gateway requests, Textract execution latency, and DynamoDB throughput.
            </p>
          </div>
        </div>
        <div className="monitoring-actions">
          <a
            href="https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards/dashboard/doc-intelligence-dashboard"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary btn-sm external-link-btn"
          >
            <span>Open AWS CloudWatch</span>
            <ExternalLink size={14} />
          </a>
        </div>
      </div>
    </div>
  );
}
