#!/usr/bin/env python3
"""
Test the fixed AWS service initialization
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_aws_service():
    print("=== Testing Fixed AWS Service ===\n")
    
    try:
        # Import the AWS service
        from services.aws_service import aws_service
        
        print("✅ AWS Service imported successfully")
        
        # Check if all required variables are loaded
        required_vars = {
            'AWS Access Key': aws_service.aws_access_key,
            'AWS Secret Key': aws_service.aws_secret_key,
            'AWS Region': aws_service.aws_region,
            'S3 Bucket': aws_service.bucket_name
        }
        
        all_loaded = True
        for var_name, var_value in required_vars.items():
            if var_value:
                if 'Key' in var_name:
                    print(f"✅ {var_name}: {var_value[:8]}...{var_value[-4:]}")
                else:
                    print(f"✅ {var_name}: {var_value}")
            else:
                print(f"❌ {var_name}: NOT SET")
                all_loaded = False
        
        print(f"\n🔍 CloudFront Domain: {aws_service.cloudfront_domain or 'Not configured (optional)'}")
        
        # Check if S3 client is initialized
        if hasattr(aws_service, 's3_client') and aws_service.s3_client is not None:
            print("✅ S3 Client: Initialized")
        else:
            print("❌ S3 Client: Not initialized")
            all_loaded = False
        
        if all_loaded:
            print("\n🎉 AWS Service is properly configured!")
        else:
            print("\n⚠️  Some AWS configuration is missing. Check your .env file.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_aws_service()
