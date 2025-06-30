"""
Authentication Controller
Handles HTTP requests for authentication operations
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from services.auth_service import get_auth_service
from models.user import UserRegistration, UserLogin, GoogleAuthRequest, OTPVerification, PasswordReset
from config.settings import settings
import os

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    auth_service = get_auth_service()
    return await auth_service.register_user(user_data)

@router.post("/login")
async def login_user(login_data: UserLogin):
    """Authenticate user login"""
    auth_service = get_auth_service()
    return await auth_service.login_user(login_data)

@router.post("/google")
async def google_auth(request: GoogleAuthRequest):
    """Handle Google OAuth authentication"""
    auth_service = get_auth_service()
    return await auth_service.google_auth(request)

@router.post("/verify-email")
async def verify_email(verification: OTPVerification):
    """Verify user email with OTP"""
    auth_service = get_auth_service()
    return await auth_service.verify_email(verification)

@router.post("/forgot-password")
async def forgot_password(email_data: dict):
    """Send password reset OTP"""
    email = email_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    auth_service = get_auth_service()
    return await auth_service.forgot_password(email)

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset user password with OTP"""
    auth_service = get_auth_service()
    return await auth_service.reset_password(reset_data)

@router.post("/admin-login")
async def admin_login(login_data: UserLogin):
    """Admin login with special admin privileges check"""
    auth_service = get_auth_service()
    result = await auth_service.login_user(login_data)
    
    # Check if user has admin privileges
    if not result.get("user", {}).get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return result

@router.get("/dev/get-latest-otp/{email}")
async def get_latest_otp_for_development(email: str):
    """Development endpoint to get latest OTP (remove in production)"""
    try:
        # Only allow in development
        if os.getenv("ENVIRONMENT") == "production":
            raise HTTPException(status_code=404, detail="Not found")
        
        from config.database import get_otp_collection
        
        otp_collection = get_otp_collection()
        otp_doc = await otp_collection.find_one(
            {"email": email},
            sort=[("created_at", -1)]  # Get the latest OTP
        )
        
        if not otp_doc:
            return {"success": False, "message": "No OTP found for this email"}
        
        return {
            "success": True,
            "email": email,
            "otp": otp_doc["otp"],
            "type": otp_doc["type"],
            "expires_at": otp_doc["expires_at"],
            "created_at": otp_doc["created_at"]
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}
