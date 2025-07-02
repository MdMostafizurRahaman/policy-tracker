"""
Authentication service for user management.
"""
import bcrypt
import jwt
import os
import random
import string
import smtplib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson import ObjectId
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config.database import database
from config.settings import get_settings
from config.constants import SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM
from models.user import UserRegistration, UserLogin, GoogleAuthRequest, OTPVerification, PasswordReset, AdminLogin, UserResponse
from utils.helpers import convert_objectid
import logging

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self._db = None
        self._users_collection = None
        self._otp_collection = None
        self.settings = get_settings()

    @property
    def db(self):
        if self._db is None:
            self._db = database.db
        return self._db

    @property
    def users_collection(self):
        if self._users_collection is None:
            self._users_collection = self.db.users
        return self._users_collection

    @property
    def otp_collection(self):
        if self._otp_collection is None:
            self._otp_collection = self.db.otp_codes
        return self._otp_collection

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email with OTP or notifications"""
        try:
            # Extract OTP for logging
            otp_match = re.search(r'\b\d{6}\b', body)
            extracted_otp = otp_match.group() if otp_match else None
            
            # Always log OTP for development
            if extracted_otp:
                logger.info(f"🔑 OTP for {to_email}: {extracted_otp}")
                print(f"🔑 DEVELOPMENT OTP for {to_email}: {extracted_otp}")
            
            # Check credentials
            if not self.settings.SMTP_USERNAME or not self.settings.SMTP_PASSWORD:
                logger.warning("⚠️ SMTP credentials missing")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
            
            logger.info(f"📧 Sending email to: {to_email}")
            logger.info(f"📧 SMTP Config: {self.settings.SMTP_USERNAME} via {self.settings.SMTP_SERVER}:{self.settings.SMTP_PORT}")
            
            # Create message with proper encoding
            msg = MIMEMultipart('alternative')
            msg['From'] = self.settings.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.set_charset('utf-8')
            
            # Add both HTML and plain text versions
            plain_text = f"Your verification code is: {extracted_otp}" if extracted_otp else "Verification email"
            text_part = MIMEText(plain_text, 'plain', 'utf-8')
            html_part = MIMEText(body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Use proper SMTP connection
            try:
                logger.info(f"🔌 Connecting to {self.settings.smtp_server}:{self.settings.smtp_port}")
                
                # Use SMTP_SSL instead of SMTP + starttls for better compatibility
                if self.settings.smtp_port == 465:
                    server = smtplib.SMTP_SSL(self.settings.smtp_server, self.settings.smtp_port)
                else:
                    server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
                    server.ehlo()
                    logger.info("🔒 Starting TLS...")
                    server.starttls()
                    server.ehlo()
                
                logger.info(f"🔑 Authenticating as: {self.settings.SMTP_USERNAME}")
                server.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                
                logger.info("📤 Sending message...")
                text = msg.as_string()
                server.sendmail(self.settings.from_email, [to_email], text)
                server.quit()
                
                logger.info(f"✅ Email sent successfully to {to_email}")
                print(f"✅ EMAIL ACTUALLY SENT to {to_email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ SMTP Authentication Error: {str(e)}")
                print(f"❌ AUTH FAILED: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except smtplib.SMTPConnectError as e:
                logger.error(f"❌ SMTP Connection Error: {str(e)}")
                print(f"❌ CONNECTION FAILED: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except Exception as e:
                logger.error(f"❌ Email sending error: {str(e)}")
                print(f"❌ EMAIL ERROR: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
        except Exception as e:
            logger.error(f"Email error: {str(e)}")
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp}")
            return False

    async def register_user(self, user_data: UserRegistration) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = await self.users_collection.find_one({"email": user_data.email})
            if existing_user:
                if existing_user.get("is_verified", False):
                    raise Exception("User already exists and is verified")
                else:
                    # User exists but not verified, delete old record
                    await self.users_collection.delete_one({"email": user_data.email})
                    await self.otp_collection.delete_many({"email": user_data.email})

            # Create new user
            hashed_password = self.hash_password(user_data.password)
            user_id = str(ObjectId())
            
            user_doc = {
                "_id": ObjectId(user_id),
                "firstName": user_data.firstName,
                "lastName": user_data.lastName,
                "email": user_data.email,
                "password": hashed_password,
                "country": user_data.country,
                "is_verified": False,
                "is_admin": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.users_collection.insert_one(user_doc)
            
            # Generate and save OTP
            otp = self.generate_otp()
            otp_doc = {
                "email": user_data.email,
                "otp": otp,
                "type": "email_verification",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            }
            
            await self.otp_collection.insert_one(otp_doc)
            
            # Send verification email
            subject = "Verify Your Email - AI Policy Tracker"
            body = f"""
            <h2>Welcome to AI Policy Tracker!</h2>
            <p>Hello {user_data.firstName},</p>
            <p>Thank you for registering. Please verify your email address using the OTP below:</p>
            <h3 style="color: #007bff; font-size: 24px; letter-spacing: 3px;">{otp}</h3>
            <p>This OTP will expire in 10 minutes.</p>
            <p>If you didn't create this account, please ignore this email.</p>
            <p>Best regards,<br>AI Policy Tracker Team</p>
            """
            
            email_sent = await self.send_email(user_data.email, subject, body)
            
            return {
                "message": "User registered successfully. Please check your email for verification code.",
                "user_id": user_id,
                "email_sent": email_sent,
                "otp_for_dev": otp if not email_sent else None
            }
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise Exception(f"Registration failed: {str(e)}")

    async def verify_email(self, verification_data: OTPVerification) -> Dict[str, Any]:
        """Verify user email with OTP"""
        try:
            # Find valid OTP
            otp_doc = await self.otp_collection.find_one({
                "email": verification_data.email,
                "otp": verification_data.otp,
                "type": "email_verification",
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not otp_doc:
                raise Exception("Invalid or expired OTP")
            
            # Update user as verified
            result = await self.users_collection.update_one(
                {"email": verification_data.email},
                {
                    "$set": {
                        "is_verified": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise Exception("User not found")
            
            # Delete used OTP
            await self.otp_collection.delete_many({"email": verification_data.email, "type": "email_verification"})
            
            # Get updated user
            user = await self.users_collection.find_one({"email": verification_data.email})
            if not user:
                raise Exception("User not found after verification")
            
            # Create access token
            token_data = {
                "sub": str(user["_id"]),
                "email": user["email"],
                "is_admin": user.get("is_admin", False)
            }
            access_token = self.create_access_token(
                token_data, 
                timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            
            return {
                "message": "Email verified successfully",
                "access_token": access_token,
                "token_type": "bearer",
                "user": UserResponse(
                    id=str(user["_id"]),
                    firstName=user["firstName"],
                    lastName=user["lastName"],
                    email=user["email"],
                    country=user["country"],
                    is_admin=user.get("is_admin", False),
                    is_verified=True,
                    created_at=user.get("created_at")
                ).dict()
            }
            
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            raise Exception(f"Email verification failed: {str(e)}")

    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """Login user with email and password"""
        try:
            # Find user
            user = await self.users_collection.find_one({"email": login_data.email})
            if not user:
                raise Exception("Invalid email or password")
            
            # Verify password
            if not self.verify_password(login_data.password, user["password"]):
                raise Exception("Invalid email or password")
            
            # Check if email is verified
            if not user.get("is_verified", False):
                raise Exception("Email not verified. Please verify your email first.")
            
            # Create access token
            token_data = {
                "sub": str(user["_id"]),
                "email": user["email"],
                "is_admin": user.get("is_admin", False)
            }
            access_token = self.create_access_token(
                token_data, 
                timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            
            # Update last login
            await self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            return {
                "message": "Login successful",
                "access_token": access_token,
                "token_type": "bearer",
                "user": UserResponse(
                    id=str(user["_id"]),
                    firstName=user["firstName"],
                    lastName=user["lastName"],
                    email=user["email"],
                    country=user["country"],
                    is_admin=user.get("is_admin", False),
                    is_verified=user.get("is_verified", False),
                    created_at=user.get("created_at")
                ).dict()
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise Exception(f"Login failed: {str(e)}")

    async def google_auth(self, google_data: GoogleAuthRequest) -> Dict[str, Any]:
        """Authenticate user with Google OAuth"""
        try:
            # Verify Google token
            if not self.settings.google_client_id:
                raise Exception("Google authentication not configured")
            
            try:
                idinfo = id_token.verify_oauth2_token(
                    google_data.token, 
                    google_requests.Request(), 
                    self.settings.google_client_id
                )
            except ValueError as e:
                raise Exception(f"Invalid Google token: {str(e)}")
            
            email = idinfo.get('email')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            
            if not email:
                raise Exception("Email not provided by Google")
            
            # Check if user exists
            user = await self.users_collection.find_one({"email": email})
            
            if user:
                # Update last login
                await self.users_collection.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "last_login": datetime.utcnow(),
                            "is_verified": True  # Google accounts are pre-verified
                        }
                    }
                )
            else:
                # Create new user
                user_id = str(ObjectId())
                user = {
                    "_id": ObjectId(user_id),
                    "firstName": first_name,
                    "lastName": last_name,
                    "email": email,
                    "password": "",  # No password for Google users
                    "country": "Unknown",  # User can update later
                    "is_verified": True,
                    "is_admin": False,
                    "google_auth": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await self.users_collection.insert_one(user)
            
            # Create access token
            token_data = {
                "sub": str(user["_id"]),
                "email": user["email"],
                "is_admin": user.get("is_admin", False)
            }
            access_token = self.create_access_token(
                token_data, 
                timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            
            return {
                "message": "Google authentication successful",
                "access_token": access_token,
                "token_type": "bearer",
                "user": UserResponse(
                    id=str(user["_id"]),
                    firstName=user["firstName"],
                    lastName=user["lastName"],
                    email=user["email"],
                    country=user["country"],
                    is_admin=user.get("is_admin", False),
                    is_verified=True,
                    created_at=user.get("created_at")
                ).dict()
            }
            
        except Exception as e:
            logger.error(f"Google auth error: {str(e)}")
            raise Exception(f"Google authentication failed: {str(e)}")

    async def forgot_password(self, email: str) -> Dict[str, Any]:
        """Send password reset OTP"""
        try:
            # Check if user exists
            user = await self.users_collection.find_one({"email": email})
            if not user:
                raise Exception("No account found with this email address")
            
            # Generate and save OTP
            otp = self.generate_otp()
            otp_doc = {
                "email": email,
                "otp": otp,
                "type": "password_reset",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            }
            
            # Delete existing password reset OTPs
            await self.otp_collection.delete_many({"email": email, "type": "password_reset"})
            await self.otp_collection.insert_one(otp_doc)
            
            # Send reset email
            subject = "Password Reset - AI Policy Tracker"
            body = f"""
            <h2>Password Reset Request</h2>
            <p>Hello {user['firstName']},</p>
            <p>You requested a password reset. Use the OTP below to reset your password:</p>
            <h3 style="color: #007bff; font-size: 24px; letter-spacing: 3px;">{otp}</h3>
            <p>This OTP will expire in 10 minutes.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
            <p>Best regards,<br>AI Policy Tracker Team</p>
            """
            
            email_sent = await self.send_email(email, subject, body)
            
            return {
                "message": "Password reset OTP sent to your email",
                "email_sent": email_sent,
                "otp_for_dev": otp if not email_sent else None
            }
            
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            raise Exception(f"Password reset request failed: {str(e)}")

    async def reset_password(self, reset_data: PasswordReset) -> Dict[str, Any]:
        """Reset user password with OTP"""
        try:
            # Find valid OTP
            otp_doc = await self.otp_collection.find_one({
                "email": reset_data.email,
                "otp": reset_data.otp,
                "type": "password_reset",
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if not otp_doc:
                raise Exception("Invalid or expired OTP")
            
            # Hash new password
            hashed_password = self.hash_password(reset_data.newPassword)
            
            # Update user password
            result = await self.users_collection.update_one(
                {"email": reset_data.email},
                {
                    "$set": {
                        "password": hashed_password,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise Exception("User not found")
            
            # Delete used OTP
            await self.otp_collection.delete_many({"email": reset_data.email, "type": "password_reset"})
            
            return {"message": "Password reset successfully"}
            
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            raise Exception(f"Password reset failed: {str(e)}")

    async def admin_login(self, login_data: AdminLogin) -> Dict[str, Any]:
        """Admin login with special privileges"""
        try:
            # Check super admin credentials
            if (login_data.email == SUPER_ADMIN_EMAIL and 
                login_data.password == SUPER_ADMIN_PASSWORD):
                
                # Create or update super admin user
                admin_user = await self.users_collection.find_one({"email": SUPER_ADMIN_EMAIL})
                
                if not admin_user:
                    # Create super admin
                    user_id = str(ObjectId())
                    admin_user = {
                        "_id": ObjectId(user_id),
                        "firstName": "Super",
                        "lastName": "Admin",
                        "email": SUPER_ADMIN_EMAIL,
                        "password": self.hash_password(SUPER_ADMIN_PASSWORD),
                        "country": "Global",
                        "is_verified": True,
                        "is_admin": True,
                        "is_super_admin": True,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    await self.users_collection.insert_one(admin_user)
                else:
                    # Update super admin status
                    await self.users_collection.update_one(
                        {"email": SUPER_ADMIN_EMAIL},
                        {
                            "$set": {
                                "is_admin": True,
                                "is_super_admin": True,
                                "last_login": datetime.utcnow()
                            }
                        }
                    )
                
                # Create admin token
                token_data = {
                    "sub": str(admin_user["_id"]),
                    "email": SUPER_ADMIN_EMAIL,
                    "is_admin": True,
                    "is_super_admin": True
                }
                access_token = self.create_access_token(
                    token_data, 
                    timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                )
                
                return {
                    "message": "Admin login successful",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "id": str(admin_user["_id"]),
                        "firstName": "Super",
                        "lastName": "Admin",
                        "email": SUPER_ADMIN_EMAIL,
                        "country": "Global",
                        "is_admin": True,
                        "is_super_admin": True,
                        "is_verified": True
                    }
                }
            else:
                # Check regular admin users
                user = await self.users_collection.find_one({
                    "email": login_data.email,
                    "is_admin": True
                })
                
                if not user or not self.verify_password(login_data.password, user["password"]):
                    raise Exception("Invalid admin credentials")
                
                # Create admin token
                token_data = {
                    "sub": str(user["_id"]),
                    "email": user["email"],
                    "is_admin": True
                }
                access_token = self.create_access_token(
                    token_data, 
                    timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                )
                
                # Update last login
                await self.users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
                
                return {
                    "message": "Admin login successful",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": UserResponse(
                        id=str(user["_id"]),
                        firstName=user["firstName"],
                        lastName=user["lastName"],
                        email=user["email"],
                        country=user["country"],
                        is_admin=True,
                        is_verified=user.get("is_verified", False),
                        created_at=user.get("created_at")
                    ).dict()
                }
            
        except Exception as e:
            logger.error(f"Admin login error: {str(e)}")
            raise Exception(f"Admin login failed: {str(e)}")

    async def get_latest_otp(self, email: str) -> Dict[str, Any]:
        """Get latest OTP for development purposes"""
        try:
            otp_doc = await self.otp_collection.find_one(
                {"email": email},
                sort=[("created_at", -1)]
            )
            
            if otp_doc:
                return {
                    "email": email,
                    "otp": otp_doc["otp"],
                    "type": otp_doc["type"],
                    "created_at": otp_doc["created_at"],
                    "expires_at": otp_doc["expires_at"],
                    "is_expired": otp_doc["expires_at"] < datetime.utcnow()
                }
            else:
                return {"message": "No OTP found for this email"}
                
        except Exception as e:
            logger.error(f"Get OTP error: {str(e)}")
            raise Exception(f"Failed to get OTP: {str(e)}")

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            if not user_id:
                raise Exception("Invalid token")
            
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise Exception("User not found")
            
            return {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "is_admin": user.get("is_admin", False),
                "is_verified": user.get("is_verified", False)
            }
            
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.JWTError:
            raise Exception("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise Exception(f"Token verification failed: {str(e)}")


# Create singleton instance
auth_service = AuthService()
