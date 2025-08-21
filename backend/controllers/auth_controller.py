"""
Authentication Controller
Handles HTTP requests for authentication operations
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from services.auth_service_dynamodb import auth_service
from models.user import UserRegistration, UserLogin, GoogleAuthRequest, OTPVerification, PasswordReset, AdminLogin
from middleware.auth import get_current_user
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register")
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        return await auth_service.register_user(user_data)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login_user(login_data: UserLogin):
    """Authenticate user login"""
    try:
        return await auth_service.login_user(login_data)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/google")
async def google_auth(request: GoogleAuthRequest):
    """Handle Google OAuth authentication"""
    try:
        return await auth_service.google_auth(request)
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-email")
async def verify_email(verification: OTPVerification):
    """Verify user email with OTP"""
    try:
        return await auth_service.verify_email(verification)
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forgot-password")
async def forgot_password(email_data: dict):
    """Send password reset OTP"""
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        return await auth_service.forgot_password(email)
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/resend-otp")
async def resend_otp(email_data: dict):
    """Resend email verification OTP"""
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        return await auth_service.resend_otp(email)
    except Exception as e:
        logger.error(f"Resend OTP error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset user password with OTP"""
    try:
        return await auth_service.reset_password(reset_data)
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin-login")
async def admin_login(login_data: AdminLogin):
    """Admin login with special admin privileges"""
    try:
        return await auth_service.admin_login(login_data)
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    try:
        return {
            "success": True,
            "user": current_user
        }
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/dev/get-latest-otp/{email}")
async def get_latest_otp_for_development(email: str):
    """Development endpoint to get latest OTP (remove in production)"""
    try:
        # Only allow in development
        if os.getenv("ENVIRONMENT") == "production":
            raise HTTPException(status_code=404, detail="Not found")
        
        return await auth_service.get_latest_otp(email)
    
    except Exception as e:
        logger.error(f"Get OTP error: {str(e)}")
        return {"success": False, "error": str(e)}
