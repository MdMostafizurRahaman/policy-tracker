"""
Email service for sending notifications and OTPs.
"""
import logging
import smtplib
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings
from config.database import get_users_collection
from utils.helpers import generate_otp

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email with proper SMTP handling"""
        try:
            # Extract OTP for logging
            otp_match = re.search(r'\b\d{6}\b', body)
            extracted_otp = otp_match.group() if otp_match else None
            
            # Always log OTP for development
            if extracted_otp:
                logger.info(f"🔑 OTP for {to_email}: {extracted_otp}")
                print(f"🔑 DEVELOPMENT OTP for {to_email}: {extracted_otp}")
            
            # Check credentials
            if not self.smtp_username or not self.smtp_password:
                logger.warning("⚠️ SMTP credentials missing")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
            
            logger.info(f"📧 Sending email to: {to_email}")
            logger.info(f"📧 SMTP Config: {self.smtp_username} via {self.smtp_server}:{self.smtp_port}")
            
            # Create message with proper encoding
            msg = MIMEMultipart('alternative')
            msg['From'] = f"AI Policy Tracker <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.set_charset('utf-8')
            
            # Add both HTML and plain text versions
            plain_text = f"Your verification code is: {extracted_otp}" if extracted_otp else "Verification email"
            text_part = MIMEText(plain_text, 'plain', 'utf-8')
            html_part = MIMEText(body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Use proper SMTP connection with context manager
            try:
                # Create SMTP connection
                logger.info(f"🔌 Connecting to {self.smtp_server}:{self.smtp_port}")
                
                # Use SMTP_SSL for port 465, SMTP + STARTTLS for port 587
                if self.smtp_port == 465:
                    logger.info("🔒 Using SMTP_SSL connection...")
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                        server.ehlo()
                        logger.info(f"🔑 Authenticating as: {self.smtp_username}")
                        server.login(self.smtp_username, self.smtp_password)
                        
                        logger.info("📤 Sending message...")
                        text = msg.as_string()
                        server.sendmail(self.from_email, [to_email], text)
                        
                        logger.info(f"✅ Email sent successfully to {to_email}")
                        print(f"✅ EMAIL SENT SUCCESSFULLY to {to_email}")
                        if extracted_otp:
                            print(f"🔑 OTP delivered via email: {extracted_otp}")
                        return True
                else:
                    logger.info("🔒 Using SMTP + STARTTLS connection...")
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.ehlo()
                        logger.info("🔒 Starting TLS...")
                        server.starttls()
                        server.ehlo()
                        
                        logger.info(f"🔑 Authenticating as: {self.smtp_username}")
                        server.login(self.smtp_username, self.smtp_password)
                        
                        logger.info("📤 Sending message...")
                        text = msg.as_string()
                        server.sendmail(self.from_email, [to_email], text)
                        
                        logger.info(f"✅ Email sent successfully to {to_email}")
                        print(f"✅ EMAIL SENT SUCCESSFULLY to {to_email}")
                        if extracted_otp:
                            print(f"🔑 OTP delivered via email: {extracted_otp}")
                        return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ SMTP Authentication Error: {str(e)}")
                print(f"❌ SMTP Authentication failed. Check username/password.")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except smtplib.SMTPConnectError as e:
                logger.error(f"❌ SMTP Connection Error: {str(e)}")
                print(f"❌ Cannot connect to SMTP server {self.smtp_server}:{self.smtp_port}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"❌ Recipients Refused: {str(e)}")
                print(f"❌ Email address {to_email} was refused by server")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except smtplib.SMTPException as e:
                logger.error(f"❌ SMTP Error: {str(e)}")
                print(f"❌ SMTP Error: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except Exception as e:
                logger.error(f"❌ Unexpected email error: {str(e)}")
                print(f"❌ Unexpected error: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Email function error: {str(e)}")
            extracted_otp = re.search(r'\b\d{6}\b', body)
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp.group()}")
            return False
    
    async def send_verification_email(self, email: str, first_name: str, otp: str) -> bool:
        """Send verification email with beautiful inline CSS styling"""
        email_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification - AI Policy Tracker</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
            <table width="100%" cellpadding="0" cellspacing="0" style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background: #ffffff; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <div style="background: rgba(255,255,255,0.2); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(10px);">
                                        <span style="font-size: 40px;">🚀</span>
                                    </div>
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">Welcome to AI Policy Tracker!</h1>
                                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px;">Your Gateway to Global AI Policy Intelligence</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <h2 style="color: #333333; margin: 0 0 20px; font-size: 24px;">Hello {first_name}! 👋</h2>
                                    <p style="color: #666666; line-height: 1.6; font-size: 16px; margin: 0 0 20px;">Thank you for joining our AI Policy community! We're excited to have you on board as we explore the evolving landscape of artificial intelligence governance worldwide.</p>
                                    <p style="color: #666666; line-height: 1.6; font-size: 16px; margin: 0 0 30px;">To complete your registration and unlock access to our comprehensive policy database, please verify your email address using the code below:</p>
                                    
                                    <!-- OTP Section -->
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                        <tr>
                                            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 15px; position: relative;">
                                                <div style="position: absolute; top: -10px; left: -10px; width: 20px; height: 20px; background: rgba(255,255,255,0.2); border-radius: 50%; animation: pulse 2s infinite;"></div>
                                                <div style="position: absolute; top: -5px; right: -5px; width: 15px; height: 15px; background: rgba(255,255,255,0.3); border-radius: 50%; animation: pulse 2s infinite 0.5s;"></div>
                                                <p style="color: #ffffff; margin: 0 0 15px; font-size: 18px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">🔐 Your Verification Code</p>
                                                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px);">
                                                    <h1 style="color: #ffffff; margin: 0; font-size: 48px; font-weight: bold; letter-spacing: 8px; font-family: 'Courier New', monospace; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">{otp}</h1>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Warning Section -->
                                    <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin: 30px 0; text-align: center;">
                                        <p style="color: #856404; margin: 0; font-size: 14px; font-weight: bold;">⏰ This verification code expires in 10 minutes for your security.</p>
                                    </div>
                                    
                                    <!-- Features Preview -->
                                    <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 30px 0;">
                                        <h3 style="color: #333333; margin: 0 0 15px; font-size: 18px;">🌍 What awaits you:</h3>
                                        <ul style="color: #666666; line-height: 1.8; margin: 0; padding-left: 20px;">
                                            <li>Interactive world map with policy visualization</li>
                                            <li>AI-powered policy chat assistant</li>
                                            <li>Comprehensive policy submission system</li>
                                            <li>Real-time policy analytics and insights</li>
                                        </ul>
                                    </div>
                                    
                                    <p style="color: #999999; font-size: 14px; line-height: 1.5; margin: 30px 0 0;">If you didn't create an account with AI Policy Tracker, please ignore this email. Your security is our priority.</p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="color: #999999; margin: 0 0 10px; font-size: 14px;">Best regards,</p>
                                    <p style="color: #667eea; margin: 0; font-size: 18px; font-weight: bold;">✨ AI Policy Tracker Team</p>
                                    <div style="margin: 20px 0 0; padding-top: 20px; border-top: 1px solid #e9ecef;">
                                        <p style="color: #cccccc; margin: 0; font-size: 12px;">Empowering Global AI Governance • 2025</p>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return await self.send_email(
            email, 
            "🚀 Welcome! Verify Your Email - AI Policy Tracker", 
            email_body
        )
    
    async def send_password_reset_email(self, email: str, first_name: str, otp: str) -> bool:
        """Send password reset email with beautiful inline CSS styling"""
        email_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - AI Policy Tracker</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); min-height: 100vh;">
            <table width="100%" cellpadding="0" cellspacing="0" style="min-height: 100vh; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background: #ffffff; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 40px 30px; text-align: center;">
                                    <div style="background: rgba(255,255,255,0.2); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(10px);">
                                        <span style="font-size: 40px;">🔐</span>
                                    </div>
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">Password Reset Request</h1>
                                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 16px;">Secure Your AI Policy Tracker Account</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <h2 style="color: #333333; margin: 0 0 20px; font-size: 24px;">Hello {first_name}! 👋</h2>
                                    <p style="color: #666666; line-height: 1.6; font-size: 16px; margin: 0 0 20px;">We received a request to reset the password for your AI Policy Tracker account. No worries - it happens to the best of us!</p>
                                    <p style="color: #666666; line-height: 1.6; font-size: 16px; margin: 0 0 30px;">Use the verification code below to create a new password and regain access to your account:</p>
                                    
                                    <!-- OTP Section -->
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                        <tr>
                                            <td style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 30px; text-align: center; border-radius: 15px; position: relative;">
                                                <div style="position: absolute; top: -10px; left: -10px; width: 20px; height: 20px; background: rgba(255,255,255,0.2); border-radius: 50%; animation: pulse 2s infinite;"></div>
                                                <div style="position: absolute; top: -5px; right: -5px; width: 15px; height: 15px; background: rgba(255,255,255,0.3); border-radius: 50%; animation: pulse 2s infinite 0.5s;"></div>
                                                <p style="color: #ffffff; margin: 0 0 15px; font-size: 18px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">🔑 Your Reset Code</p>
                                                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px);">
                                                    <h1 style="color: #ffffff; margin: 0; font-size: 48px; font-weight: bold; letter-spacing: 8px; font-family: 'Courier New', monospace; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">{otp}</h1>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Warning Section -->
                                    <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border: 1px solid #ffeaa7; padding: 20px; border-radius: 10px; margin: 30px 0; text-align: center;">
                                        <p style="color: #856404; margin: 0; font-size: 14px; font-weight: bold;">⏰ This reset code expires in 10 minutes for your security.</p>
                                    </div>
                                    
                                    <!-- Security Tips -->
                                    <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 30px 0;">
                                        <h3 style="color: #333333; margin: 0 0 15px; font-size: 18px;">🔒 Security Tips:</h3>
                                        <ul style="color: #666666; line-height: 1.8; margin: 0; padding-left: 20px;">
                                            <li>Choose a strong, unique password</li>
                                            <li>Use a combination of letters, numbers, and symbols</li>
                                            <li>Don't share your password with anyone</li>
                                            <li>Consider using a password manager</li>
                                        </ul>
                                    </div>
                                    
                                    <div style="background: linear-gradient(135deg, #ff7675 0%, #fd79a8 100%); padding: 20px; border-radius: 10px; margin: 30px 0;">
                                        <p style="color: #ffffff; margin: 0; font-size: 14px; text-align: center; font-weight: bold;">⚠️ If you didn't request this password reset, please ignore this email and your password will remain unchanged.</p>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="color: #999999; margin: 0 0 10px; font-size: 14px;">Best regards,</p>
                                    <p style="color: #ff6b6b; margin: 0; font-size: 18px; font-weight: bold;">🔐 AI Policy Tracker Security Team</p>
                                    <div style="margin: 20px 0 0; padding-top: 20px; border-top: 1px solid #e9ecef;">
                                        <p style="color: #cccccc; margin: 0; font-size: 12px;">Protecting Your AI Policy Data • 2025</p>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return await self.send_email(
            email, 
            "🔐 Password Reset Code - AI Policy Tracker", 
            email_body
        )

# Global email service instance
email_service = EmailService()
