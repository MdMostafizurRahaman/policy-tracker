import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App configuration
APP_TITLE = "AI Policy Database API with Admin Workflow"
APP_VERSION = "1.0.0"

# File upload configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Database configuration
MONGODB_URL = os.getenv("MONGO_URI")

# Chatbot configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# CORS configuration
ALLOWED_ORIGINS = [
    "https://policy-tracker-f.onrender.com", 
    "http://localhost:3000"
]