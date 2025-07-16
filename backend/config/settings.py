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
    
    # All configuration loaded from .env file
    # JWT and Security Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Legacy alias
    ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # Legacy alias
    
    # Email Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
    FROM_EMAIL = os.getenv("FROM_EMAIL")  # Legacy alias
    
    # Frontend Configuration
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    
    # Database
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    
    # DynamoDB Configuration
    DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "")
    AWS_DYNAMODB_REGION = os.getenv("AWS_DYNAMODB_REGION", "us-east-1")
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
    
    # Admin
    SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL")
    SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")
    
    # File Upload
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "pdf,doc,docx,txt").split(",")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # AI Analysis
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_API_URL = os.getenv("GROQ_API_URL")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    SUPPORTED_FILE_TYPES = os.getenv("SUPPORTED_FILE_TYPES", ".pdf,.doc,.docx,.txt").split(",")
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
    
    # CloudFront
    CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL")
    REDIS_TTL_DEFAULT = int(os.getenv("REDIS_TTL_DEFAULT", "3600"))
    
    # S3 Storage
    S3_PREFIX_UPLOADS = os.getenv("S3_PREFIX_UPLOADS")
    S3_PREFIX_PROCESSED = os.getenv("S3_PREFIX_PROCESSED")
    
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
        if not cls.AWS_ACCESS_KEY_ID:
            raise ValueError("AWS_ACCESS_KEY_ID must be set in environment variables")
            
        if not cls.AWS_SECRET_ACCESS_KEY:
            raise ValueError("AWS_SECRET_ACCESS_KEY must be set in environment variables")
        
        if not cls.AWS_S3_BUCKET:
            raise ValueError("AWS_S3_BUCKET must be set in environment variables")
            
        if not cls.AWS_REGION:
            raise ValueError("AWS_REGION must be set in environment variables")
        
        return True

# Create a global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings instance"""
    return settings
