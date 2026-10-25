"""
Milestone 8 Deployment Automation Script:
Provisions production static hosting with Amazon S3 Website Hosting & optional CloudFront CDN:
1. Builds optimized Vite React SPA production bundle (npm run build)
2. Provisions S3 hosting bucket (doc-intelligence-frontend-399383129700) with SSE-S3 AES-256
3. Configures S3 Static Website Hosting with SPA client-side routing (IndexDocument: index.html, ErrorDocument: index.html)
4. Applies public read bucket policy for web asset delivery
5. Uploads build artifacts with optimized Content-Type and Cache-Control headers
6. Attempts CloudFront global CDN distribution deployment (with graceful fallback if account verification is pending)
7. Updates document uploads S3 bucket CORS to allow live production origin
"""

import json
import mimetypes
import os
import subprocess
import sys
import time
import boto3
from botocore.exceptions import ClientError

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AWS_REGION = "ap-south-1"
ACCOUNT_ID = "399383129700"
FRONTEND_BUCKET = f"doc-intelligence-frontend-{ACCOUNT_ID}"
UPLOADS_BUCKET = f"doc-intelligence-uploads-{ACCOUNT_ID}"
OAC_NAME = "doc-intelligence-frontend-oac"

# S3 Website endpoint format for ap-south-1
S3_WEBSITE_URL = f"http://{FRONTEND_BUCKET}.s3-website.{AWS_REGION}.amazonaws.com"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DIST_DIR = os.path.join(FRONTEND_DIR, "dist")

def log(step: str, msg: str):
    print(f"[{step}] {msg}")

def build_frontend_bundle():
    """Build Vite React SPA production bundle."""
    log("BUILD", "Compiling frontend bundle with 'npm run build'...")
    cmd = "npm.cmd run build" if sys.platform == "win32" else "npm run build"
    result = subprocess.run(cmd, cwd=FRONTEND_DIR, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        log("BUILD", f"Error during build:\n{result.stderr}")
        raise RuntimeError("Frontend compilation failed.")
    
    index_html = os.path.join(DIST_DIR, "index.html")
    if not os.path.isfile(index_html):
        raise FileNotFoundError(f"Expected build output at '{index_html}' was not found.")
    
    log("BUILD", "✓ Frontend bundle built successfully in frontend/dist")

def ensure_s3_hosting_bucket(s3_client):
    """Create S3 hosting bucket with encryption and website hosting."""
    log("S3_HOSTING", f"Checking frontend bucket '{FRONTEND_BUCKET}'...")
    try:
        s3_client.head_bucket(Bucket=FRONTEND_BUCKET)
        log("S3_HOSTING", f"  Bucket '{FRONTEND_BUCKET}' exists.")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            log("S3_HOSTING", f"  Creating bucket '{FRONTEND_BUCKET}' in {AWS_REGION}...")
            s3_client.create_bucket(
                Bucket=FRONTEND_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION}
            )
            log("S3_HOSTING", "  ✓ Bucket created.")
        else:
            raise e

    # Apply SSE-S3 AES-256 encryption at rest
    s3_client.put_bucket_encryption(
        Bucket=FRONTEND_BUCKET,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }
    )
    log("S3_HOSTING", "  ✓ Server-Side Encryption (AES256) enabled.")

    # Configure public access block to allow public website reading
    s3_client.put_public_access_block(
        Bucket=FRONTEND_BUCKET,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False
        }
    )
    log("S3_HOSTING", "  ✓ Public access configured for static website hosting.")

    # Configure static website hosting with SPA error routing
    s3_client.put_bucket_website(
        Bucket=FRONTEND_BUCKET,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "index.html"}  # SPA routing fallback for direct URL refreshes
        }
    )
    log("S3_HOSTING", "  ✓ S3 Static Website Hosting configured with SPA routing.")

    # Apply public read bucket policy
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{FRONTEND_BUCKET}/*"
            }
        ]
    }
    s3_client.put_bucket_policy(
        Bucket=FRONTEND_BUCKET,
        Policy=json.dumps(policy)
    )
    log("S3_HOSTING", "  ✓ S3 Public Read Bucket Policy applied.")

def upload_dist_to_s3(s3_client):
    """Upload frontend dist files to S3 with correct MIME types and Cache-Control headers."""
    log("UPLOAD", f"Uploading build assets from '{DIST_DIR}' to 's3://{FRONTEND_BUCKET}'...")
    count = 0

    for root, _, files in os.walk(DIST_DIR):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, DIST_DIR).replace("\\", "/")
            
            content_type, _ = mimetypes.guess_type(full_path)
            if not content_type:
                if file.endswith(".js") or file.endswith(".mjs"):
                    content_type = "application/javascript"
                elif file.endswith(".css"):
                    content_type = "text/css"
                elif file.endswith(".html"):
                    content_type = "text/html"
                elif file.endswith(".json"):
                    content_type = "application/json"
                elif file.endswith(".svg"):
                    content_type = "image/svg+xml"
                else:
                    content_type = "application/octet-stream"

            # Cache headers:
            # - index.html: no-cache so browsers always fetch the latest version
            # - hashed assets: immutable 1 year cache
            if rel_path == "index.html":
                cache_control = "max-age=0, must-revalidate, no-cache"
            elif rel_path.startswith("assets/"):
                cache_control = "public, max-age=31536000, immutable"
            else:
                cache_control = "public, max-age=86400"

            with open(full_path, "rb") as f:
                s3_client.put_object(
                    Bucket=FRONTEND_BUCKET,
                    Key=rel_path,
                    Body=f.read(),
                    ContentType=content_type,
                    CacheControl=cache_control
                )
            count += 1

    log("UPLOAD", f"  ✓ Uploaded {count} files to s3://{FRONTEND_BUCKET}/")

def try_deploy_cloudfront(cf_client) -> tuple:
    """Attempt CloudFront distribution deployment; return (dist_id, domain) or (None, None)."""
    log("CLOUDFRONT", "Checking CloudFront distribution capability...")
    try:
        # Check existing distributions
        dists = cf_client.list_distributions().get("DistributionList", {}).get("Items", [])
        origin_domain = f"{FRONTEND_BUCKET}.s3.{AWS_REGION}.amazonaws.com"
        for d in dists:
            for orig in d.get("Origins", {}).get("Items", []):
                if orig.get("DomainName") == origin_domain:
                    log("CLOUDFRONT", f"  Found existing distribution: {d['Id']} ({d['DomainName']})")
                    return d["Id"], d["DomainName"]

        # If none found, attempt creation
        log("CLOUDFRONT", f"  Attempting to create CloudFront distribution for {origin_domain}...")
        dist_config = {
            "CallerReference": str(time.time()),
            "Aliases": {"Quantity": 0},
            "DefaultRootObject": "index.html",
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": f"S3-{FRONTEND_BUCKET}",
                        "DomainName": origin_domain,
                        "CustomHeaders": {"Quantity": 0},
                        "S3OriginConfig": {"OriginAccessIdentity": ""}
                    }
                ]
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": f"S3-{FRONTEND_BUCKET}",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"],
                    "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}
                },
                "Compress": True,
                "ForwardedValues": {
                    "QueryString": False,
                    "Cookies": {"Forward": "none"}
                },
                "MinTTL": 0,
                "DefaultTTL": 86400,
                "MaxTTL": 31536000
            },
            "CustomErrorResponses": {
                "Quantity": 2,
                "Items": [
                    {"ErrorCode": 403, "ResponsePagePath": "/index.html", "ResponseCode": "200", "ErrorCachingMinTTL": 10},
                    {"ErrorCode": 404, "ResponsePagePath": "/index.html", "ResponseCode": "200", "ErrorCachingMinTTL": 10}
                ]
            },
            "Comment": "Serverless Document Intelligence Platform Production CDN",
            "Enabled": True
        }
        resp = cf_client.create_distribution(DistributionConfig=dist_config)
        d_info = resp["Distribution"]
        return d_info["Id"], d_info["DomainName"]
    except ClientError as e:
        log("CLOUDFRONT", f"  CloudFront notice: {e.response['Error']['Message']}")
        log("CLOUDFRONT", "  Account verification required for global CloudFront creation.")
        log("CLOUDFRONT", "  Falling back to live Amazon S3 Static Website Hosting endpoint.")
        return None, None

def update_uploads_bucket_cors(s3_client, extra_origins: list):
    """Update S3 document uploads bucket CORS to allow live production origins."""
    log("CORS", f"Updating CORS on '{UPLOADS_BUCKET}' with production origins...")
    allowed = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        S3_WEBSITE_URL,
        f"http://{FRONTEND_BUCKET}.s3-website-{AWS_REGION}.amazonaws.com"
    ]
    for o in extra_origins:
        if o and o not in allowed:
            allowed.append(o)

    cors_config = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
                "AllowedOrigins": allowed,
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600
            }
        ]
    }
    s3_client.put_bucket_cors(
        Bucket=UPLOADS_BUCKET,
        CORSConfiguration=cors_config
    )
    log("CORS", f"  ✓ Updated S3 uploads CORS configuration with {len(allowed)} origins.")

def main():
    print("=" * 80)
    print("  MILESTONE 8: PRODUCTION STATIC WEB HOSTING DEPLOYMENT")
    print("=" * 80)
    print(f" Target Region:       {AWS_REGION}")
    print(f" AWS Account:         {ACCOUNT_ID}")
    print(f" Frontend S3 Bucket:  {FRONTEND_BUCKET}")
    print(f" Uploads S3 Bucket:   {UPLOADS_BUCKET}")
    print(f" S3 Website Endpoint: {S3_WEBSITE_URL}")
    print("=" * 80)

    session = boto3.Session(region_name=AWS_REGION)
    s3_client = session.client("s3")
    cf_client = session.client("cloudfront")

    # Step 1: Build Frontend
    build_frontend_bundle()

    # Step 2: S3 Hosting Bucket & Website Configuration
    ensure_s3_hosting_bucket(s3_client)

    # Step 3: Upload files
    upload_dist_to_s3(s3_client)

    # Step 4: Check / deploy CloudFront if available
    dist_id, cf_domain = try_deploy_cloudfront(cf_client)
    extra_origins = [f"https://{cf_domain}"] if cf_domain else []

    # Step 5: Update CORS on uploads bucket
    update_uploads_bucket_cors(s3_client, extra_origins)

    primary_url = f"https://{cf_domain}" if cf_domain else S3_WEBSITE_URL

    print("\n" + "=" * 80)
    print("  ✓ MILESTONE 8 PRODUCTION HOSTING DEPLOYED SUCCESSFULLY!")
    print("=" * 80)
    print(f"• Primary Production URL:     {primary_url}")
    print(f"• Amazon S3 Website Endpoint: {S3_WEBSITE_URL}")
    if cf_domain:
        print(f"• CloudFront Distribution ID: {dist_id}")
        print(f"• CloudFront HTTPS URL:       https://{cf_domain}")
    print(f"• S3 Frontend Bucket:         {FRONTEND_BUCKET}")
    print(f"• Document Uploads Bucket:    {UPLOADS_BUCKET}")
    print(f"• API Gateway REST Endpoint:  https://wxgm03t7wc.execute-api.ap-south-1.amazonaws.com/prod")
    print(f"• CloudWatch Dashboard:       https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards/dashboard/doc-intelligence-dashboard")
    print("=" * 80)

if __name__ == "__main__":
    main()
