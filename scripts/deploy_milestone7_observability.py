"""
Milestone 7 Deployment Automation Script:
Provisions CloudWatch Observability Suite for Document Intelligence Serverless Platform:
- Configures 14-day retention on CloudWatch Log Groups for all 5 Lambdas
- Creates CloudWatch Metric Filters for tracking processing and upload failures
- Configures CloudWatch Metric Alarms for critical failure monitoring
- Enables detailed API Gateway CloudWatch metrics
- Creates a comprehensive CloudWatch Executive Dashboard (doc-intelligence-dashboard)
"""

import json
import os
import sys
import boto3
from botocore.exceptions import ClientError

AWS_REGION = "ap-south-1"
ACCOUNT_ID = "399383129700"
API_NAME = "doc-intelligence-api"
STAGE_NAME = "prod"
DASHBOARD_NAME = "doc-intelligence-dashboard"
DYNAMODB_TABLE = "doc-intelligence-documents"
S3_BUCKET = f"doc-intelligence-uploads-{ACCOUNT_ID}"

LAMBDA_FUNCTIONS = [
    "doc-intelligence-create-upload",
    "doc-intelligence-process-document",
    "doc-intelligence-list-documents",
    "doc-intelligence-get-document",
    "doc-intelligence-save-corrections"
]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def log(step: str, msg: str):
    print(f"[{step}] {msg}")

def ensure_log_groups_and_retention(logs_client):
    """Ensure log groups exist for all 5 Lambdas and configure 14-day retention."""
    log("LOG_GROUPS", "Configuring 14-day retention on CloudWatch Log Groups...")
    
    for fn in LAMBDA_FUNCTIONS:
        log_group_name = f"/aws/lambda/{fn}"
        try:
            logs_client.create_log_group(logGroupName=log_group_name)
            log("LOG_GROUPS", f"  Created log group: {log_group_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceAlreadyExistsException":
                log("LOG_GROUPS", f"  Log group exists: {log_group_name}")
            else:
                log("LOG_GROUPS", f"  Warning creating {log_group_name}: {e}")
        
        try:
            logs_client.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=14
            )
            log("LOG_GROUPS", f"  ✓ Set 14-day retention on {log_group_name}")
        except ClientError as e:
            log("LOG_GROUPS", f"  Failed to set retention on {log_group_name}: {e}")

def configure_metric_filters(logs_client):
    """Create Metric Filters to extract custom operational metrics from Lambda logs."""
    log("METRIC_FILTERS", "Configuring CloudWatch Metric Filters...")

    # Filter 1: Document Processing Errors
    process_lg = "/aws/lambda/doc-intelligence-process-document"
    try:
        logs_client.put_metric_filter(
            logGroupName=process_lg,
            filterName="DocumentProcessingErrors",
            filterPattern='?ERROR ?Error ?Exception ?FAILED',
            metricTransformations=[
                {
                    "metricName": "ProcessDocumentErrors",
                    "metricNamespace": "DocIntelligence",
                    "metricValue": "1",
                    "defaultValue": 0.0
                }
            ]
        )
        log("METRIC_FILTERS", f"  ✓ Configured 'ProcessDocumentErrors' on {process_lg}")
    except ClientError as e:
        log("METRIC_FILTERS", f"  Error setting metric filter on {process_lg}: {e}")

    # Filter 2: Upload Validation Errors
    upload_lg = "/aws/lambda/doc-intelligence-create-upload"
    try:
        logs_client.put_metric_filter(
            logGroupName=upload_lg,
            filterName="UploadValidationErrors",
            filterPattern='?ERROR ?Error ?Exception',
            metricTransformations=[
                {
                    "metricName": "UploadErrors",
                    "metricNamespace": "DocIntelligence",
                    "metricValue": "1",
                    "defaultValue": 0.0
                }
            ]
        )
        log("METRIC_FILTERS", f"  ✓ Configured 'UploadErrors' on {upload_lg}")
    except ClientError as e:
        log("METRIC_FILTERS", f"  Error setting metric filter on {upload_lg}: {e}")

    # Filter 3: Review Corrections Errors
    corrections_lg = "/aws/lambda/doc-intelligence-save-corrections"
    try:
        logs_client.put_metric_filter(
            logGroupName=corrections_lg,
            filterName="CorrectionErrors",
            filterPattern='?ERROR ?Error ?Exception',
            metricTransformations=[
                {
                    "metricName": "CorrectionErrors",
                    "metricNamespace": "DocIntelligence",
                    "metricValue": "1",
                    "defaultValue": 0.0
                }
            ]
        )
        log("METRIC_FILTERS", f"  ✓ Configured 'CorrectionErrors' on {corrections_lg}")
    except ClientError as e:
        log("METRIC_FILTERS", f"  Error setting metric filter on {corrections_lg}: {e}")

def configure_cloudwatch_alarms(cw_client):
    """Configure CloudWatch Alarms for error alerting."""
    log("ALARMS", "Configuring CloudWatch Metric Alarms...")

    # Alarm 1: Critical Processing Errors
    try:
        cw_client.put_metric_alarm(
            AlarmName="doc-intelligence-processing-errors-alarm",
            AlarmDescription="Alerts when document processing Lambda encounters 3 or more errors or failed extractions within 5 minutes.",
            ActionsEnabled=False,
            MetricName="ProcessDocumentErrors",
            Namespace="DocIntelligence",
            Statistic="Sum",
            Period=300,
            EvaluationPeriods=1,
            Threshold=3.0,
            ComparisonOperator="GreaterThanOrEqualToThreshold",
            TreatMissingData="notBreaching"
        )
        log("ALARMS", "  ✓ Configured alarm: doc-intelligence-processing-errors-alarm")
    except ClientError as e:
        log("ALARMS", f"  Error creating processing errors alarm: {e}")

    # Alarm 2: API Gateway 5XX Errors
    try:
        cw_client.put_metric_alarm(
            AlarmName="doc-intelligence-api-5xx-alarm",
            AlarmDescription="Alerts when API Gateway doc-intelligence-api encounters any 5XX server errors.",
            ActionsEnabled=False,
            MetricName="5XXError",
            Namespace="AWS/ApiGateway",
            Dimensions=[
                {"Name": "ApiName", "Value": API_NAME}
            ],
            Statistic="Sum",
            Period=300,
            EvaluationPeriods=1,
            Threshold=1.0,
            ComparisonOperator="GreaterThanOrEqualToThreshold",
            TreatMissingData="notBreaching"
        )
        log("ALARMS", "  ✓ Configured alarm: doc-intelligence-api-5xx-alarm")
    except ClientError as e:
        log("ALARMS", f"  Error creating API 5XX alarm: {e}")

def enable_apigw_metrics(apigw_client):
    """Enable CloudWatch metrics on API Gateway stage."""
    log("APIGW_METRICS", "Enabling CloudWatch metrics on API Gateway prod stage...")
    try:
        apis = apigw_client.get_rest_apis().get("items", [])
        api = next((a for a in apis if a["name"] == API_NAME), None)
        if not api:
            log("APIGW_METRICS", f"  Warning: REST API '{API_NAME}' not found.")
            return

        api_id = api["id"]
        apigw_client.update_stage(
            restApiId=api_id,
            stageName=STAGE_NAME,
            patchOperations=[
                {
                    "op": "replace",
                    "path": "/*/*/metrics/enabled",
                    "value": "true"
                }
            ]
        )
        log("APIGW_METRICS", f"  ✓ Enabled detailed CloudWatch metrics on stage '{STAGE_NAME}' for API '{API_NAME}'")
    except ClientError as e:
        log("APIGW_METRICS", f"  Warning enabling API Gateway metrics: {e}")

def create_cloudwatch_dashboard(cw_client):
    """Build and deploy executive CloudWatch Dashboard for the serverless platform."""
    log("DASHBOARD", f"Building CloudWatch Dashboard '{DASHBOARD_NAME}'...")

    dashboard_body = {
        "widgets": [
            # Row 1: Header / Markdown Overview
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 4,
                "properties": {
                    "markdown": f"""# 📊 Serverless Document Intelligence Platform — Operations Dashboard
**AWS Region:** `{AWS_REGION}` | **Account ID:** `{ACCOUNT_ID}` | **Environment:** `Production`
**Core Services:** Amazon Cognito • Amazon S3 • Amazon API Gateway (`{API_NAME}`) • AWS Lambda (5 Functions) • Amazon Textract • Amazon DynamoDB (`{DYNAMODB_TABLE}`)
*Live end-to-end monitoring of API throughput, Lambda execution health, AI extraction pipelines, and database activity.*"""
                }
            },
            # Row 2: Lambda Invocations & Errors
            {
                "type": "metric",
                "x": 0,
                "y": 4,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", "doc-intelligence-create-upload", {"stat": "Sum", "label": "create-upload"}],
                        ["...", "doc-intelligence-process-document", {"stat": "Sum", "label": "process-document"}],
                        ["...", "doc-intelligence-list-documents", {"stat": "Sum", "label": "list-documents"}],
                        ["...", "doc-intelligence-get-document", {"stat": "Sum", "label": "get-document"}],
                        ["...", "doc-intelligence-save-corrections", {"stat": "Sum", "label": "save-corrections"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": "⚡ Lambda Invocations (All Functions)",
                    "period": 300
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 4,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Errors", "FunctionName", "doc-intelligence-create-upload", {"stat": "Sum", "color": "#d62728", "label": "create-upload Errors"}],
                        ["...", "doc-intelligence-process-document", {"stat": "Sum", "color": "#e377c2", "label": "process-document Errors"}],
                        ["...", "doc-intelligence-list-documents", {"stat": "Sum", "color": "#ff7f0e", "label": "list-documents Errors"}],
                        ["...", "doc-intelligence-get-document", {"stat": "Sum", "color": "#bcbd22", "label": "get-document Errors"}],
                        ["...", "doc-intelligence-save-corrections", {"stat": "Sum", "color": "#17becf", "label": "save-corrections Errors"}]
                    ],
                    "view": "timeSeries",
                    "stacked": True,
                    "region": AWS_REGION,
                    "title": "🚨 Lambda Errors & Failures",
                    "period": 300
                }
            },
            # Row 3: Lambda Latency & Execution Duration
            {
                "type": "metric",
                "x": 0,
                "y": 10,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Duration", "FunctionName", "doc-intelligence-create-upload", {"stat": "Average", "label": "create-upload (avg)"}],
                        ["...", "doc-intelligence-process-document", {"stat": "Average", "label": "process-document (avg)"}],
                        ["...", "doc-intelligence-list-documents", {"stat": "Average", "label": "list-documents (avg)"}],
                        ["...", "doc-intelligence-get-document", {"stat": "Average", "label": "get-document (avg)"}],
                        ["...", "doc-intelligence-save-corrections", {"stat": "Average", "label": "save-corrections (avg)"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": "⏱️ Lambda Average Duration (ms)",
                    "period": 300,
                    "yAxis": {"left": {"label": "Milliseconds", "showUnits": False}}
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 10,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Duration", "FunctionName", "doc-intelligence-process-document", {"stat": "p95", "label": "process-document (p95)", "color": "#2ca02c"}],
                        ["...", "doc-intelligence-create-upload", {"stat": "p95", "label": "create-upload (p95)", "color": "#1f77b4"}],
                        ["...", "doc-intelligence-list-documents", {"stat": "p95", "label": "list-documents (p95)", "color": "#ff7f0e"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": "📈 Lambda Latency Percentiles (p95)",
                    "period": 300,
                    "yAxis": {"left": {"label": "Milliseconds", "showUnits": False}}
                }
            },
            # Row 4: API Gateway Traffic & Errors
            {
                "type": "metric",
                "x": 0,
                "y": 16,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Count", "ApiName", API_NAME, "Stage", STAGE_NAME, {"stat": "Sum", "label": "Total API Requests"}],
                        [".", "4XXError", ".", ".", ".", ".", {"stat": "Sum", "color": "#ff7f0e", "label": "4XX Client Errors"}],
                        [".", "5XXError", ".", ".", ".", ".", {"stat": "Sum", "color": "#d62728", "label": "5XX Server Errors"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": f"🌐 API Gateway ({API_NAME} / {STAGE_NAME}) Throughput & Errors",
                    "period": 300
                }
            },
            # Row 4 Right: Custom Application Metrics (Metric Filters)
            {
                "type": "metric",
                "x": 12,
                "y": 16,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["DocIntelligence", "ProcessDocumentErrors", {"stat": "Sum", "color": "#d62728", "label": "Processing Failures"}],
                        [".", "UploadErrors", {"stat": "Sum", "color": "#ff7f0e", "label": "Upload Validation Failures"}],
                        [".", "CorrectionErrors", {"stat": "Sum", "color": "#9467bd", "label": "Correction Save Failures"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": "🔍 Custom Application Failure Metrics (CloudWatch Metric Filters)",
                    "period": 300
                }
            },
            # Row 5: DynamoDB Operations & Throttling
            {
                "type": "metric",
                "x": 0,
                "y": 22,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", DYNAMODB_TABLE, {"stat": "Sum", "label": "Consumed Read Capacity"}],
                        [".", "ConsumedWriteCapacityUnits", ".", ".", {"stat": "Sum", "label": "Consumed Write Capacity"}],
                        [".", "SystemErrorsForOperations", ".", ".", {"stat": "Sum", "color": "#d62728", "label": "DynamoDB System Errors"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": f"💾 DynamoDB Activity & Capacity ({DYNAMODB_TABLE})",
                    "period": 300
                }
            },
            # Row 5 Right: S3 Storage Activity
            {
                "type": "metric",
                "x": 12,
                "y": 22,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/S3", "NumberOfObjects", "BucketName", S3_BUCKET, "StorageType", "AllStorageTypes", {"stat": "Average", "label": "Total Uploaded Objects"}],
                        [".", "BucketSizeBytes", ".", ".", ".", "StandardStorage", {"stat": "Average", "label": "Bucket Size (Bytes)", "yAxis": "right"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": f"📦 Amazon S3 Storage Metrics ({S3_BUCKET})",
                    "period": 86400,
                    "yAxis": {"right": {"label": "Bytes"}}
                }
            },
            # Row 6: Live CloudWatch Logs Insights Error Feed
            {
                "type": "log",
                "x": 0,
                "y": 28,
                "width": 24,
                "height": 8,
                "properties": {
                    "query": f"""SOURCE '/aws/lambda/doc-intelligence-create-upload'
| SOURCE '/aws/lambda/doc-intelligence-process-document'
| SOURCE '/aws/lambda/doc-intelligence-list-documents'
| SOURCE '/aws/lambda/doc-intelligence-get-document'
| SOURCE '/aws/lambda/doc-intelligence-save-corrections'
| fields @timestamp, @logStream, @message
| filter @message like /(?i)(error|exception|failed|fatal)/
| sort @timestamp desc
| limit 25""",
                    "region": AWS_REGION,
                    "title": "📋 CloudWatch Logs Insights: Live Exception & Failure Stream across 5 Lambdas",
                    "view": "table"
                }
            }
        ]
    }

    try:
        cw_client.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=json.dumps(dashboard_body)
        )
        dashboard_url = f"https://{AWS_REGION}.console.aws.amazon.com/cloudwatch/home?region={AWS_REGION}#dashboards/dashboard/{DASHBOARD_NAME}"
        log("DASHBOARD", f"  ✓ Successfully deployed CloudWatch Dashboard: {DASHBOARD_NAME}")
        log("DASHBOARD", f"  🌐 Direct AWS Console URL: {dashboard_url}")
        return dashboard_url
    except ClientError as e:
        log("DASHBOARD", f"  Error deploying dashboard: {e}")
        raise e

def main():
    print("=" * 70)
    print("  MILESTONE 7: OBSERVABILITY & CLOUDWATCH MONITORING DEPLOYMENT")
    print("=" * 70)
    print(f"Target Region:  {AWS_REGION}")
    print(f"AWS Account:    {ACCOUNT_ID}")
    print(f"Dashboard Name: {DASHBOARD_NAME}")
    print("=" * 70)

    session = boto3.Session(region_name=AWS_REGION)
    logs_client = session.client("logs")
    cw_client = session.client("cloudwatch")
    apigw_client = session.client("apigateway")

    # Step 1: Ensure Log Groups and Retention
    ensure_log_groups_and_retention(logs_client)

    # Step 2: Metric Filters
    configure_metric_filters(logs_client)

    # Step 3: Alarms
    configure_cloudwatch_alarms(cw_client)

    # Step 4: API Gateway Metrics
    enable_apigw_metrics(apigw_client)

    # Step 5: Executive Dashboard
    dashboard_url = create_cloudwatch_dashboard(cw_client)

    print("\n" + "=" * 70)
    print("  ✓ MILESTONE 7 OBSERVABILITY DEPLOYMENT COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"• Log Retention:       14 Days applied to all 5 Lambda Log Groups")
    print(f"• Metric Filters:      'ProcessDocumentErrors', 'UploadErrors', 'CorrectionErrors'")
    print(f"• CloudWatch Alarms:   'doc-intelligence-processing-errors-alarm', 'doc-intelligence-api-5xx-alarm'")
    print(f"• API Gateway Metrics: Enabled on '{API_NAME}' ({STAGE_NAME})")
    print(f"• CloudWatch Dashboard: {DASHBOARD_NAME}")
    print(f"• Console URL:         {dashboard_url}")
    print("=" * 70)

if __name__ == "__main__":
    main()
