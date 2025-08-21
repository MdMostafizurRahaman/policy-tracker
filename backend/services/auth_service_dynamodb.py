"""
Authentication service for user management with DynamoDB.
"""
import bcrypt
import jwt
import os
import random
import string
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config.dynamodb import get_dynamodb
from config.settings import settings
from models.user_dynamodb import User
from models.user import UserRegistration, UserLogin, GoogleAuthRequest, OTPVerification, PasswordReset, AdminLogin, UserResponse
from services.email_service import email_service
from utils.helpers import generate_otp
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.settings = settings
        
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    async def register_user(self, registration_data: UserRegistration) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = await User.find_by_email(registration_data.email)
            if existing_user:
                return {"status": "error", "message": "User with this email already exists"}
            
            # Combine firstName and lastName to create full_name
            full_name = f"{registration_data.firstName} {registration_data.lastName}".strip()
            
            # Create new user
            user = await User.create_user(
                email=registration_data.email,
                password=registration_data.password,
                name=full_name,
                firstName=registration_data.firstName,
                lastName=registration_data.lastName,
                country=registration_data.country
            )
            
            if not user:
                return {"status": "error", "message": "Failed to create user"}
            
            # Generate OTP for email verification
            otp = generate_otp()
            otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            
            # Update user with OTP
            await user.update({
                'email_verification_otp': otp,
                'otp_expiry': otp_expiry.isoformat(),
                'is_email_verified': False
            })
            
            # Send verification email using email service
            user_name = f"{registration_data.firstName} {registration_data.lastName}".strip()
            email_sent = await email_service.send_verification_email(
                registration_data.email,
                registration_data.firstName,
                otp
            )
            
            # Create access token
            access_token = self.create_access_token(
                data={"sub": user.user_id, "email": user.email}
            )
            
            response = {
                "status": "success",
                "message": "User registered successfully. Please verify your email.",
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "firstName": registration_data.firstName,
                    "lastName": registration_data.lastName,
                    "country": registration_data.country,
                    "is_email_verified": user.is_email_verified
                },
                "access_token": access_token,
                "token_type": "bearer",
                "email_sent": email_sent
            }
            
            # Include OTP for development if email failed to send
            if not email_sent:
                response["otp_for_dev"] = otp
                logger.warning(f"📧 Email failed to send to {registration_data.email}, providing OTP for development: {otp}")
                print(f"🔑 DEVELOPMENT OTP for {registration_data.email}: {otp}")
            elif os.getenv("ENVIRONMENT", "production").lower() == "development":
                # Include OTP in development environment even if email was sent
                response["otp_for_dev"] = otp
                logger.info(f"📧 Email sent successfully to {registration_data.email}, also providing OTP for development: {otp}")
                print(f"🔑 DEVELOPMENT OTP for {registration_data.email}: {otp}")
            
            return response
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return {"status": "error", "message": "Registration failed"}
    
    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            # Find user by email
            user = await User.find_by_email(login_data.email)
            if not user:
                return {"status": "error", "message": "Invalid email or password"}
            
            # Verify password
            if not user.verify_password(login_data.password):
                return {"status": "error", "message": "Invalid email or password"}
            
            # Check if user is active
            if not user.is_active:
                return {"status": "error", "message": "Account is disabled"}
            
            # Update last login
            await user.update({
                'last_login': datetime.utcnow().isoformat(),
                'login_count': user.login_count + 1
            })
            
            # Create access token
            access_token = self.create_access_token(
                data={"sub": user.user_id, "email": user.email}
            )
            
            return {
                "status": "success",
                "message": "Login successful",
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.name,
                    "firstName": user.firstName,
                    "lastName": user.lastName,
                    "country": user.country,
                    "is_email_verified": user.is_email_verified,
                    "role": user.role
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {"status": "error", "message": "Login failed"}
    
    async def google_auth(self, google_data: GoogleAuthRequest) -> Dict[str, Any]:
        """Authenticate user with Google OAuth"""
        try:
            # Verify Google token
            idinfo = id_token.verify_oauth2_token(
                google_data.token, 
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return {"status": "error", "message": "Invalid token issuer"}
            
            google_id = idinfo['sub']
            email = idinfo['email']
            name = idinfo.get('name', '')
            
            # Check if user exists by Google ID
            user = await User.find_by_google_id(google_id)
            
            if user:
                # User exists, update login info
                await user.update({
                    'last_login': datetime.utcnow().isoformat(),
                    'login_count': user.login_count + 1
                })
            else:
                # Check if user exists by email
                user = await User.find_by_email(email)
                if user:
                    # Link Google account to existing user
                    await user.update({'google_id': google_id})
                else:
                    # Create new user
                    user = await User.create_user(
                        email=email,
                        full_name=name,
                        google_id=google_id,
                        is_email_verified=True  # Google emails are pre-verified
                    )
                    
                    if not user:
                        return {"status": "error", "message": "Failed to create user"}
            
            # Create access token
            access_token = self.create_access_token(
                data={"sub": user.user_id, "email": user.email}
            )
            
            return {
                "status": "success",
                "message": "Google authentication successful",
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_email_verified": user.is_email_verified,
                    "role": user.role
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except ValueError as e:
            logger.error(f"Google auth error: {str(e)}")
            return {"status": "error", "message": "Invalid Google token"}
        except Exception as e:
            logger.error(f"Google auth error: {str(e)}")
            return {"status": "error", "message": "Google authentication failed"}
    
    async def verify_otp(self, otp_data: OTPVerification) -> Dict[str, Any]:
        """Verify email OTP"""
        try:
            # Find user by email
            user = await User.find_by_email(otp_data.email)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Check if OTP is valid and not expired
            if user.email_verification_otp != otp_data.otp:
                return {"status": "error", "message": "Invalid OTP"}
            
            if user.otp_expiry and datetime.fromisoformat(user.otp_expiry) < datetime.utcnow():
                return {"status": "error", "message": "OTP has expired"}
            
            # Verify email
            await user.update({
                'is_email_verified': True,
                'email_verification_otp': None,
                'otp_expiry': None
            })
            
            return {
                "status": "success",
                "message": "Email verified successfully"
            }
            
        except Exception as e:
            logger.error(f"OTP verification error: {str(e)}")
            return {"status": "error", "message": "OTP verification failed"}
    
    async def verify_email(self, verification: OTPVerification) -> Dict[str, Any]:
        """Verify user email with OTP (alias for verify_otp)"""
        return await self.verify_otp(verification)
    
    async def resend_otp(self, email: str) -> Dict[str, Any]:
        """Resend email verification OTP"""
        try:
            # Find user by email
            user = await User.find_by_email(email)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            if user.is_email_verified:
                return {"status": "error", "message": "Email is already verified"}
            
            # Generate new OTP
            otp = generate_otp()
            otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            
            # Update user with new OTP
            await user.update({
                'email_verification_otp': otp,
                'otp_expiry': otp_expiry.isoformat()
            })
            
            # Send verification email using email service
            email_sent = await email_service.send_verification_email(
                email,
                user.firstName or "User",
                otp
            )
            
            response = {
                "status": "success",
                "message": "OTP sent successfully",
                "email_sent": email_sent
            }
            
            # Include OTP for development if email failed to send
            if not email_sent:
                response["otp_for_dev"] = otp
                logger.warning(f"📧 Resend OTP email failed to send to {email}, providing OTP for development: {otp}")
                print(f"🔑 DEVELOPMENT OTP for {email}: {otp}")
            
            return response
            
        except Exception as e:
            logger.error(f"Resend OTP error: {str(e)}")
            return {"status": "error", "message": "Failed to resend OTP"}
    
    async def forgot_password(self, email: str) -> Dict[str, Any]:
        """Send password reset OTP"""
        try:
            # Find user by email
            user = await User.find_by_email(email)
            if not user:
                # Return success even if user doesn't exist for security
                return {"status": "success", "message": "Password reset email sent if account exists"}
            
            # Generate OTP for password reset
            otp = generate_otp()
            otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            
            # Update user with reset OTP
            await user.update({
                'password_reset_otp': otp,
                'password_reset_otp_expiry': otp_expiry.isoformat()
            })
            
            # Send reset email using email service
            email_sent = await email_service.send_password_reset_email(
                email,
                user.firstName or "User",
                otp
            )
            
            response = {
                "status": "success",
                "message": "Password reset email sent if account exists",
                "email_sent": email_sent
            }
            
            # Include OTP for development if email failed to send
            if not email_sent:
                response["otp_for_dev"] = otp
                logger.warning(f"📧 Password reset email failed to send to {email}, providing OTP for development: {otp}")
                print(f"🔑 DEVELOPMENT PASSWORD RESET OTP for {email}: {otp}")
            
            return response
            
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            return {"status": "error", "message": "Failed to process password reset"}
    
    async def reset_password(self, reset_data: PasswordReset) -> Dict[str, Any]:
        """Reset user password with OTP"""
        try:
            # Find user by email
            user = await User.find_by_email(reset_data.email)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Check if OTP is valid and not expired
            if user.password_reset_otp != reset_data.otp:
                return {"status": "error", "message": "Invalid reset code"}
            
            if (user.password_reset_otp_expiry and 
                datetime.fromisoformat(user.password_reset_otp_expiry) < datetime.utcnow()):
                return {"status": "error", "message": "Reset code has expired"}
            
            # Check if new password matches confirmation
            if reset_data.newPassword != reset_data.confirmPassword:
                return {"status": "error", "message": "Passwords do not match"}
            
            # Update password and clear reset OTP
            new_password_hash = self.hash_password(reset_data.newPassword)
            await user.update({
                'password': new_password_hash,
                'password_reset_otp': None,
                'password_reset_otp_expiry': None
            })
            
            return {
                "status": "success",
                "message": "Password reset successfully"
            }
            
        except Exception as e:
            logger.error(f"Reset password error: {str(e)}")
            return {"status": "error", "message": "Password reset failed"}
    
    async def admin_login(self, login_data: AdminLogin) -> Dict[str, Any]:
        """Admin login with enhanced security"""
        try:
            # Check super admin credentials
            if (login_data.email == settings.SUPER_ADMIN_EMAIL and
                login_data.password == settings.SUPER_ADMIN_PASSWORD):
                
                # Find or create super admin user
                admin_user = await User.find_by_email(settings.SUPER_ADMIN_EMAIL)
                
                if not admin_user:
                    # Create super admin user
                    admin_user = await User.create_user(
                        email=settings.SUPER_ADMIN_EMAIL,
                        password=settings.SUPER_ADMIN_PASSWORD,
                        name="Super Admin",
                        role="super_admin"
                    )
                    
                    if not admin_user:
                        return {"status": "error", "message": "Failed to create admin user"}
                else:
                    # Update last login for existing admin
                    current_login_count = getattr(admin_user, 'login_count', 0)
                    await admin_user.update({
                        'last_login': datetime.utcnow().isoformat(),
                        'login_count': current_login_count + 1
                    })
                
                # Create admin access token
                access_token = self.create_access_token(
                    data={"sub": admin_user.user_id, "email": admin_user.email, "role": "super_admin"}
                )
                
                return {
                    "status": "success",
                    "message": "Admin login successful",
                    "user": {
                        "user_id": admin_user.user_id,
                        "email": admin_user.email,
                        "name": admin_user.name,
                        "role": admin_user.role
                    },
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            
            # Regular admin login
            user = await User.find_by_email(login_data.email)
            if not user or user.role not in ['admin', 'super_admin']:
                return {"status": "error", "message": "Invalid admin credentials"}
            
            if not user.verify_password(login_data.password):
                return {"status": "error", "message": "Invalid admin credentials"}
            
            # Update last login
            await user.update({
                'last_login': datetime.utcnow().isoformat(),
                'login_count': user.login_count + 1
            })
            
            # Create access token
            access_token = self.create_access_token(
                data={"sub": user.user_id, "email": user.email, "role": user.role}
            )
            
            return {
                "status": "success",
                "message": "Admin login successful",
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Admin login error: {str(e)}")
            return {"status": "error", "message": "Admin login failed"}
    
    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from token"""
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            user = await User.find_by_id(user_id)
            
            if not user or not user.is_active:
                return None
            
            return {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_email_verified": user.is_email_verified
            }
            
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return None
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        try:
            user = await User.find_by_id(user_id)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Verify current password
            if user.password_hash and not user.verify_password(current_password):
                return {"status": "error", "message": "Current password is incorrect"}
            
            # Update password
            new_password_hash = self.hash_password(new_password)
            await user.update({'password': new_password_hash})
            
            return {
                "status": "success",
                "message": "Password changed successfully"
            }
            
        except Exception as e:
            logger.error(f"Change password error: {str(e)}")
            return {"status": "error", "message": "Failed to change password"}
    
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            user = await User.find_by_id(user_id)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Update allowed fields
            allowed_fields = ['full_name', 'phone', 'organization', 'profile_picture']
            update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
            
            if update_data:
                await user.update(update_data)
            
            return {
                "status": "success",
                "message": "Profile updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Update profile error: {str(e)}")
            return {"status": "error", "message": "Failed to update profile"}

    async def get_latest_otp(self, email: str) -> Dict[str, Any]:
        """Get latest OTP for development (should only be used in development)"""
        try:
            user = await User.find_by_email(email)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Return both email verification OTP and password reset OTP
            response = {
                "status": "success",
                "email": email,
                "verification_otp": user.email_verification_otp,
                "password_reset_otp": getattr(user, 'password_reset_otp', None)
            }
            
            # Also log the OTP for easy access during development
            if user.email_verification_otp:
                logger.info(f"🔑 EMAIL VERIFICATION OTP for {email}: {user.email_verification_otp}")
                print(f"🔑 EMAIL VERIFICATION OTP for {email}: {user.email_verification_otp}")
            
            if hasattr(user, 'password_reset_otp') and user.password_reset_otp:
                logger.info(f"🔑 PASSWORD RESET OTP for {email}: {user.password_reset_otp}")
                print(f"🔑 PASSWORD RESET OTP for {email}: {user.password_reset_otp}")
            
            return response
            
        except Exception as e:
            logger.error(f"Get latest OTP error: {str(e)}")
            return {"status": "error", "message": "Failed to get OTP"}

# Create a singleton instance
auth_service = AuthService()
