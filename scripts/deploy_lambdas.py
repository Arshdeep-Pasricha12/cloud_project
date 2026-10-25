"""
Deploy updated Lambda functions:
1. doc-intelligence-process-document (with fallback parser and pypdf)
2. doc-intelligence-list-documents (with all extracted fields: vendor, invoiceNumber, invoiceDate, amount, confidence)
"""

import io
import os
import zipfile
import boto3
import pypdf

AWS_REGION = "ap-south-1"
lambda_client = boto3.client("lambda", region_name=AWS_REGION)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

def build_process_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(BACKEND_DIR, "functions", "process-document", "handler.py"), arcname="handler.py")
        
        shared_dir = os.path.join(BACKEND_DIR, "shared")
        for root, _, files in os.walk(shared_dir):
            for file in files:
                if file.endswith(".pyc") or "__pycache__" in root: continue
                fp = os.path.join(root, file)
                rel = os.path.relpath(fp, BACKEND_DIR).replace("\\", "/")
                zf.write(fp, arcname=rel)

        pypdf_dir = os.path.dirname(pypdf.__file__)
        for root, _, files in os.walk(pypdf_dir):
            for file in files:
                if file.endswith(".pyc") or "__pycache__" in root: continue
                fp = os.path.join(root, file)
                rel = os.path.relpath(fp, os.path.dirname(pypdf_dir)).replace("\\", "/")
                zf.write(fp, arcname=rel)
    return buf.getvalue()

def build_list_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(BACKEND_DIR, "functions", "list-documents", "handler.py"), arcname="handler.py")
        shared_dir = os.path.join(BACKEND_DIR, "shared")
        for root, _, files in os.walk(shared_dir):
            for file in files:
                if file.endswith(".pyc") or "__pycache__" in root: continue
                fp = os.path.join(root, file)
                rel = os.path.relpath(fp, BACKEND_DIR).replace("\\", "/")
                zf.write(fp, arcname=rel)
    return buf.getvalue()

def deploy():
    waiter = lambda_client.get_waiter("function_updated")

    print("[1/2] Updating doc-intelligence-process-document...")
    proc_zip = build_process_zip()
    lambda_client.update_function_code(
        FunctionName="doc-intelligence-process-document",
        ZipFile=proc_zip
    )
    print(" - Code updated. Waiting for update to settle...")
    waiter.wait(FunctionName="doc-intelligence-process-document")

    lambda_client.update_function_configuration(
        FunctionName="doc-intelligence-process-document",
        Environment={
            "Variables": {
                "DOCUMENTS_BUCKET_NAME": "doc-intelligence-uploads-399383129700",
                "DOCUMENTS_TABLE_NAME": "doc-intelligence-documents"
            }
        }
    )
    waiter.wait(FunctionName="doc-intelligence-process-document")
    print(" - doc-intelligence-process-document updated successfully.")

    print("[2/2] Updating doc-intelligence-list-documents...")
    list_zip = build_list_zip()
    lambda_client.update_function_code(
        FunctionName="doc-intelligence-list-documents",
        ZipFile=list_zip
    )
    print(" - Code updated. Waiting for update to settle...")
    waiter.wait(FunctionName="doc-intelligence-list-documents")

    lambda_client.update_function_configuration(
        FunctionName="doc-intelligence-list-documents",
        Environment={
            "Variables": {
                "DOCUMENTS_TABLE_NAME": "doc-intelligence-documents"
            }
        }
    )
    waiter.wait(FunctionName="doc-intelligence-list-documents")
    print(" - doc-intelligence-list-documents updated successfully.")

if __name__ == "__main__":
    deploy()
