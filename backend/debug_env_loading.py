#!/usr/bin/env python3
"""
Debug script to test environment variable loading
Run this from the backend directory to debug .env loading issues
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def debug_env_loading():
    print("=== Environment Variable Loading Debug ===\n")
    
    # Get current working directory
    cwd = Path.cwd()
    print(f"Current working directory: {cwd}")
    
    # Get script directory
    script_dir = Path(__file__).parent
    print(f"Script directory: {script_dir}")
    
    # Try multiple .env locations
    env_locations = [
        script_dir / '.env',  # backend/.env
        script_dir / 'services' / '.env',  # services/.env
        cwd / '.env',  # current working directory
        cwd / 'backend' / '.env'  # cwd/backend/.env
    ]
    
    print(f"\nChecking .env file locations:")
    env_loaded = False
    for i, env_location in enumerate(env_locations, 1):
        exists = env_location.exists()
        print(f"{i}. {env_location} - {'EXISTS' if exists else 'NOT FOUND'}")
        
        if exists and not env_loaded:
            print(f"   -> Loading from: {env_location}")
            load_dotenv(dotenv_path=env_location)
            env_loaded = True
    
    if not env_loaded:
        print("\nNo .env file found, trying default load_dotenv()...")
        load_dotenv()
    
    # Test AWS environment variables
    print(f"\n=== AWS Environment Variables ===")
    aws_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION',
        'AWS_S3_BUCKET',
        'CLOUDFRONT_DOMAIN'
    ]
    
    for var in aws_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'SECRET' in var:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                print(f"{var}: {masked_value}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: NOT SET")
    
    # Test other environment variables
    print(f"\n=== Other Environment Variables ===")
    other_vars = ['MONGO_URI', 'GEMINI_API_KEY', 'GROQ_API_KEY']
    
    for var in other_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'URI' in var:
                masked_value = value[:10] + '*' * (len(value) - 20) + value[-10:] if len(value) > 20 else '*' * len(value)
                print(f"{var}: {masked_value}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: NOT SET")
    
    # Show all environment variables that start with AWS
    print(f"\n=== All AWS-related Environment Variables ===")
    aws_env_vars = {k: v for k, v in os.environ.items() if k.startswith('AWS')}
    if aws_env_vars:
        for key, value in aws_env_vars.items():
            if 'KEY' in key or 'SECRET' in key:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                print(f"{key}: {masked_value}")
            else:
                print(f"{key}: {value}")
    else:
        print("No AWS environment variables found in os.environ")

if __name__ == "__main__":
    debug_env_loading()
