"""
<<<<<<< HEAD
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
=======
Authentication Service
Business logic for user authentication, registration, and password management
"""
from datetime import datetime, timedelta
from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config.database import get_users_collection, get_otp_collection
from config.settings import settings
from utils.security import hash_password, verify_password, create_access_token, generate_otp
from utils.converters import convert_objectid
from services.email_service import send_email
from models.user import UserRegistration, UserLogin, GoogleAuthRequest, OTPVerification, PasswordReset
import logging
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2

logger = logging.getLogger(__name__)

class AuthService:
<<<<<<< HEAD
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
=======
    """Authentication service for user management"""
    
    def __init__(self):
        self.users_collection = get_users_collection()
        self.otp_collection = get_otp_collection()
    
    async def register_user(self, user_data: UserRegistration):
        """Register a new user"""
        try:
            logger.info(f"Registration attempt for: {user_data.email}")
            
            # Check if user already exists
            existing_user = await self.users_collection.find_one({"email": user_data.email})
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Hash password
<<<<<<< HEAD
            hashed_password = hash_password(user_data["password"])
            
            # Create user document
            user_doc = {
                "firstName": user_data["firstName"],
                "lastName": user_data["lastName"],
                "email": user_data["email"],
                "password": hashed_password,
                "country": user_data["country"],
=======
            hashed_password = hash_password(user_data.password)
            
            # Create user document
            user_doc = {
                "firstName": user_data.firstName,
                "lastName": user_data.lastName,
                "email": user_data.email,
                "password": hashed_password,
                "country": user_data.country,
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
                "is_admin": False,
                "is_verified": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Save user
<<<<<<< HEAD
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
=======
            result = await self.users_collection.insert_one(user_doc)
            logger.info(f"User created with ID: {result.inserted_id}")
            
            # Generate and send OTP
            otp_sent = await self._send_verification_otp(user_data.email, user_data.firstName)
            
            return {
                "success": True,
                "message": "Account created successfully! Please check your email for verification code." if otp_sent else f"Account created! Email sending failed.",
                "user_id": str(result.inserted_id),
                "email_sent": otp_sent
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
<<<<<<< HEAD
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
=======
    async def login_user(self, login_data: UserLogin):
        """Authenticate user login"""
        try:
            # Find user
            user = await self.users_collection.find_one({"email": login_data.email})
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Verify password
<<<<<<< HEAD
            if not verify_password(password, user["password"]):
=======
            if not verify_password(login_data.password, user["password"]):
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
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
<<<<<<< HEAD
            await collections["users"].update_one(
=======
            await self.users_collection.update_one(
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
<<<<<<< HEAD
            logger.info(f"User logged in successfully: {email}")
=======
            logger.info(f"User logged in successfully: {login_data.email}")
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
            
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
    
<<<<<<< HEAD
    async def forgot_password(self, email: str) -> Dict[str, Any]:
        """Send password reset OTP"""
        try:
            collections = self._get_collections()
            
            # Check if user exists
            user = await collections["users"].find_one({"email": email})
=======
    async def google_auth(self, request: GoogleAuthRequest):
        """Handle Google OAuth authentication"""
        try:
            # Check if Google Client ID is configured
            if not settings.GOOGLE_CLIENT_ID:
                logger.error("Google Client ID not configured")
                raise HTTPException(
                    status_code=501, 
                    detail="Google authentication is not configured on the server"
                )
            
            # Verify the Google token
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
            
            # Check if user exists
            existing_user = await self.users_collection.find_one({"email": email})
            
            if existing_user:
                # Update user info and mark as Google authenticated
                await self.users_collection.update_one(
                    {"email": email},
                    {
                        "$set": {
                            "google_id": google_user_id,
                            "google_auth": True,
                            "is_verified": True,
                            "updated_at": datetime.utcnow(),
                            "last_login": datetime.utcnow()
                        }
                    }
                )
                user = await self.users_collection.find_one({"email": email})
            else:
                # Create new user
                new_user = {
                    "firstName": first_name or "Google",
                    "lastName": last_name or "User",
                    "email": email,
                    "google_id": google_user_id,
                    "google_auth": True,
                    "is_verified": True,
                    "is_admin": False,
                    "country": "Not specified",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "last_login": datetime.utcnow()
                }
                
                result = await self.users_collection.insert_one(new_user)
                user = await self.users_collection.find_one({"_id": result.inserted_id})

            # Generate JWT token
            access_token = create_access_token(data={"sub": user["email"]})
            
            # Convert ObjectId for response
            user = convert_objectid(user)
            
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
    
    async def verify_email(self, verification: OTPVerification):
        """Verify user email with OTP"""
        try:
            # Find valid OTP
            otp_doc = await self.otp_collection.find_one({
                "email": verification.email,
                "otp": verification.otp,
                "type": "email_verification",
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not otp_doc:
                raise HTTPException(status_code=400, detail="Invalid or expired verification code")
            
            # Update user as verified
            result = await self.users_collection.update_one(
                {"email": verification.email},
                {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete used OTP
            await self.otp_collection.delete_one({"_id": otp_doc["_id"]})
            
            logger.info(f"Email verified successfully for {verification.email}")
            return {"success": True, "message": "Email verified successfully"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
    
    async def forgot_password(self, email: str):
        """Send password reset OTP"""
        try:
            # Check if user exists
            user = await self.users_collection.find_one({"email": email})
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
            if not user:
                # Don't reveal if email exists or not for security
                return {"success": True, "message": "If the email exists, a reset code has been sent"}
            
            # Clean up existing OTPs
<<<<<<< HEAD
            await collections["otp_codes"].delete_many({
=======
            await self.otp_collection.delete_many({
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
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
<<<<<<< HEAD
            await collections["otp_codes"].insert_one(otp_doc)
            
            # Send password reset email
            await email_service.send_password_reset_email(
                email, 
                user["firstName"], 
                otp
            )
=======
            await self.otp_collection.insert_one(otp_doc)
            
            # Send password reset email
            await self._send_password_reset_email(email, user['firstName'], otp)
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
            
            return {"success": True, "message": "Password reset code sent to your email"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")
    
<<<<<<< HEAD
    async def reset_password(self, email: str, otp: str, new_password: str) -> Dict[str, Any]:
        """Reset user password with OTP"""
        try:
            collections = self._get_collections()
            
            # Find valid OTP
            otp_doc = await collections["otp_codes"].find_one({
                "email": email,
                "otp": otp,
=======
    async def reset_password(self, reset_data: PasswordReset):
        """Reset user password with OTP"""
        try:
            # Find valid OTP
            otp_doc = await self.otp_collection.find_one({
                "email": reset_data.email,
                "otp": reset_data.otp,
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
                "type": "password_reset",
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not otp_doc:
                raise HTTPException(status_code=400, detail="Invalid or expired reset code")
            
            # Hash new password
<<<<<<< HEAD
            hashed_password = hash_password(new_password)
            
            # Update user password
            result = await collections["users"].update_one(
                {"email": email},
=======
            hashed_password = hash_password(reset_data.newPassword)
            
            # Update user password
            result = await self.users_collection.update_one(
                {"email": reset_data.email},
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
                {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete used OTP
<<<<<<< HEAD
            await collections["otp_codes"].delete_one({"_id": otp_doc["_id"]})
            
            logger.info(f"Password reset successfully for {email}")
=======
            await self.otp_collection.delete_one({"_id": otp_doc["_id"]})
            
            logger.info(f"Password reset successfully for {reset_data.email}")
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
            return {"success": True, "message": "Password reset successfully"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")
<<<<<<< HEAD

# Global auth service instance
auth_service = AuthService()
=======
    
    async def _send_verification_otp(self, email: str, first_name: str) -> bool:
        """Send verification OTP email"""
        # Clean up existing OTPs for this email
        await self.otp_collection.delete_many({
            "email": email,
            "type": "email_verification"
        })
        
        # Generate and save OTP
        otp = generate_otp()
        otp_doc = {
            "email": email,
            "otp": otp,
            "type": "email_verification",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        await self.otp_collection.insert_one(otp_doc)
        
        # Enhanced email template
        email_body = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 20px;">
            <div style="background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 40px; color: white;">🚀</span>
                    </div>
                    <h1 style="color: #333; margin: 0; font-size: 28px; font-weight: bold;">Welcome to AI Policy Tracker!</h1>
                </div>
                
                <p style="color: #555; font-size: 16px; line-height: 1.6;">Hello <strong>{first_name}</strong>,</p>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">Thank you for joining our AI Policy community! To complete your registration, please verify your email address.</p>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 15px; margin: 30px 0;">
                    <p style="color: white; margin: 0 0 15px 0; font-size: 18px; font-weight: bold;">Your Verification Code</p>
                    <h1 style="color: white; font-size: 48px; margin: 0; letter-spacing: 8px; font-family: 'Courier New', monospace; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{otp}</h1>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px; padding: 15px; margin: 20px 0;">
                    <p style="color: #856404; margin: 0; font-size: 14px; text-align: center;"><strong>⏰ This code expires in 10 minutes.</strong></p>
                </div>
                
                <p style="color: #555; font-size: 14px; line-height: 1.6;">If you didn't create an account with us, please ignore this email.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <div style="text-align: center;">
                    <p style="color: #888; font-size: 14px; margin: 0;">Best regards,</p>
                    <p style="color: #667eea; font-size: 16px; font-weight: bold; margin: 5px 0 0 0;">AI Policy Tracker Team</p>
                </div>
            </div>
        </div>
        """
        
        return await send_email(email, "🚀 Welcome! Verify Your Email - AI Policy Tracker", email_body)
    
    async def _send_password_reset_email(self, email: str, first_name: str, otp: str) -> bool:
        """Send password reset email"""
        email_body = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 20px; border-radius: 20px;">
            <div style="background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 40px; color: white;">🔐</span>
                    </div>
                    <h1 style="color: #333; margin: 0; font-size: 28px; font-weight: bold;">Password Reset Request</h1>
                </div>
                
                <p style="color: #555; font-size: 16px; line-height: 1.6;">Hello <strong>{first_name}</strong>,</p>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">You requested to reset your password for your AI Policy Tracker account.</p>
                
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 30px; text-align: center; border-radius: 15px; margin: 30px 0;">
                    <p style="color: white; margin: 0 0 15px 0; font-size: 18px; font-weight: bold;">Your Reset Code</p>
                    <h1 style="color: white; font-size: 48px; margin: 0; letter-spacing: 8px; font-family: 'Courier New', monospace; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{otp}</h1>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px; padding: 15px; margin: 20px 0;">
                    <p style="color: #856404; margin: 0; font-size: 14px; text-align: center;"><strong>⏰ This code expires in 10 minutes.</strong></p>
                </div>
                
                <p style="color: #555; font-size: 14px; line-height: 1.6;">If you didn't request this reset, please ignore this email and your password will remain unchanged.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <div style="text-align: center;">
                    <p style="color: #888; font-size: 14px; margin: 0;">Best regards,</p>
                    <p style="color: #ff6b6b; font-size: 16px; font-weight: bold; margin: 5px 0 0 0;">AI Policy Tracker Team</p>
                </div>
            </div>
        </div>
        """
        
        return await send_email(email, "🔐 Password Reset Code - AI Policy Tracker", email_body)

# Global auth service instance - will be initialized lazily
auth_service = None

def get_auth_service():
    """Get or create auth service instance"""
    global auth_service
    if auth_service is None:
        auth_service = AuthService()
    return auth_service
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
