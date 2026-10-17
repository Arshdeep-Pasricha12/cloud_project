# Utility & Deployment Scripts

This directory will contain deployment automation, test runners, and helper scripts for the Serverless Document Intelligence Platform.

### Planned Scripts:
- `deploy-backend.sh` / `deploy-backend.ps1`: Packages Lambda functions and updates API Gateway / DynamoDB via AWS CLI or SAM.
- `seed-test-run.py`: Script to invoke Textract on a test invoice for local verification.
- `run-tests.sh` / `run-tests.ps1`: Executes backend pytest test suite with coverage report.
