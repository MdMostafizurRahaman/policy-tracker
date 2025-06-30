"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    EmailVerification, PasswordReset, ForgotPassword, GoogleAuth
)
from services.auth_service import AuthService
from services.email_service import EmailService
from config.database import get_database
from typing import Optional
import os

router = APIRouter()
security = HTTPBearer()

def get_auth_service():
    """Get auth service instance"""
    db = get_database()
    return AuthService(db)

def get_email_service():
    """Get email service instance"""
    return EmailService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = await auth_service.get_user_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Register new user"""
    try:
        result = await auth_service.create_user(user_data)
        
        # Send verification email
        email_sent = email_service.send_verification_email(
            user_data.email, 
            result["otp"], 
            user_data.firstName
        )
        
        return {
            "message": "User registered successfully",
            "email_sent": email_sent,
            "otp_for_dev": result["otp"] if not email_sent else None
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/verify-email", response_model=dict)
async def verify_email(
    verification: EmailVerification,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify user email with OTP"""
    try:
        success = await auth_service.verify_user_email(verification.email, verification.otp)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )
        
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user"""
    try:
        user = await auth_service.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token
        token = auth_service.create_access_token({"sub": user.id})
        
        return TokenResponse(
            access_token=token,
            user=user
        )
        
    except ValueError as e:
        if "verify" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please verify your email first"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/admin-login", response_model=TokenResponse)
async def admin_login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Admin login with enhanced validation"""
    try:
        user = await auth_service.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Create access token
        token = auth_service.create_access_token({"sub": user.id})
        
        return TokenResponse(
            access_token=token,
            user=user
        )
        
    except ValueError as e:
        if "verify" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please verify your email first"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin login failed"
        )

@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    forgot_data: ForgotPassword,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Send password reset OTP"""
    try:
        # Check if user exists
        user = await auth_service.users_collection.find_one({"email": forgot_data.email})
        if not user:
            # Don't reveal if email exists or not
            return {"message": "If the email exists, a reset code has been sent"}
        
        # Generate OTP and save
        otp = auth_service.generate_otp()
        from datetime import datetime, timedelta
        
        await auth_service.users_collection.update_one(
            {"email": forgot_data.email},
            {
                "$set": {
                    "reset_otp": otp,
                    "reset_otp_expires": datetime.utcnow() + timedelta(minutes=10)
                }
            }
        )
        
        # Send reset email
        email_sent = email_service.send_password_reset_email(
            forgot_data.email,
            otp,
            user["firstName"]
        )
        
        return {
            "message": "Password reset code sent to your email",
            "email_sent": email_sent,
            "otp_for_dev": otp if not email_sent else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset code"
        )

@router.post("/reset-password", response_model=dict)
async def reset_password(
    reset_data: PasswordReset,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password with OTP"""
    try:
        from datetime import datetime
        
        # Find user with valid reset OTP
        user = await auth_service.users_collection.find_one({
            "email": reset_data.email,
            "reset_otp": reset_data.otp,
            "reset_otp_expires": {"$gt": datetime.utcnow()}
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset code"
            )
        
        # Hash new password
        hashed_password = auth_service.hash_password(reset_data.newPassword)
        
        # Update password and remove reset OTP
        await auth_service.users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"password": hashed_password},
                "$unset": {"reset_otp": "", "reset_otp_expires": ""}
            }
        )
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/google", response_model=TokenResponse)
async def google_auth(
    google_data: GoogleAuth,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Google OAuth authentication"""
    # This would need Google OAuth implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google authentication not implemented yet"
    )

@router.get("/dev/latest-otp/{email}")
async def get_latest_otp(
    email: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get latest OTP for development/testing (only in dev mode)"""
    try:
        # This should only work in development mode
        if not os.getenv("DEBUG_MODE", "false").lower() == "true":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endpoint not found"
            )
        
        user = await auth_service.users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return verification OTP if exists
        verification_otp = user.get("verification_otp")
        reset_otp = user.get("reset_otp")
        
        return {
            "email": email,
            "verification_otp": verification_otp,
            "reset_otp": reset_otp,
            "note": "This endpoint only works in development mode"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get OTP"
        )
