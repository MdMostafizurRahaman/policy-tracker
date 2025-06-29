"""
Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from models.auth import UserRegistration, UserLogin, GoogleAuthRequest, OTPVerification, PasswordReset
from services.auth_service import auth_service
from core.security import get_current_user
from core.database import get_collections
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register")
async def register_user(user_data: UserRegistration):
    """Enhanced user registration with better validation and email handling"""
    return await auth_service.register_user(user_data.dict())

@router.post("/verify-email")
async def verify_email(verification: OTPVerification):
    """Enhanced email verification"""
    return await auth_service.verify_email(verification.email, verification.otp)

@router.post("/login")
async def login_user(login_data: UserLogin):
    """Enhanced user login"""
    return await auth_service.login_user(login_data.email, login_data.password)

@router.post("/google")
async def google_auth(request: GoogleAuthRequest):
    """Enhanced Google OAuth authentication with better error handling"""
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
        from core.config import settings
        from core.database import get_collections
        from core.security import create_access_token
        from utils.helpers import convert_objectid
        from datetime import datetime
        
        # Check if Google Client ID is configured
        if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "641700598182-a8mlt3q0dbi7e71ugr581jjhmi020n88.apps.googleusercontent.com":
            logger.error("Google Client ID not configured")
            raise HTTPException(
                status_code=501, 
                detail="Google authentication is not configured on the server"
            )
        
        logger.info(f"Attempting Google auth with Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")
        logger.info(f"Token received (first 50 chars): {request.token[:50]}...")
        
        # Verify the Google token with enhanced error handling
        try:
            idinfo = id_token.verify_oauth2_token(
                request.token, 
                google_requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )
            logger.info("Google token verified successfully")
            
        except ValueError as e:
            logger.error(f"Google token verification failed: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid Google token: {str(e)}"
            )

        # Validate issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            logger.error(f"Invalid issuer: {idinfo['iss']}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid token issuer"
            )

        # Extract user information
        google_user_id = idinfo['sub']
        email = idinfo['email']
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        logger.info(f"Google user info: {email}, {first_name} {last_name}")
        
        collections = get_collections()
        
        # Check if user exists
        existing_user = await collections["users"].find_one({"email": email})
        
        if existing_user:
            logger.info(f"Existing user found: {email}")
            # Update user info and mark as Google authenticated
            await collections["users"].update_one(
                {"email": email},
                {
                    "$set": {
                        "google_id": google_user_id,
                        "google_auth": True,
                        "is_verified": True,  # Google users are pre-verified
                        "updated_at": datetime.utcnow(),
                        "last_login": datetime.utcnow()
                    }
                }
            )
            user = await collections["users"].find_one({"email": email})
        else:
            logger.info(f"Creating new user: {email}")
            # Create new user
            new_user = {
                "firstName": first_name or "Google",
                "lastName": last_name or "User",
                "email": email,
                "google_id": google_user_id,
                "google_auth": True,
                "is_verified": True,
                "is_admin": False,
                "country": "Not specified",  # Can be updated later
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            
            result = await collections["users"].insert_one(new_user)
            user = await collections["users"].find_one({"_id": result.inserted_id})

        # Generate JWT token
        access_token = create_access_token(data={"sub": user["email"]})
        
        # Convert ObjectId for response
        user = convert_objectid(user)
        
        logger.info(f"Google authentication successful for {email}")
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "firstName": user["firstName"],
                "lastName": user["lastName"],
                "email": user["email"],
                "country": user["country"],
                "is_admin": user.get("is_admin", False),
                "is_verified": user.get("is_verified", True)
            },
            "message": "Google authentication successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Google authentication failed: {str(e)}"
        )

@router.post("/forgot-password")
async def forgot_password(email_data: dict):
    """Enhanced forgot password with better email"""
    email = email_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    return await auth_service.forgot_password(email)

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Enhanced password reset"""
    return await auth_service.reset_password(
        reset_data.email, 
        reset_data.otp, 
        reset_data.newPassword
    )

@router.get("/dev/get-latest-otp/{email}")
async def get_latest_otp_for_development(email: str):
    """Development endpoint to get latest OTP (remove in production)"""
    try:
        from core.config import settings
        
        # Only allow in development
        if settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=404, detail="Not found")
        
        # Log warning when this endpoint is accessed
        logger.warning(f"🚨 DEVELOPMENT OTP ENDPOINT ACCESSED for {email}")
        
        collections = get_collections()
        otp_doc = await collections["otp_codes"].find_one(
            {"email": email},
            sort=[("created_at", -1)]  # Get the latest OTP
        )
        
        if not otp_doc:
            return {"success": False, "message": "No OTP found for this email"}
        
        logger.warning(f"🚨 DEVELOPMENT OTP RETURNED: {otp_doc['otp']} for {email}")
        
        return {
            "success": True,
            "email": email,
            "otp": otp_doc["otp"],
            "type": otp_doc["type"],
            "expires_at": otp_doc["expires_at"],
            "created_at": otp_doc["created_at"]
        }
    
    except Exception as e:
        logger.error(f"Error getting development OTP: {str(e)}")
        return {"success": False, "error": str(e)}
