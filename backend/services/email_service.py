"""
Email Service
Handles email sending functionality with SMTP
"""
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str) -> bool:
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
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.warning("⚠️ SMTP credentials missing")
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp}")
            return False
        
        logger.info(f"📧 Sending email to: {to_email}")
        logger.info(f"📧 SMTP Config: {settings.SMTP_USERNAME} via {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
        
        # Create message with proper encoding
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.FROM_EMAIL
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
            logger.info(f"🔌 Connecting to {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
            
            # Use SMTP_SSL instead of SMTP + starttls for better compatibility
            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
            else:
                server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
                server.ehlo()
                logger.info("🔒 Starting TLS...")
                server.starttls()
                server.ehlo()
            
            logger.info(f"🔑 Authenticating as: {settings.SMTP_USERNAME}")
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            logger.info("📤 Sending message...")
            text = msg.as_string()
            server.sendmail(settings.FROM_EMAIL, [to_email], text)
            server.quit()
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            print(f"✅ EMAIL ACTUALLY SENT to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication Error: {str(e)}")
            print(f"❌ AUTH FAILED: {str(e)}")
            print(f"🔑 USERNAME: {settings.SMTP_USERNAME}")
            print(f"🔑 PASSWORD LENGTH: {len(settings.SMTP_PASSWORD)} chars")
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp}")
            return False
            
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ SMTP Connection Error: {str(e)}")
            print(f"❌ CONNECTION FAILED: {str(e)}")
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp}")
            return False
            
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP Error: {str(e)}")
            print(f"❌ SMTP ERROR: {str(e)}")
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected email error: {str(e)}")
            print(f"❌ UNEXPECTED ERROR: {str(e)}")
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Email function error: {str(e)}")
        print(f"❌ FUNCTION ERROR: {str(e)}")
        if extracted_otp:
            print(f"🔑 USE THIS OTP: {extracted_otp}")
        return False
