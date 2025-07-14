#!/usr/bin/env python3
"""
Test AWS Service specifically
"""
import sys
import logging
from pathlib import Path

# Set up logging to see the debug messages
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

print("=== Testing AWS Service ===\n")

try:
    print("Importing AWS Service...")
    from services.aws_service import AWSService
    
    print("Creating AWS Service instance...")
    aws_service = AWSService()
    
    print("\n--- Direct Variable Check ---")
    print(f"Access Key: {'✓ Set' if aws_service.aws_access_key else '✗ NOT SET'}")
    print(f"Secret Key: {'✓ Set' if aws_service.aws_secret_key else '✗ NOT SET'}")
    print(f"Region: {aws_service.aws_region or '✗ NOT SET'}")
    print(f"Bucket: {aws_service.bucket_name or '✗ NOT SET'}")
    print(f"CloudFront: {aws_service.cloudfront_domain or 'Not configured'}")
    
    if all([aws_service.aws_access_key, aws_service.aws_secret_key, aws_service.aws_region, aws_service.bucket_name]):
        print("\n✅ All AWS environment variables are working!")
        
        # Test S3 client creation
        try:
            print("\n--- Testing S3 Client ---")
            print(f"S3 Client: {'✓ Created' if hasattr(aws_service, 's3_client') and aws_service.s3_client else '✗ Failed'}")
            print(f"S3 Resource: {'✓ Created' if hasattr(aws_service, 's3_resource') and aws_service.s3_resource else '✗ Failed'}")
        except Exception as e:
            print(f"✗ S3 Client Error: {e}")
    else:
        print("\n❌ Some AWS environment variables are missing!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
