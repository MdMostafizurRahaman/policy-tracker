"""
Authentication service for user management.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException
from bson import ObjectId
from core.database import get_collections
from core.security import hash_password, verify_password, create_access_token
from core.config import settings
from utils.helpers import convert_objectid, generate_otp
from services.email_service import email_service

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        # Collections will be accessed dynamically to avoid initialization issues
        pass
    
    def _get_collections(self):
        """Get collections dynamically"""
        return get_collections()
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        try:
            logger.info(f"Registration attempt for: {user_data['email']}")
            
            # Check if user already exists
            collections = self._get_collections()
            existing_user = await collections["users"].find_one({"email": user_data["email"]})
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Hash password
            hashed_password = hash_password(user_data["password"])
            
            # Create user document
            user_doc = {
                "firstName": user_data["firstName"],
                "lastName": user_data["lastName"],
                "email": user_data["email"],
                "password": hashed_password,
                "country": user_data["country"],
                "is_admin": False,
                "is_verified": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Save user
            result = await collections["users"].insert_one(user_doc)
            logger.info(f"User created with ID: {result.inserted_id}")
            
            # Clean up existing OTPs for this email
            await collections["otp_codes"].delete_many({
                "email": user_data["email"],
                "type": "email_verification"
            })
            
            # Generate and save OTP
            otp = generate_otp()
            otp_doc = {
                "email": user_data["email"],
                "otp": otp,
                "type": "email_verification",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            }
            await collections["otp_codes"].insert_one(otp_doc)
            logger.info(f"OTP generated and saved for {user_data['email']}: {otp}")
            
            # Send verification email
            email_sent = await email_service.send_verification_email(
                user_data["email"], 
                user_data["firstName"], 
                otp
            )
            
            logger.info(f"Registration completed for {user_data['email']}, email_sent: {email_sent}")
            
            # Return different messages based on email status
            if email_sent:
                message = "Account created successfully! Please check your email for verification code."
            else:
                message = f"Account created! Email sending failed. Your OTP is: {otp} (Use this to verify)"
            
            return {
                "success": True,
                "message": message,
                "user_id": str(result.inserted_id),
                "email_sent": email_sent,
                "otp_for_dev": otp if not email_sent else None
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def verify_email(self, email: str, otp: str) -> Dict[str, Any]:
        """Verify user email with OTP"""
        try:
            collections = self._get_collections()
            
            # Find valid OTP
            otp_doc = await collections["otp_codes"].find_one({
                "email": email,
                "otp": otp,
                "type": "email_verification",
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not otp_doc:
                raise HTTPException(status_code=400, detail="Invalid or expired verification code")
            
            # Update user as verified
            result = await collections["users"].update_one(
                {"email": email},
                {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete used OTP
            await collections["otp_codes"].delete_one({"_id": otp_doc["_id"]})
            
            logger.info(f"Email verified successfully for {email}")
            return {"success": True, "message": "Email verified successfully"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and return access token"""
        try:
            collections = self._get_collections()
            
            # Find user
            user = await collections["users"].find_one({"email": email})
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Verify password
            if not verify_password(password, user["password"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Check if email is verified
            if not user.get("is_verified", False):
                raise HTTPException(
                    status_code=401, 
                    detail="Please verify your email first. Check your inbox for verification code."
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user["email"]}, expires_delta=access_token_expires
            )
            
            # Update last login
            await collections["users"].update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            logger.info(f"User logged in successfully: {email}")
            
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
                    "is_verified": user.get("is_verified", False)
                }
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    
    async def forgot_password(self, email: str) -> Dict[str, Any]:
        """Send password reset OTP"""
        try:
            collections = self._get_collections()
            
            # Check if user exists
            user = await collections["users"].find_one({"email": email})
            if not user:
                # Don't reveal if email exists or not for security
                return {"success": True, "message": "If the email exists, a reset code has been sent"}
            
            # Clean up existing OTPs
            await collections["otp_codes"].delete_many({
                "email": email,
                "type": "password_reset"
            })
            
            # Generate and save OTP
            otp = generate_otp()
            otp_doc = {
                "email": email,
                "otp": otp,
                "type": "password_reset",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            }
            await collections["otp_codes"].insert_one(otp_doc)
            
            # Send password reset email
            await email_service.send_password_reset_email(
                email, 
                user["firstName"], 
                otp
            )
            
            return {"success": True, "message": "Password reset code sent to your email"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")
    
    async def reset_password(self, email: str, otp: str, new_password: str) -> Dict[str, Any]:
        """Reset user password with OTP"""
        try:
            collections = self._get_collections()
            
            # Find valid OTP
            otp_doc = await collections["otp_codes"].find_one({
                "email": email,
                "otp": otp,
                "type": "password_reset",
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not otp_doc:
                raise HTTPException(status_code=400, detail="Invalid or expired reset code")
            
            # Hash new password
            hashed_password = hash_password(new_password)
            
            # Update user password
            result = await collections["users"].update_one(
                {"email": email},
                {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete used OTP
            await collections["otp_codes"].delete_one({"_id": otp_doc["_id"]})
            
            logger.info(f"Password reset successfully for {email}")
            return {"success": True, "message": "Password reset successfully"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

# Global auth service instance
auth_service = AuthService()
