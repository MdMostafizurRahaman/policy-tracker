"""
Core configuration for the AI Policy Tracker application.
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Enhanced AI Policy Database API"
    VERSION: str = "4.0.0"
    DESCRIPTION: str = "Complete AI Policy Management System with Authentication, Submissions, and Admin Dashboard"
    
    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    MONGODB_URL: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/ai_policy_db")
    DATABASE_NAME: str = "ai_policy_database"
    
    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@aipolicytracker.com")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    
    # CORS Origins
    ALLOWED_ORIGINS: List[str] = [
        "https://policy-tracker-5.onrender.com",
        "https://policy-tracker-f.onrender.com", 
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "http://192.168.56.1:3000"
    ]
    
    # Admin Configuration
    SUPER_ADMIN_EMAIL: str = "admin@gmail.com"
    SUPER_ADMIN_PASSWORD: str = "admin123"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        case_sensitive = True

# Global settings instance
settings = Settings()
