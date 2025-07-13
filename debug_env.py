#!/usr/bin/env python3
"""
Debug AWS environment variable loading
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=== AWS Environment Variable Debug ===\n")

# Check current working directory
print(f"Current working directory: {os.getcwd()}")

# Check if .env file exists in backend directory
backend_env = Path("backend/.env")
print(f"Backend .env exists: {backend_env.exists()}")
if backend_env.exists():
    print(f"Backend .env path: {backend_env.absolute()}")

# Try different loading methods
print("\n--- Method 1: Load from backend/.env ---")
if backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
    print("✓ Loaded backend/.env")
else:
    print("✗ backend/.env not found")

# Check environment variables
aws_vars = [
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY', 
    'AWS_REGION',
    'AWS_S3_BUCKET'
]

print("\n--- Environment Variables Status ---")
for var in aws_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive data
        if 'SECRET' in var or 'KEY' in var:
            display = f"{value[:8]}..." if len(value) > 8 else "***"
        else:
            display = value
        print(f"{var}: ✓ {display}")
    else:
        print(f"{var}: ✗ NOT SET")

# Try the same path resolution as the AWS service
print("\n--- AWS Service Path Resolution ---")
current_dir = Path(__file__).parent / 'backend' / 'services'
backend_dir = current_dir.parent
env_path = backend_dir / '.env'

print(f"Service current_dir: {current_dir}")
print(f"Service backend_dir: {backend_dir}")
print(f"Service env_path: {env_path}")
print(f"Service env_path exists: {env_path.exists()}")

if env_path.exists():
    print("\n--- Reloading with service path ---")
    load_dotenv(dotenv_path=env_path, override=True)
    
    print("After reload:")
    for var in aws_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var or 'KEY' in var:
                display = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display = value
            print(f"{var}: ✓ {display}")
        else:
            print(f"{var}: ✗ NOT SET")
