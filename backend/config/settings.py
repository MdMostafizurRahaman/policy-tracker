"""
Application Configuration Settings
Centralized configuration management for the AI Policy Tracker application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Application Info
    APP_NAME = "Enhanced AI Policy Database API"
    APP_VERSION = "4.0.0"
    APP_DESCRIPTION = "Complete AI Policy Management System with Authentication, Submissions, and Admin Dashboard"
    
    # JWT and Security Configuration
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-here-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
    
    # Enhanced Email Configuration with fallback
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@aipolicytracker.com")
    
    # Google OAuth Configuration with fallback
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    
    # MongoDB Configuration
    MONGODB_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017/ai_policy_db")
    DATABASE_NAME = "ai_policy_database"
    
    # CORS Configuration
    ALLOWED_ORIGINS = [
        "https://policy-tracker-5.onrender.com",
        "https://policy-tracker-f.onrender.com", 
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "http://192.168.56.1:3000"
    ]
    
    # Admin Configuration
    SUPER_ADMIN_EMAIL = "admin@gmail.com"
    SUPER_ADMIN_PASSWORD = "admin123"
    
    # File Upload Configuration
    UPLOAD_DIR = "uploads"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Create a global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings instance"""
    return settings
