"""
Authentication service for user management with DynamoDB.
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
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config.dynamodb import get_dynamodb
from config.settings import settings
from models.user_dynamodb import User
from models.user import UserRegistration, UserLogin, GoogleAuthRequest, OTPVerification, PasswordReset, AdminLogin, UserResponse
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
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send an email with optional HTML formatting"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Policy Tracker <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                # Create HTML and plain text versions
                html_part = MIMEText(body, 'html')
                msg.attach(html_part)
            else:
                # Plain text email
                text_part = MIMEText(body, 'plain')
                msg.attach(text_part)
            
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def create_verification_email_html(self, otp: str, user_name: str = "User") -> str:
        """Create a beautiful HTML email for email verification"""
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification - Policy Tracker</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 28px;
                    margin-bottom: 10px;
                    font-weight: 700;
                }}
                .header p {{
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .otp-section {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-label {{
                    color: white;
                    font-size: 16px;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}
                .otp-code {{
                    background: white;
                    color: #333;
                    font-size: 32px;
                    font-weight: bold;
                    padding: 15px 30px;
                    border-radius: 8px;
                    letter-spacing: 8px;
                    display: inline-block;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .instructions {{
                    background: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 0 8px 8px 0;
                }}
                .instructions h3 {{
                    color: #667eea;
                    margin-bottom: 10px;
                }}
                .warning {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                }}
                .footer p {{
                    color: #6c757d;
                    font-size: 14px;
                    margin-bottom: 10px;
                }}
                .social-links {{
                    margin-top: 20px;
                }}
                .social-links a {{
                    display: inline-block;
                    margin: 0 10px;
                    padding: 10px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    line-height: 20px;
                }}
                @media (max-width: 600px) {{
                    .container {{
                        margin: 10px;
                        border-radius: 0;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                    .otp-code {{
                        font-size: 24px;
                        letter-spacing: 4px;
                        padding: 12px 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Policy Tracker</h1>
                    <p>Global Policy Database & Analysis Platform</p>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        Hello {user_name}! 👋
                    </div>
                    
                    <p>Welcome to Policy Tracker! We're excited to have you join our global community of policy researchers and analysts.</p>
                    
                    <div class="otp-section">
                        <div class="otp-label">Your Verification Code</div>
                        <div class="otp-code">{otp}</div>
                    </div>
                    
                    <div class="instructions">
                        <h3>📋 How to verify your email:</h3>
                        <ol>
                            <li>Copy the 6-digit verification code above</li>
                            <li>Return to the Policy Tracker website</li>
                            <li>Enter the code in the verification field</li>
                            <li>Click "Verify Email" to complete your registration</li>
                        </ol>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong> This verification code will expire in 10 minutes for security reasons. If you didn't request this verification, please ignore this email.
                    </div>
                    
                    <p>Once verified, you'll be able to:</p>
                    <ul style="margin: 15px 0; padding-left: 20px;">
                        <li>✅ Submit and track policy proposals</li>
                        <li>🌍 Explore policies from around the world</li>
                        <li>🤖 Use our AI-powered policy analysis tools</li>
                        <li>💬 Chat with our policy assistant</li>
                        <li>📊 Access detailed policy statistics</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>Thank you for choosing Policy Tracker!</p>
                    <p>If you have any questions, please contact our support team.</p>
                    <p style="margin-top: 20px;">
                        <strong>Policy Tracker Team</strong><br>
                        Global Policy Database & Analysis Platform
                    </p>
                    
                    <div class="social-links">
                        <a href="#" title="Website">🌐</a>
                        <a href="#" title="Support">📧</a>
                        <a href="#" title="Documentation">📚</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template
    
    def create_password_reset_email_html(self, otp: str, user_name: str = "User") -> str:
        """Create a beautiful HTML email for password reset"""
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - Policy Tracker</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                    color: white;
                    padding: 40px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 28px;
                    margin-bottom: 10px;
                    font-weight: 700;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .otp-section {{
                    background: linear-gradient(135deg, #ffa726 0%, #ff7043 100%);
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .otp-label {{
                    color: white;
                    font-size: 16px;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}
                .otp-code {{
                    background: white;
                    color: #333;
                    font-size: 32px;
                    font-weight: bold;
                    padding: 15px 30px;
                    border-radius: 8px;
                    letter-spacing: 8px;
                    display: inline-block;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .security-notice {{
                    background: #ffebee;
                    border: 1px solid #ffcdd2;
                    color: #c62828;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset</h1>
                    <p>Policy Tracker Security</p>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        Hello {user_name}! 🔑
                    </div>
                    
                    <p>We received a request to reset your password for your Policy Tracker account.</p>
                    
                    <div class="otp-section">
                        <div class="otp-label">Your Reset Code</div>
                        <div class="otp-code">{otp}</div>
                    </div>
                    
                    <div class="security-notice">
                        <strong>🔒 Security Notice:</strong> This reset code will expire in 10 minutes. If you didn't request this password reset, please ignore this email and your password will remain unchanged.
                    </div>
                </div>
                
                <div class="footer">
                    <p>Stay secure with Policy Tracker!</p>
                    <p><strong>Policy Tracker Security Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template
    
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
            otp = self.generate_otp()
            otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            
            # Update user with OTP
            await user.update({
                'email_verification_otp': otp,
                'otp_expiry': otp_expiry.isoformat(),
                'is_email_verified': False
            })
            
            # Send verification email
            user_name = f"{registration_data.firstName} {registration_data.lastName}".strip()
            email_html = self.create_verification_email_html(otp, user_name)
            email_sent = self.send_email(
                registration_data.email,
                "🛡️ Verify Your Email - Policy Tracker",
                email_html,
                is_html=True
            )
            
            # Create access token
            access_token = self.create_access_token(
                data={"sub": user.user_id, "email": user.email}
            )
            
            return {
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
            otp = self.generate_otp()
            otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            
            # Update user with new OTP
            await user.update({
                'email_verification_otp': otp,
                'otp_expiry': otp_expiry.isoformat()
            })
            
            # Send verification email
            email_body = f"Your verification code is: {otp}. This code will expire in 10 minutes."
            email_sent = self.send_email(
                email,
                "Email Verification - Policy Tracker",
                email_body
            )
            
            return {
                "status": "success",
                "message": "OTP sent successfully",
                "email_sent": email_sent
            }
            
        except Exception as e:
            logger.error(f"Resend OTP error: {str(e)}")
            return {"status": "error", "message": "Failed to resend OTP"}
    
    async def forgot_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email"""
        try:
            # Find user by email
            user = await User.find_by_email(email)
            if not user:
                # Return success even if user doesn't exist for security
                return {"status": "success", "message": "Password reset email sent if account exists"}
            
            # Generate reset token
            reset_token = self.create_access_token(
                data={"sub": user.user_id, "type": "password_reset"},
                expires_delta=timedelta(hours=1)
            )
            
            # Update user with reset token
            await user.update({
                'password_reset_token': reset_token,
                'password_reset_expires': (datetime.utcnow() + timedelta(hours=1)).isoformat()
            })
            
            # Send reset email with HTML template
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            email_body_html = self.create_password_reset_email_html(user.email, reset_url)
            email_sent = self.send_email(
                email,
                "Password Reset - Policy Tracker",
                email_body_html,
                is_html=True
            )
            
            return {
                "status": "success",
                "message": "Password reset email sent if account exists",
                "email_sent": email_sent
            }
            
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            return {"status": "error", "message": "Failed to process password reset"}
    
    async def reset_password(self, reset_data: PasswordReset) -> Dict[str, Any]:
        """Reset user password with token"""
        try:
            # Verify reset token
            payload = self.verify_token(reset_data.token)
            if not payload or payload.get('type') != 'password_reset':
                return {"status": "error", "message": "Invalid or expired reset token"}
            
            user_id = payload.get('sub')
            user = await User.find_by_id(user_id)
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Check if reset token is still valid
            if (user.password_reset_expires and 
                datetime.fromisoformat(user.password_reset_expires) < datetime.utcnow()):
                return {"status": "error", "message": "Reset token has expired"}
            
            # Update password
            new_password_hash = self.hash_password(reset_data.new_password)
            await user.update({
                'password': new_password_hash,
                'password_reset_token': None,
                'password_reset_expires': None
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

# Create a singleton instance
auth_service = AuthService()
