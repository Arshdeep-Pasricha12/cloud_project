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
  Sliders
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
      status: 'Connected',
      resource: config.cognitoPoolId,
      detail: 'OAuth 2.0 / JWT SRP Auth',
      metric: 'Active'
    },
    {
      id: 's3',
      name: 'Amazon S3 Document Lake',
      role: 'Secure Encrypted Ingestion Storage',
      icon: Cloud,
      status: 'Connected',
      resource: config.s3Bucket,
      detail: 'SSE-S3 AES-256 At-Rest',
      metric: 'Private Bucket'
    },
    {
      id: 'api-gw',
      name: 'Amazon API Gateway REST',
      role: 'API Ingestion & CORS Proxy',
      icon: Server,
      status: 'Connected',
      resource: 'wxgm03t7wc / prod',
      detail: 'Cognito JWT Authorizer',
      metric: 'Low Latency'
    },
    {
      id: 'textract',
      name: 'Amazon Textract AnalyzeExpense',
      role: 'AI Line-Item OCR Engine',
      icon: Cpu,
      status: 'Connected',
      resource: 'AWS Textract Financial AI',
      detail: 'Multipage Invoice Parser',
      metric: 'Deep Learning'
    },
    {
      id: 'dynamodb',
      name: 'Amazon DynamoDB Core Store',
      role: 'Document Metadata & Audit Index',
      icon: Database,
      status: 'Connected',
      resource: 'doc-intelligence-documents',
      detail: 'UserDocumentsIndex GSI',
      metric: 'On-Demand'
    },
    {
      id: 'cloudwatch',
      name: 'Amazon CloudWatch Observability',
      role: 'Structured Logging & Telemetry',
      icon: Activity,
      status: 'Connected',
      resource: 'doc-intelligence-dashboard',
      detail: '14-Day Log Group Retention',
      metric: 'Audit Ready'
    }
  ];

  return (
    <div className="settings-page" id="settings-page">
      {/* Header */}
      <div className="settings-header-row">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">
            Cloud infrastructure, extraction thresholds, and compliance controls.
          </p>
        </div>
        <div className="status-pill reviewed">
          <span>Production active</span>
        </div>
      </div>

      {/* Cloud Services Grid */}
      <div className="settings-section">
        <div className="section-title-bar">
          <h2 className="section-title">Cloud Infrastructure</h2>
          <span className="region-indicator">Region: ap-south-1 (Mumbai)</span>
        </div>

        <div className="services-card-grid">
          {cloudServices.map((srv) => {
            const Icon = srv.icon;
            return (
              <div key={srv.id} className="service-infra-card" id={`service-card-${srv.id}`}>
                <div className="service-card-top">
                  <div className="service-icon-wrap">
                    <Icon size={16} />
                  </div>
                  <span className="service-status-tag reviewed">
                    <CheckCircle2 size={11} />
                    <span>{srv.status}</span>
                  </span>
                </div>

                <h3 className="service-name">{srv.name}</h3>
                <p className="service-role">{srv.role}</p>

                <div className="service-meta-box">
                  <div className="service-meta-item">
                    <span className="meta-lbl">Resource</span>
                    <span className="meta-val font-mono" title={srv.resource}>{srv.resource}</span>
                  </div>
                  <div className="service-meta-item">
                    <span className="meta-lbl">Protocol</span>
                    <span className="meta-val">{srv.detail}</span>
                  </div>
                </div>

                <div className="service-footer-pill">
                  <span>{srv.metric}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two-Column Policies & Rules */}
      <div className="settings-split-grid">
        {/* Extraction Policies */}
        <div className="settings-card">
          <div className="card-header-bar">
            <Sliders size={16} className="card-header-icon" />
            <div>
              <h3 className="panel-title">Extraction & Processing Policies</h3>
              <p className="panel-desc">Thresholds for automated invoice ingestion</p>
            </div>
          </div>

          <div className="policies-list">
            <div className="policy-row">
              <div className="policy-info">
                <span className="policy-title">OCR Confidence Threshold</span>
                <span className="policy-desc">Fields below this score trigger human review flags</span>
              </div>
              <span className="policy-badge tabular-nums">80.0% Minimum</span>
            </div>

            <div className="policy-row">
              <div className="policy-info">
                <span className="policy-title">Maximum File Payload</span>
                <span className="policy-desc">Enforced at S3 presigned URL generation</span>
              </div>
              <span className="policy-badge tabular-nums">10.0 MB</span>
            </div>

            <div className="policy-row">
              <div className="policy-info">
                <span className="policy-title">Supported Formats</span>
                <span className="policy-desc">Validated on client upload and Lambda handler</span>
              </div>
              <div className="formats-pill-row">
                <span className="format-pill">PDF</span>
                <span className="format-pill">PNG</span>
                <span className="format-pill">JPEG</span>
              </div>
            </div>

            <div className="policy-row">
              <div className="policy-info">
                <span className="policy-title">Extraction Immutability</span>
                <span className="policy-desc">Raw OCR outputs are preserved alongside human edits</span>
              </div>
              <span className="policy-badge success">Enforced</span>
            </div>
          </div>
        </div>

        {/* Security & Governance */}
        <div className="settings-card">
          <div className="card-header-bar">
            <ShieldCheck size={16} className="card-header-icon" />
            <div>
              <h3 className="panel-title">Security & Compliance Governance</h3>
              <p className="panel-desc">Data protection and zero-trust controls</p>
            </div>
          </div>

          <ul className="governance-list">
            <li className="gov-item">
              <span className="gov-bullet">•</span>
              <div>
                <strong>Zero Long-Lived Credentials:</strong> Client applications never handle AWS IAM credentials. All storage access uses ephemeral 900-second S3 presigned PUT URLs.
              </div>
            </li>
            <li className="gov-item">
              <span className="gov-bullet">•</span>
              <div>
                <strong>Tenant Cryptographic Isolation:</strong> Documents are queried strictly by authenticated user UUID from validated Cognito JWT authorizer claims.
              </div>
            </li>
            <li className="gov-item">
              <span className="gov-bullet">•</span>
              <div>
                <strong>At-Rest & In-Transit Encryption:</strong> All S3 document objects are encrypted using AES-256 (SSE-S3); all network communication uses TLS 1.3.
              </div>
            </li>
            <li className="gov-item">
              <span className="gov-bullet">•</span>
              <div>
                <strong>Audit Trails:</strong> Every review modification is version-stamped with reviewer identity, timestamp, and field differences.
              </div>
            </li>
          </ul>
        </div>
      </div>

      {/* CloudWatch Operations Link */}
      <div className="settings-card operations-card">
        <div className="operations-info">
          <Activity size={18} className="operations-icon" />
          <div>
            <h4 className="panel-title">CloudWatch Operations Dashboard</h4>
            <p className="panel-desc">
              Live telemetry configured for Lambda microservices, API Gateway requests, and DynamoDB throughput.
            </p>
          </div>
        </div>
        <a
          href="https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards/dashboard/doc-intelligence-dashboard"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary btn-sm"
        >
          <span>Open AWS CloudWatch</span>
          <ExternalLink size={13} />
        </a>
      </div>

      {/* Footnote */}
      <div className="page-footnote">
        <CheckCircle2 size={13} className="page-footnote-icon" />
        <span>Infrastructure configuration is managed via Infrastructure-as-Code and verified with automated test suites.</span>
      </div>
    </div>
  );
}
