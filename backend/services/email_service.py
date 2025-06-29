"""
Email service for sending notifications and OTPs.
"""
import logging
import smtplib
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings
from core.database import get_collections
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
            msg['From'] = self.from_email
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
                
                # Use SMTP_SSL instead of SMTP + starttls for better compatibility
                if self.smtp_port == 465:
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                else:
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.ehlo()
                    logger.info("🔒 Starting TLS...")
                    server.starttls()
                    server.ehlo()
                
                logger.info(f"🔑 Authenticating as: {self.smtp_username}")
                server.login(self.smtp_username, self.smtp_password)
                
                logger.info("📤 Sending message...")
                text = msg.as_string()
                server.sendmail(self.from_email, [to_email], text)
                server.quit()
                
                logger.info(f"✅ Email sent successfully to {to_email}")
                print(f"✅ EMAIL ACTUALLY SENT to {to_email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ SMTP Authentication Error: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except smtplib.SMTPConnectError as e:
                logger.error(f"❌ SMTP Connection Error: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except smtplib.SMTPException as e:
                logger.error(f"❌ SMTP Error: {str(e)}")
                if extracted_otp:
                    print(f"🔑 USE THIS OTP: {extracted_otp}")
                return False
                
            except Exception as e:
                logger.error(f"❌ Unexpected email error: {str(e)}")
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
        """Send verification email with beautiful Tailwind styling"""
        email_body = f"""
        <div class="max-w-2xl mx-auto bg-gradient-to-br from-blue-500 to-purple-600 p-5 rounded-3xl">
            <div class="bg-white p-10 rounded-2xl shadow-2xl">
                <div class="text-center mb-8">
                    <div class="bg-gradient-to-br from-blue-500 to-purple-600 w-20 h-20 rounded-full mx-auto mb-5 flex items-center justify-center">
                        <span class="text-4xl text-white">🚀</span>
                    </div>
                    <h1 class="text-gray-800 m-0 text-3xl font-bold">Welcome to AI Policy Tracker!</h1>
                </div>
                
                <p class="text-gray-600 text-lg leading-relaxed">Hello <strong class="text-gray-800">{first_name}</strong>,</p>
                <p class="text-gray-600 text-lg leading-relaxed">Thank you for joining our AI Policy community! To complete your registration, please verify your email address.</p>
                
                <div class="bg-gradient-to-br from-blue-500 to-purple-600 p-8 text-center rounded-2xl my-8">
                    <p class="text-white m-0 mb-4 text-xl font-bold">Your Verification Code</p>
                    <h1 class="text-white text-5xl m-0 tracking-widest font-mono">{otp}</h1>
                </div>
                
                <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-4 my-5">
                    <p class="text-yellow-800 m-0 text-sm text-center"><strong>⏰ This code expires in 10 minutes.</strong></p>
                </div>
                
                <p class="text-gray-600 text-sm leading-relaxed">If you didn't create an account with us, please ignore this email.</p>
                
                <hr class="my-8 border-gray-200">
                <div class="text-center">
                    <p class="text-gray-500 text-sm m-0">Best regards,</p>
                    <p class="text-blue-500 text-lg font-bold mt-1 m-0">AI Policy Tracker Team</p>
                </div>
            </div>
        </div>
        """
        
        return await self.send_email(
            email, 
            "🚀 Welcome! Verify Your Email - AI Policy Tracker", 
            email_body
        )
    
    async def send_password_reset_email(self, email: str, first_name: str, otp: str) -> bool:
        """Send password reset email with beautiful Tailwind styling"""
        email_body = f"""
        <div class="max-w-2xl mx-auto bg-gradient-to-br from-red-500 to-orange-600 p-5 rounded-3xl">
            <div class="bg-white p-10 rounded-2xl shadow-2xl">
                <div class="text-center mb-8">
                    <div class="bg-gradient-to-br from-red-500 to-orange-600 w-20 h-20 rounded-full mx-auto mb-5 flex items-center justify-center">
                        <span class="text-4xl text-white">🔐</span>
                    </div>
                    <h1 class="text-gray-800 m-0 text-3xl font-bold">Password Reset Request</h1>
                </div>
                
                <p class="text-gray-600 text-lg leading-relaxed">Hello <strong class="text-gray-800">{first_name}</strong>,</p>
                <p class="text-gray-600 text-lg leading-relaxed">You requested to reset your password for your AI Policy Tracker account.</p>
                
                <div class="bg-gradient-to-br from-red-500 to-orange-600 p-8 text-center rounded-2xl my-8">
                    <p class="text-white m-0 mb-4 text-xl font-bold">Your Reset Code</p>
                    <h1 class="text-white text-5xl m-0 tracking-widest font-mono">{otp}</h1>
                </div>
                
                <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-4 my-5">
                    <p class="text-yellow-800 m-0 text-sm text-center"><strong>⏰ This code expires in 10 minutes.</strong></p>
                </div>
                
                <p class="text-gray-600 text-sm leading-relaxed">If you didn't request this reset, please ignore this email and your password will remain unchanged.</p>
                
                <hr class="my-8 border-gray-200">
                <div class="text-center">
                    <p class="text-gray-500 text-sm m-0">Best regards,</p>
                    <p class="text-red-500 text-lg font-bold mt-1 m-0">AI Policy Tracker Team</p>
                </div>
            </div>
        </div>
        """
        
        return await self.send_email(
            email, 
            "🔐 Password Reset Code - AI Policy Tracker", 
            email_body
        )

# Global email service instance
email_service = EmailService()
