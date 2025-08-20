#!/usr/bin/env python3
"""
Development server startup script for Policy Tracker Backend
Loads environment variables and starts the server with proper configuration
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Change to backend directory
os.chdir(backend_dir)

# Load environment variables from .env file
env_file = backend_dir / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                os.environ[key] = value

# Import and run the main application
if __name__ == "__main__":
    # Import uvicorn and settings after setting up environment
    import uvicorn
    from config.settings import settings
    
    # Get configuration from environment
    host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    port = int(os.environ.get("BACKEND_PORT", os.environ.get("PORT", 8000)))
    
    print(f"🚀 Starting Policy Tracker Backend")
    print(f"📊 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌍 Frontend URL: {os.environ.get('FRONTEND_URL', 'http://localhost:3003')}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
