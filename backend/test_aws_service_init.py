#!/usr/bin/env python3
"""
Test AWS service initialization
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import and test
try:
    from services.aws_service import aws_service
    
    print("=== AWS Service Test ===")
    print(f"AWS Access Key: {aws_service.aws_access_key[:10] + '...' if aws_service.aws_access_key else 'None'}")
    print(f"AWS Secret Key: {aws_service.aws_secret_key[:10] + '...' if aws_service.aws_secret_key else 'None'}")
    print(f"AWS Region: {aws_service.aws_region}")
    print(f"S3 Bucket: {aws_service.bucket_name}")
    print(f"CloudFront Domain: {aws_service.cloudfront_domain}")
    
    # Test if S3 client is initialized
    print(f"S3 Client initialized: {hasattr(aws_service, 's3_client') and aws_service.s3_client is not None}")
    
except Exception as e:
    print(f"Error importing aws_service: {e}")
    import traceback
    traceback.print_exc()
