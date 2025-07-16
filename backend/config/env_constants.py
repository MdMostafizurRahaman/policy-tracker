"""
Environment Variable Constants
This file maps environment variable names to make them clickable/navigable to the .env file.
All these variables are defined in: backend/.env
"""

# Database Configuration (defined in .env)
DATABASE_NAME = "DATABASE_NAME"

# JWT and Security (defined in .env)
JWT_SECRET_KEY = "JWT_SECRET_KEY"
JWT_ALGORITHM = "JWT_ALGORITHM"
ACCESS_TOKEN_EXPIRE_MINUTES = "ACCESS_TOKEN_EXPIRE_MINUTES"

# Email Configuration (defined in .env)
SMTP_SERVER = "SMTP_SERVER"
SMTP_PORT = "SMTP_PORT"
SMTP_USERNAME = "SMTP_USERNAME"
SMTP_PASSWORD = "SMTP_PASSWORD"
FROM_EMAIL = "FROM_EMAIL"

# Google OAuth (defined in .env)
GOOGLE_CLIENT_ID = "GOOGLE_CLIENT_ID"

# CORS Configuration (defined in .env)
ALLOWED_ORIGINS = "ALLOWED_ORIGINS"

# Admin Credentials (defined in .env)
SUPER_ADMIN_EMAIL = "SUPER_ADMIN_EMAIL"
SUPER_ADMIN_PASSWORD = "SUPER_ADMIN_PASSWORD"

# File Upload Settings (defined in .env)
UPLOAD_DIR = "UPLOAD_DIR"
MAX_FILE_SIZE = "MAX_FILE_SIZE"
ALLOWED_FILE_TYPES = "ALLOWED_FILE_TYPES"

# Environment (defined in .env)
ENVIRONMENT = "ENVIRONMENT"

# AI Analysis (defined in .env)
GROQ_API_KEY = "GROQ_API_KEY"
GROQ_API_URL = "GROQ_API_URL"
MAX_FILE_SIZE_MB = "MAX_FILE_SIZE_MB"
SUPPORTED_FILE_TYPES = "SUPPORTED_FILE_TYPES"

# AWS Configuration (defined in .env)
AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
AWS_REGION = "AWS_REGION"
AWS_S3_BUCKET = "AWS_S3_BUCKET"

# CloudFront (defined in .env)
CLOUDFRONT_DOMAIN = "CLOUDFRONT_DOMAIN"

# Redis Configuration (defined in .env)
REDIS_URL = "REDIS_URL"
REDIS_TTL_DEFAULT = "REDIS_TTL_DEFAULT"

# S3 Storage (defined in .env)
S3_PREFIX_UPLOADS = "S3_PREFIX_UPLOADS"
S3_PREFIX_PROCESSED = "S3_PREFIX_PROCESSED"
