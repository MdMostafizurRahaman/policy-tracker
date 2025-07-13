"""
Application Configuration Settings
Centralized configuration management for the AI Policy Tracker application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

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
    
    # AI Analysis Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MAX_FILE_SIZE_MB = 10
    SUPPORTED_FILE_TYPES = [".pdf", ".doc", ".docx", ".txt"]
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")  # Should be set in .env
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "policy-tracker-files")
    
    # CloudFront CDN (optional)
    CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN", "")  # e.g. "d123456789.cloudfront.net"
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_TTL_DEFAULT = int(os.getenv("REDIS_TTL_DEFAULT", "3600"))  # 1 hour
    
    # File Upload Settings
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "pdf,doc,docx,txt,csv,xls,xlsx").split(",")
    
    # S3 Storage Configuration
    S3_PREFIX_UPLOADS = os.getenv("S3_PREFIX_UPLOADS", "policy-uploads/")
    S3_PREFIX_PROCESSED = os.getenv("S3_PREFIX_PROCESSED", "policy-processed/")
    
    @classmethod
    def get_aws_config(cls):
        """Get AWS configuration dictionary"""
        return {
            "aws_access_key_id": cls.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": cls.AWS_SECRET_ACCESS_KEY,
            "region_name": cls.AWS_REGION
        }
    
    @classmethod
    def validate_aws_config(cls):
        """Validate that required AWS configuration is present"""
        if not cls.AWS_SECRET_ACCESS_KEY:
            raise ValueError("AWS_SECRET_ACCESS_KEY must be set in environment variables")
        
        if not cls.AWS_S3_BUCKET:
            raise ValueError("AWS_S3_BUCKET must be set in environment variables")
        
        return True

# Create a global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings instance"""
    return settings
