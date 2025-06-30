"""
Email service for sending notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email using SMTP"""
        try:
            if not self.username or not self.password:
                logger.warning("Email credentials not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_verification_email(self, email: str, otp: str, name: str) -> bool:
        """Send email verification OTP"""
        subject = "Verify Your Email - AI Policy Tracker"
        body = f"""
        <html>
        <body>
            <h2>Welcome to AI Policy Tracker, {name}!</h2>
            <p>Thank you for signing up. Please verify your email address using the code below:</p>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0;">
                {otp}
            </div>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>AI Policy Tracker Team</p>
        </body>
        </html>
        """
        return self.send_email(email, subject, body, is_html=True)
    
    def send_password_reset_email(self, email: str, otp: str, name: str) -> bool:
        """Send password reset OTP"""
        subject = "Password Reset - AI Policy Tracker"
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {name},</p>
            <p>You requested to reset your password. Use the code below to proceed:</p>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0;">
                {otp}
            </div>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>AI Policy Tracker Team</p>
        </body>
        </html>
        """
        return self.send_email(email, subject, body, is_html=True)
