#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the backend directory
backend_dir = Path(__file__).parent
env_path = backend_dir / '.env'
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {env_path.exists()}")

load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv('GROQ_API_KEY')
print(f"GROQ_API_KEY found: {groq_api_key is not None}")
if groq_api_key:
    print(f"GROQ_API_KEY value (first 10 chars): {groq_api_key[:10]}")
    print(f"GROQ_API_KEY length: {len(groq_api_key)}")
else:
    print("GROQ_API_KEY is None or empty")

# List all environment variables that start with GROQ
print("\nAll GROQ-related environment variables:")
for key, value in os.environ.items():
    if 'GROQ' in key.upper():
        print(f"{key}: {value[:10]}..." if value else f"{key}: {value}")
