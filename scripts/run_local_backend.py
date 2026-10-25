"""
Local Development Server: Bridge for Lambda create-upload
Allows running and testing the Lambda handler locally over HTTP without deploying Amazon API Gateway.

Usage:
  python scripts/run_local_backend.py
"""
import http.server
import json
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import importlib.util

handler_file = backend_path / "functions" / "create-upload" / "handler.py"
spec = importlib.util.spec_from_file_location("create_upload_handler", str(handler_file))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
lambda_handler = module.lambda_handler

PORT = int(os.environ.get("LOCAL_BACKEND_PORT", 8000))


class LocalLambdaBridgeHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_POST(self):
        if self.path != "/documents/upload-url":
            err_body = json.dumps({"error": "NotFound", "message": f"Endpoint {self.path} not found"}).encode("utf-8")
            self.send_response(404)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(err_body)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        body_str = body_bytes.decode("utf-8") if body_bytes else ""

        # Construct API Gateway Proxy Event format
        event = {
            "httpMethod": "POST",
            "path": self.path,
            "headers": dict(self.headers),
            "body": body_str,
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "dev-local-user"
                    }
                }
            }
        }

        # Invoke Lambda handler
        response = lambda_handler(event, None)

        status_code = response.get("statusCode", 500)
        body = response.get("body", "{}")
        response_bytes = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")

        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, format, *args):
        print(f"[Local Lambda Bridge] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    bucket = os.environ.get("DOCUMENTS_BUCKET_NAME") or "doc-intelligence-uploads-399383129700"
    region = os.environ.get("AWS_REGION") or "ap-south-1"
    os.environ["DOCUMENTS_BUCKET_NAME"] = bucket
    os.environ["AWS_REGION"] = region

    print("=" * 65)
    print("  Serverless Document Intelligence - Local Lambda Bridge")
    print("=" * 65)
    print(f"  Target S3 Bucket: {bucket}")
    print(f"  AWS Region:       {region}")
    print(f"  Local Endpoint:   http://localhost:{PORT}/documents/upload-url")
    print("=" * 65)
    print(f"  Listening on port {PORT}...")

    server_address = ("", PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, LocalLambdaBridgeHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down local bridge server.")
