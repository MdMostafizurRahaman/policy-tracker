from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime, timedelta
import os
import motor.motor_asyncio
import shutil
import uuid
from bson import ObjectId
from dotenv import load_dotenv
import mimetypes
import io
import json
import jwt
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import uvicorn
import asyncio
import logging
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import smtplib
import re
import bcrypt
import jwt
import random
import string
import traceback
from chatbot import (
    init_chatbot, 
    ChatRequest, 
    chat_endpoint, 
    get_conversation_endpoint, 
    delete_conversation_endpoint, 
    get_conversations_endpoint,
    policy_search_endpoint
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# JWT and Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Enhanced Email Configuration with fallback
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@aipolicytracker.com")

# Google OAuth Configuration with fallback
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced AI Policy Database API", 
    version="4.0.0",
    description="Complete AI Policy Management System with Authentication, Submissions, and Admin Dashboard"
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://policy-tracker-5.onrender.com",
        "https://policy-tracker-f.onrender.com", 
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "https://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection with retry logic
MONGODB_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017/ai_policy_db")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.ai_policy_database

# Collections
users_collection = db.users
temp_submissions_collection = db.temp_submissions
master_policies_collection = db.master_policies
admin_actions_collection = db.admin_actions
files_collection = db.files
otp_collection = db.otp_codes

# Security
security = HTTPBearer()

# Enhanced Policy Areas Configuration
POLICY_AREAS = [
    {
        "id": "ai-safety",
        "name": "AI Safety",
        "description": "Policies ensuring AI systems are safe and beneficial",
        "icon": "🛡️",
        "color": "from-red-500 to-pink-600",
        "gradient": "bg-gradient-to-r from-red-500 to-pink-600"
    },
    {
        "id": "cyber-safety",
        "name": "CyberSafety", 
        "description": "Cybersecurity and digital safety policies",
        "icon": "🔒",
        "color": "from-blue-500 to-cyan-600",
        "gradient": "bg-gradient-to-r from-blue-500 to-cyan-600"
    },
    {
        "id": "digital-education",
        "name": "Digital Education",
        "description": "Educational technology and digital literacy policies",
        "icon": "🎓",
        "color": "from-green-500 to-emerald-600",
        "gradient": "bg-gradient-to-r from-green-500 to-emerald-600"
    },
    {
        "id": "digital-inclusion",
        "name": "Digital Inclusion",
        "description": "Bridging the digital divide and ensuring equal access",
        "icon": "🌐",
        "color": "from-purple-500 to-indigo-600",
        "gradient": "bg-gradient-to-r from-purple-500 to-indigo-600"
    },
    {
        "id": "digital-leisure",
        "name": "Digital Leisure",
        "description": "Gaming, entertainment, and digital recreation policies",
        "icon": "🎮",
        "color": "from-yellow-500 to-orange-600",
        "gradient": "bg-gradient-to-r from-yellow-500 to-orange-600"
    },
    {
        "id": "disinformation",
        "name": "(Dis)Information",
        "description": "Combating misinformation and promoting truth",
        "icon": "📰",
        "color": "from-gray-500 to-slate-600",
        "gradient": "bg-gradient-to-r from-gray-500 to-slate-600"
    },
    {
        "id": "digital-work",
        "name": "Digital Work",
        "description": "Future of work and digital employment policies",
        "icon": "💼",
        "color": "from-teal-500 to-blue-600",
        "gradient": "bg-gradient-to-r from-teal-500 to-blue-600"
    },
    {
        "id": "mental-health",
        "name": "Mental Health",
        "description": "Digital wellness and mental health policies",
        "icon": "🧠",
        "color": "from-pink-500 to-rose-600",
        "gradient": "bg-gradient-to-r from-pink-500 to-rose-600"
    },
    {
        "id": "physical-health",
        "name": "Physical Health",
        "description": "Healthcare technology and physical wellness policies",
        "icon": "❤️",
        "color": "from-emerald-500 to-green-600",
        "gradient": "bg-gradient-to-r from-emerald-500 to-green-600"
    },
    {
        "id": "social-media-gaming",
        "name": "Social Media/Gaming Regulation",
        "description": "Social media platforms and gaming regulation",
        "icon": "📱",
        "color": "from-indigo-500 to-purple-600",
        "gradient": "bg-gradient-to-r from-indigo-500 to-purple-600"
    }
]

# Enhanced Countries list
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas",
    "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize",
    "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil",
    "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon",
    "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba",
    "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
    "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia",
    "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
    "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan",
    "Kenya", "Kiribati", "North Korea", "South Korea", "Kuwait", "Kyrgyzstan",
    "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
    "Liechtenstein", "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi",
    "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania",
    "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia",
    "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria",
    "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
    "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan",
    "Suriname", "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan",
    "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga",
    "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
    "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

# Admin Configuration
SUPER_ADMIN_EMAIL = "admin@gmail.com"
SUPER_ADMIN_PASSWORD = "admin123"

# Enhanced Pydantic Models
class UserRegistration(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    confirmPassword: str
    country: str

    @validator('firstName', 'lastName')
    def validate_names(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('confirmPassword')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('country')
    def validate_country(cls, v):
        if v not in COUNTRIES:
            raise ValueError('Invalid country selected')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    token: str

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str

    @validator('otp')
    def validate_otp(cls, v):
        if not v or len(v) != 6 or not v.isdigit():
            raise ValueError('OTP must be exactly 6 digits')
        return v

class PasswordReset(BaseModel):
    email: EmailStr
    otp: str
    newPassword: str
    confirmPassword: str

    @validator('newPassword')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('confirmPassword')
    def passwords_match(cls, v, values, **kwargs):
        if 'newPassword' in values and v != values['newPassword']:
            raise ValueError('Passwords do not match')
        return v

class SubPolicy(BaseModel):
    policyName: str = ""
    policyId: str = ""
    policyDescription: str = ""
    targetGroups: List[str] = []
    policyFile: Optional[Dict] = None
    policyLink: str = ""
    implementation: Dict = Field(default_factory=dict)
    evaluation: Dict = Field(default_factory=dict)
    participation: Dict = Field(default_factory=dict)
    alignment: Dict = Field(default_factory=dict)
    status: str = "pending"
    admin_notes: str = ""

class PolicyArea(BaseModel):
    area_id: str
    area_name: str
    policies: List[SubPolicy] = Field(default_factory=list)

    @validator('area_id')
    def validate_area_id(cls, v):
        valid_ids = [area["id"] for area in POLICY_AREAS]
        if v not in valid_ids:
            raise ValueError(f'Invalid policy area ID. Must be one of: {valid_ids}')
        return v

class EnhancedSubmission(BaseModel):
    user_id: str
    user_email: str
    user_name: str
    country: str
    policyAreas: List[PolicyArea]
    submission_status: str = "pending"
    submitted_at: Optional[str] = None
    
    @validator('policyAreas')
    def validate_policy_areas(cls, v):
        if not v:
            raise ValueError('At least one policy area must be provided')
        return v

    @validator('country')
    def validate_country(cls, v):
        if v not in COUNTRIES:
            raise ValueError('Invalid country')
        return v

class PolicyStatusUpdate(BaseModel):
    submission_id: str
    area_id: str
    policy_index: int
    status: str
    admin_notes: str = ""
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'approved', 'rejected', 'under_review', 'needs_revision']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v

    @validator('policy_index')
    def validate_policy_index(cls, v):
        if v < 0:
            raise ValueError('Policy index must be non-negative')
        return v

# Enhanced Utility Functions
def convert_objectid(obj):
    """Convert ObjectId to string recursively"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

def pydantic_to_dict(obj):
    """Convert Pydantic model to dict recursively"""
    if hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, dict):
        return {key: pydantic_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [pydantic_to_dict(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj
    else:
        return obj

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

async def send_email(to_email: str, subject: str, body: str) -> bool:
    """FIXED email sending with proper SMTP handling"""
    try:
        # Extract OTP for logging
        otp_match = re.search(r'\b\d{6}\b', body)
        extracted_otp = otp_match.group() if otp_match else None
        
        # Always log OTP for development
        if extracted_otp:
            logger.info(f"🔑 OTP for {to_email}: {extracted_otp}")
            print(f"🔑 DEVELOPMENT OTP for {to_email}: {extracted_otp}")
        
        # Check credentials
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("⚠️ SMTP credentials missing")
            if extracted_otp:
                print(f"🔑 USE THIS OTP: {extracted_otp}")
            return False
        
        logger.info(f"📧 Sending email to: {to_email}")
        logger.info(f"📧 SMTP Config: {SMTP_USERNAME} via {SMTP_SERVER}:{SMTP_PORT}")
        
        # Create message with proper encoding
        msg = MIMEMultipart('alternative')
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.set_charset('utf-8')
        
        # Add both HTML and plain text versions
        plain_text = f"Your verification code is: {extracted_otp}" if extracted_otp else "Verification email"
        text_part = MIMEText(plain_text, 'plain', 'utf-8')
        html_part = MIMEText(body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # FIXED: Use proper SMTP connection with context manager
        try:
            # Create SMTP connection
            logger.info(f"🔌 Connecting to {SMTP_SERVER}:{SMTP_PORT}")
            
            # Use SMTP_SSL instead of SMTP + starttls for better compatibility
            if SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            else:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.ehlo()
                logger.info("🔒 Starting TLS...")
                server.starttls()
                server.ehlo()
            
            logger.info(f"🔑 Authenticating as: {SMTP_USERNAME}")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            logger.info("📤 Sending message...")
            text = msg.as_string()
            server.sendmail(FROM_EMAIL, [to_email], text)
            server.quit()
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            print(f"✅ EMAIL ACTUALLY SENT to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication Error: {str(e)}")
            print(f"❌ AUTH FAILED: {str(e)}")
            print(f"🔑 USERNAME: {SMTP_USERNAME}")
            print(f"🔑 PASSWORD LENGTH: {len(SMTP_PASSWORD)} chars")
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
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await users_collection.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return convert_objectid(user)
    except jwt.PyJWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Get current admin user"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Enhanced file handling
async def save_file_to_db(file: UploadFile, metadata: Dict = None) -> str:
    """Save uploaded file to database"""
    try:
        file_content = await file.read()
        await file.seek(0)
        
        file_doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_data": file_content,
            "size": len(file_content),
            "upload_date": datetime.utcnow(),
            **(metadata or {})
        }
        
        result = await files_collection.insert_one(file_doc)
        logger.info(f"File saved to database: {file.filename} (ID: {result.inserted_id})")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error saving file to database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

async def get_file_from_db(file_id: str):
    """Get file from database"""
    try:
        file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        return file_doc
    except Exception as e:
        logger.error(f"Error retrieving file: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

# Enhanced admin initialization
async def initialize_super_admin():
    """Initialize super admin with enhanced error handling"""
    try:
        existing_admin = await users_collection.find_one({"email": SUPER_ADMIN_EMAIL})
        if not existing_admin:
            admin_doc = {
                "firstName": "Super",
                "lastName": "Admin",
                "email": SUPER_ADMIN_EMAIL,
                "password": hash_password(SUPER_ADMIN_PASSWORD),
                "country": "Global",
                "is_admin": True,
                "is_super_admin": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await users_collection.insert_one(admin_doc)
            logger.info("Super admin created successfully")
        else:
            # Update password if needed
            if not verify_password(SUPER_ADMIN_PASSWORD, existing_admin["password"]):
                await users_collection.update_one(
                    {"email": SUPER_ADMIN_EMAIL},
                    {"$set": {
                        "password": hash_password(SUPER_ADMIN_PASSWORD),
                        "updated_at": datetime.utcnow()
                    }}
                )
                logger.info("Super admin password updated")
            logger.info("Super admin already exists")
    except Exception as e:
        logger.error(f"Error initializing super admin: {e}")

# Database health check
async def check_database_connection():
    """Check if database is accessible"""
    try:
        await db.command("ping")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AI Policy Tracker API v4.0.0")
    
    # Check database connection
    if await check_database_connection():
        await initialize_super_admin()
        
        # Initialize the database-only chatbot
        init_chatbot(client)
        logger.info("Database-only chatbot initialized")
        
        logger.info("Application startup completed successfully")
    else:
        logger.error("Application startup failed - database connection issue")

# Enhanced Authentication Endpoints
@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    """Enhanced user registration with better validation and email handling"""
    try:
        logger.info(f"Registration attempt for: {user_data.email}")
        
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user document
        user_doc = {
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "email": user_data.email,
            "password": hashed_password,
            "country": user_data.country,
            "is_admin": False,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save user
        result = await users_collection.insert_one(user_doc)
        logger.info(f"User created with ID: {result.inserted_id}")
        
        # Clean up existing OTPs for this email
        await otp_collection.delete_many({
            "email": user_data.email,
            "type": "email_verification"
        })
        
        # Generate and save OTP
        otp = generate_otp()
        otp_doc = {
            "email": user_data.email,
            "otp": otp,
            "type": "email_verification",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        await otp_collection.insert_one(otp_doc)
        logger.info(f"OTP generated and saved for {user_data.email}: {otp}")
        
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
                
                <p style="color: #555; font-size: 16px; line-height: 1.6;">Hello <strong>{user_data.firstName}</strong>,</p>
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
        
        # Send verification email
        email_sent = await send_email(
            user_data.email, 
            "🚀 Welcome! Verify Your Email - AI Policy Tracker", 
            email_body
        )
        
        logger.info(f"Registration completed for {user_data.email}, email_sent: {email_sent}")
        
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
            "otp_for_dev": otp if not email_sent else None  # Include OTP if email failed
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/verify-email")
async def verify_email(verification: OTPVerification):
    """Enhanced email verification"""
    try:
        # Find valid OTP
        otp_doc = await otp_collection.find_one({
            "email": verification.email,
            "otp": verification.otp,
            "type": "email_verification",
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not otp_doc:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        
        # Update user as verified
        result = await users_collection.update_one(
            {"email": verification.email},
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete used OTP
        await otp_collection.delete_one({"_id": otp_doc["_id"]})
        
        logger.info(f"Email verified successfully for {verification.email}")
        return {"success": True, "message": "Email verified successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.get("/api/dev/get-latest-otp/{email}")
async def get_latest_otp_for_development(email: str):
    """Development endpoint to get latest OTP (remove in production)"""
    try:
        # Only allow in development
        if os.getenv("ENVIRONMENT") == "production":
            raise HTTPException(status_code=404, detail="Not found")
        
        otp_doc = await otp_collection.find_one(
            {"email": email},
            sort=[("created_at", -1)]  # Get the latest OTP
        )
        
        if not otp_doc:
            return {"success": False, "message": "No OTP found for this email"}
        
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

@app.post("/api/auth/login")
async def login_user(login_data: UserLogin):
    """Enhanced user login"""
    try:
        # Find user
        user = await users_collection.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if email is verified
        if not user.get("is_verified", False):
            raise HTTPException(
                status_code=401, 
                detail="Please verify your email first. Check your inbox for verification code."
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        # Update last login
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        logger.info(f"User logged in successfully: {login_data.email}")
        
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

@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Enhanced Google OAuth authentication with better error handling"""
    try:
        # Check if Google Client ID is configured
        if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "641700598182-a8mlt3q0dbi7e71ugr581jjhmi020n88.apps.googleusercontent.com":
            logger.error("Google Client ID not configured")
            raise HTTPException(
                status_code=501, 
                detail="Google authentication is not configured on the server"
            )
        
        logger.info(f"Attempting Google auth with Client ID: {GOOGLE_CLIENT_ID[:20]}...")
        logger.info(f"Token received (first 50 chars): {request.token[:50]}...")
        
        # Verify the Google token with enhanced error handling
        try:
            idinfo = id_token.verify_oauth2_token(
                request.token, 
                google_requests.Request(), 
                GOOGLE_CLIENT_ID
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
        
        # Check if user exists
        existing_user = await users_collection.find_one({"email": email})
        
        if existing_user:
            logger.info(f"Existing user found: {email}")
            # Update user info and mark as Google authenticated
            await users_collection.update_one(
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
            user = await users_collection.find_one({"email": email})
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
            
            result = await users_collection.insert_one(new_user)
            user = await users_collection.find_one({"_id": result.inserted_id})

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
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Google authentication failed: {str(e)}"
        )

@app.post("/api/auth/forgot-password")
async def forgot_password(email_data: dict):
    """Enhanced forgot password with better email"""
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check if user exists
        user = await users_collection.find_one({"email": email})
        if not user:
            # Don't reveal if email exists or not for security
            return {"success": True, "message": "If the email exists, a reset code has been sent"}
        
        # Clean up existing OTPs
        await otp_collection.delete_many({
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
        await otp_collection.insert_one(otp_doc)
        
        # Enhanced password reset email
        email_body = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 20px; border-radius: 20px;">
            <div style="background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 40px; color: white;">🔐</span>
                    </div>
                    <h1 style="color: #333; margin: 0; font-size: 28px; font-weight: bold;">Password Reset Request</h1>
                </div>
                
                <p style="color: #555; font-size: 16px; line-height: 1.6;">Hello <strong>{user['firstName']}</strong>,</p>
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
        
        await send_email(email, "🔐 Password Reset Code - AI Policy Tracker", email_body)
        
        return {"success": True, "message": "Password reset code sent to your email"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

@app.post("/api/auth/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Enhanced password reset"""
    try:
        # Find valid OTP
        otp_doc = await otp_collection.find_one({
            "email": reset_data.email,
            "otp": reset_data.otp,
            "type": "password_reset",
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not otp_doc:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code")
        
        # Hash new password
        hashed_password = hash_password(reset_data.newPassword)
        
        # Update user password
        result = await users_collection.update_one(
            {"email": reset_data.email},
            {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete used OTP
        await otp_collection.delete_one({"_id": otp_doc["_id"]})
        
        logger.info(f"Password reset successfully for {reset_data.email}")
        return {"success": True, "message": "Password reset successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

# Enhanced Policy Management Endpoints
@app.post("/api/submit-enhanced-form")
async def submit_enhanced_form(
    submission: EnhancedSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Enhanced policy submission with better validation"""
    try:
        logger.info(f"Enhanced submission received from user {current_user['email']}")
        
        # Validate user owns this submission
        if submission.user_id != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Unauthorized submission")
        
        # Filter out empty policy areas and policies
        filtered_policy_areas = []
        total_policies = 0
        
        for area in submission.policyAreas:
            non_empty_policies = [
                policy for policy in area.policies 
                if policy.policyName and policy.policyName.strip()
            ]
            if non_empty_policies:
                area_dict = {
                    "area_id": area.area_id,
                    "area_name": area.area_name,
                    "policies": [policy.dict() for policy in non_empty_policies]
                }
                filtered_policy_areas.append(area_dict)
                total_policies += len(non_empty_policies)
        
        if not filtered_policy_areas:
            raise HTTPException(
                status_code=400, 
                detail="At least one policy with a name must be provided"
            )
        
        # Prepare submission document
        submission_dict = {
            "user_id": submission.user_id,
            "user_email": submission.user_email,
            "user_name": submission.user_name,
            "country": submission.country,
            "policyAreas": filtered_policy_areas,
            "submission_status": "pending",
            "total_policies": total_policies,
            "total_areas": len(filtered_policy_areas),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into temporary collection
        result = await temp_submissions_collection.insert_one(submission_dict)
        
        if result.inserted_id:
            logger.info(
                f"Enhanced submission successful: {total_policies} policies in "
                f"{len(filtered_policy_areas)} areas from {submission.user_email}"
            )
            
            return {
                "success": True, 
                "message": "Enhanced submission successful and is pending admin review", 
                "submission_id": str(result.inserted_id),
                "total_policies": total_policies,
                "policy_areas_count": len(filtered_policy_areas)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save submission")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced submission error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

# Enhanced admin endpoints with better policy scoring
@app.put("/api/admin/update-enhanced-policy-status")
async def update_enhanced_policy_status(
    status_update: PolicyStatusUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Enhanced policy status update with automatic master DB movement"""
    try:
        submission_id = status_update.submission_id
        area_id = status_update.area_id
        policy_index = status_update.policy_index
        new_status = status_update.status
        admin_notes = status_update.admin_notes
        
        # Find the submission
        submission = await temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Find the policy area and validate policy exists
        area_found = False
        policy_areas = submission.get("policyAreas", [])
        
        for i, area in enumerate(policy_areas):
            if area["area_id"] == area_id:
                if policy_index >= len(area["policies"]):
                    raise HTTPException(status_code=404, detail="Policy not found")
                
                # Update policy status
                policy_areas[i]["policies"][policy_index]["status"] = new_status
                policy_areas[i]["policies"][policy_index]["admin_notes"] = admin_notes
                policy_areas[i]["policies"][policy_index]["reviewed_at"] = datetime.utcnow()
                policy_areas[i]["policies"][policy_index]["reviewed_by"] = admin_user["email"]
                area_found = True
                break
        
        if not area_found:
            raise HTTPException(status_code=404, detail="Policy area not found")
        
        # Update submission
        await temp_submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {
                "policyAreas": policy_areas,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Log admin action
        admin_log = {
            "action": f"status_update_{new_status}",
            "submission_id": submission_id,
            "area_id": area_id,
            "policy_index": policy_index,
            "admin_id": str(admin_user["_id"]),
            "admin_email": admin_user["email"],
            "admin_notes": admin_notes,
            "timestamp": datetime.utcnow()
        }
        await admin_actions_collection.insert_one(admin_log)
        
        # If approved, move to master DB immediately
        if new_status == 'approved':
            await move_policy_to_master_internal(submission, area_id, policy_index, admin_user)
        
        # Update overall submission status
        await update_submission_status(submission_id)
        
        logger.info(f"Policy status updated to {new_status} by {admin_user['email']}")
        return {"success": True, "message": f"Policy status updated to {new_status}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy status update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")

async def move_policy_to_master_internal(submission: dict, area_id: str, policy_index: int, admin_user: dict):
    """Internal function to move approved policy to master database"""
    try:
        # Get the policy
        policy = None
        for area in submission.get("policyAreas", []):
            if area["area_id"] == area_id:
                if policy_index < len(area["policies"]):
                    policy = area["policies"][policy_index]
                    break
        
        if not policy:
            return
        
        # Check if already moved to master
        existing_master = await master_policies_collection.find_one({
            "original_submission_id": str(submission["_id"]),
            "policyArea": area_id,
            "policy_index": policy_index,
            "master_status": "active"
        })
        
        if existing_master:
            return  # Already in master DB
        
        # Get area info for enhanced data
        area_info = next((area for area in POLICY_AREAS if area["id"] == area_id), None)
        
        # Prepare policy for master DB with enhanced metadata
        master_policy = {
            **policy,
            "country": submission["country"],
            "policyArea": area_id,
            "area_name": area_info["name"] if area_info else area_id,
            "area_icon": area_info["icon"] if area_info else "📄",
            "area_color": area_info["color"] if area_info else "from-gray-500 to-gray-600",
            "user_id": submission["user_id"],
            "user_email": submission.get("user_email", ""),
            "user_name": submission.get("user_name", ""),
            "original_submission_id": str(submission["_id"]),
            "policy_index": policy_index,
            "moved_to_master_at": datetime.utcnow(),
            "approved_by": str(admin_user["_id"]),
            "approved_by_email": admin_user["email"],
            "master_status": "active",
            # FIXED: Don't set visibility field - all approved policies are public by default
            "policy_score": calculate_policy_score(policy),
            "completeness_score": calculate_completeness_score(policy)
        }
        
        # Insert into master collection
        result = await master_policies_collection.insert_one(master_policy)
        
        if result.inserted_id:
            logger.info(f"Policy moved to master DB: {policy.get('policyName', 'Unnamed')} from {submission['country']}")
    
    except Exception as e:
        logger.error(f"Error moving policy to master: {str(e)}")

def calculate_policy_score(policy: dict) -> int:
    """Calculate policy completeness score (0-100)"""
    score = 0
    
    # Basic info (30 points)
    if policy.get("policyName"):
        score += 10
    if policy.get("policyId"):
        score += 5
    if policy.get("policyDescription"):
        score += 15
    
    # Implementation details (25 points)
    impl = policy.get("implementation", {})
    if impl.get("yearlyBudget"):
        score += 10
    if impl.get("deploymentYear"):
        score += 5
    if impl.get("budgetCurrency"):
        score += 5
    if impl.get("privateSecFunding") is not None:
        score += 5
    
    # Evaluation (20 points)
    eval_data = policy.get("evaluation", {})
    if eval_data.get("isEvaluated"):
        score += 10
        if eval_data.get("evaluationType"):
            score += 5
        if eval_data.get("riskAssessment"):
            score += 5
    
    # Participation (15 points)
    part = policy.get("participation", {})
    if part.get("hasConsultation"):
        score += 10
        if part.get("consultationStartDate"):
            score += 3
        if part.get("commentsPublic"):
            score += 2
    
    # Alignment (10 points)
    align = policy.get("alignment", {})
    if align.get("aiPrinciples"):
        score += 5
    if align.get("humanRightsAlignment"):
        score += 3
    if align.get("internationalCooperation"):
        score += 2
    
    return min(score, 100)

def calculate_completeness_score(policy: dict) -> str:
    """Calculate policy completeness level"""
    score = calculate_policy_score(policy)
    
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "fair"
    else:
        return "basic"

async def update_submission_status(submission_id: str):
    """Enhanced submission status update"""
    try:
        submission = await temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            return
        
        policy_areas = submission.get("policyAreas", [])
        if not policy_areas:
            new_status = "empty"
        else:
            all_policies = []
            for area in policy_areas:
                all_policies.extend(area.get("policies", []))
            
            if not all_policies:
                new_status = "empty"
            else:
                policy_statuses = [p.get("status", "pending") for p in all_policies]
                
                approved_count = sum(1 for status in policy_statuses if status == "approved")
                total_count = len(policy_statuses)
                
                if approved_count == total_count:
                    new_status = "fully_approved"
                elif approved_count > 0:
                    new_status = "partially_approved"
                elif all(status in ["rejected", "needs_revision"] for status in policy_statuses):
                    new_status = "processed"
                else:
                    new_status = "under_review"
        
        await temp_submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {
                "submission_status": new_status, 
                "updated_at": datetime.utcnow()
            }}
        )
    except Exception as e:
        logger.error(f"Error updating submission status: {e}")

# Enhanced master policies endpoint for map
@app.get("/api/public/master-policies")
async def get_public_master_policies(
    limit: int = Query(1000, ge=1, le=1000),
    country: str = None,
    area: str = None
):
    """Enhanced public endpoint - shows ALL approved policies with better deduplication"""
    try:
        # FIXED: Remove ALL visibility filters - just get active master policies
        master_filter = {"master_status": "active"}
        
        if country:
            master_filter["country"] = country
        if area:
            master_filter["policyArea"] = area
        
        # Get policies from master collection with ALL fields
        master_policies = []
        async for doc in master_policies_collection.find(master_filter).limit(limit).sort("moved_to_master_at", -1):
            policy_dict = convert_objectid(doc)
            # Ensure consistent field names for frontend compatibility
            policy_dict["name"] = policy_dict.get("policyName", "Unnamed Policy")
            policy_dict["area_id"] = policy_dict.get("policyArea")
            master_policies.append(policy_dict)
        
        # ALSO check temp_submissions for approved policies that might not be migrated yet
        temp_filter = {}
        if country:
            temp_filter["country"] = country
        
        temp_policies = []
        async for submission in temp_submissions_collection.find(temp_filter):
            country_name = submission.get("country")
            if country and country_name != country:
                continue
                
            # Handle different data formats
            if "policyAreas" in submission:
                policy_areas = submission["policyAreas"]
                
                if isinstance(policy_areas, list):
                    # New format: list of {area_id, area_name, policies}
                    for area in policy_areas:
                        area_id = area.get("area_id")
                        if not area or (area and area_id == area):
                            policies = area.get("policies", [])
                            for policy_index, policy in enumerate(policies):
                                if policy.get("status") == "approved":
                                    # Check if already in master
                                    exists = await master_policies_collection.find_one({
                                        "original_submission_id": str(submission["_id"]),
                                        "policyArea": area_id,
                                        "policy_index": policy_index
                                    })
                                    if not exists:
                                        area_info = next((a for a in POLICY_AREAS if a["id"] == area_id), None)
                                        temp_policy = {
                                            **convert_objectid(policy),
                                            "country": country_name,
                                            "policyArea": area_id,
                                            "area_name": area_info["name"] if area_info else area_id,
                                            "area_icon": area_info["icon"] if area_info else "📄",
                                            "name": policy.get("policyName", "Unnamed Policy"),
                                            "area_id": area_id,
                                            "master_status": "active"
                                        }
                                        temp_policies.append(temp_policy)
                elif isinstance(policy_areas, dict):
                    # Old format: {area_id: [policies]}
                    for area_id, policies in policy_areas.items():
                        if isinstance(policies, list):
                            for policy_index, policy in enumerate(policies):
                                if policy.get("status") == "approved":
                                    # Check if already in master
                                    exists = await master_policies_collection.find_one({
                                        "original_submission_id": str(submission["_id"]),
                                        "policyArea": area_id,
                                        "policy_index": policy_index
                                    })
                                    if not exists:
                                        area_info = next((a for a in POLICY_AREAS if a["id"] == area_id), None)
                                        temp_policy = {
                                            **convert_objectid(policy),
                                            "country": country_name,
                                            "policyArea": area_id,
                                            "area_name": area_info["name"] if area_info else area_id,
                                            "area_icon": area_info["icon"] if area_info else "📄",
                                            "name": policy.get("policyName", "Unnamed Policy"),
                                            "area_id": area_id,
                                            "master_status": "active"
                                        }
                                        temp_policies.append(temp_policy)
        
        # Combine both sources
        all_policies = master_policies + temp_policies
        
        # FIXED: Use MongoDB _id as the primary deduplication key (most reliable)
        unique_policies = []
        seen_ids = set()
        
        for policy in all_policies:
            # Use the MongoDB _id as the primary key (most reliable)
            policy_id = str(policy.get('_id', ''))
            
            if policy_id and policy_id not in seen_ids:
                seen_ids.add(policy_id)
                unique_policies.append(policy)
            elif not policy_id:
                # For policies without _id, use a fallback key
                fallback_key = f"{policy.get('country', '')}-{policy.get('policyArea', '')}-{policy.get('policyName', policy.get('name', ''))}-{policy.get('moved_to_master_at', '')}"
                if fallback_key not in seen_ids:
                    seen_ids.add(fallback_key)
                    unique_policies.append(policy)
        
        # Apply limit
        final_policies = unique_policies[:limit]
        
        logger.info(f"Public master policies: {len(master_policies)} from master + {len(temp_policies)} from temp = {len(final_policies)} total unique (removed {len(all_policies) - len(final_policies)} duplicates)")
        
        return {
            "success": True,
            "policies": final_policies,
            "total_count": len(final_policies),
            "sources": {
                "master_db": len(master_policies),
                "temp_approved": len(temp_policies),
                "total_unique": len(final_policies),
                "duplicates_removed": len(all_policies) - len(final_policies),
                "deduplication_method": "mongodb_id_primary"
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching public master policies: {str(e)}")
        return {
            "success": False,
            "policies": [],
            "total_count": 0,
            "error": str(e)
        }

async def get_master_policy_statistics():
    """Get statistics for master policies"""
    try:
        # Country distribution
        country_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        country_stats = {}
        async for doc in master_policies_collection.aggregate(country_pipeline):
            country_stats[doc["_id"]] = doc["count"]
        
        # Policy area distribution
        area_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$policyArea", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        area_stats = {}
        async for doc in master_policies_collection.aggregate(area_pipeline):
            area_stats[doc["_id"]] = doc["count"]
        
        return {
            "success": True,
            "country_stats": country_stats,
            "area_stats": area_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting master policy statistics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Debugging and maintenance endpoints
@app.get("/api/debug/remove-duplicates")
async def debug_remove_duplicates():
    """Debug endpoint to remove duplicate policies"""
    try:
        # Group by policy name and country, then count
        pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {
                "_id": {
                    "policyName": "$policyName",
                    "country": "$country"
                },
                "count": {"$sum": 1},
                "docs": {"$push": "$$ROOT"}
            }},
            {"$match": {"count": { "$gt": 1 }}}
        ]
        
        duplicates_found = 0
        duplicates_removed = 0
        
        async for group in master_policies_collection.aggregate(pipeline):
            duplicates_found += group["count"] - 1
            
            # Sort by moved_to_master_at and keep the first one (oldest)
            docs = sorted(group["docs"], key=lambda x: x.get("moved_at", datetime.min))
            
            # Remove all but the first document
            for doc in docs[1:]:
                await master_policies_collection.delete_one({"_id": doc["id"]})
                duplicates_removed += 1
        
        return {
            "success": True,
            "duplicates_found": duplicates_found,
            "duplicates_removed": duplicates_removed,
            "message": f"Removed {duplicates_removed} duplicate policies"
        }
    
    except Exception as e:
        logger.error(f"Error removing duplicates: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "duplicates_removed": 0
        }

@app.get("/api/debug/policy-counts")
async def debug_policy_counts():
    """Debug endpoint to see exact policy counts"""
    try:
        # Count all master policies
        total_master = await master_policies_collection.count_documents({})
        active_master = await master_policies_collection.count_documents({"master_status": "active"})
        
        # Count by country
        country_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        country_counts = []
        async for doc in master_policies_collection.aggregate(country_pipeline):
            country_counts.append({"country": doc["_id"], "count": doc["count"]})
        
        # Sample policies for inspection
        sample_policies = []
        async for doc in master_policies_collection.find({"master_status": "active"}).limit(5):
            sample = convert_objectid(doc)
            sample_policies.append({
                "id": sample.get("_id"),
                "country": sample.get("country"),
                "policyArea": sample.get("policyArea"),
                "policyName": sample.get("policyName"),
                "moved_at": sample.get("moved_to_master_at")
            })
        
        return {
            "total_master_policies": total_master,
            "active_master_policies": active_master,
            "inactive_master_policies": total_master - active_master,
            "country_counts": country_counts,
            "sample_policies": sample_policies
        }
    
    except Exception as e:
        logger.error(f"Error getting policy counts: {str(e)}")
        return {"error": str(e)}

@app.get("/api/public/master-policies-no-dedup")
async def get_master_policies_no_deduplication(
    limit: int = Query(1000, ge=1, le=1000),
    country: str = None,
    area: str = None
):
    """Temporary endpoint with NO deduplication - shows all policies"""
    try:
        master_filter = {"master_status": "active"}
        
        if country:
            master_filter["country"] = country
        if area:
            master_filter["policyArea"] = area
        
        # Get ALL policies without any deduplication
        all_policies = []
        async for doc in master_policies_collection.find(master_filter).limit(limit):
            policy_dict = convert_objectid(doc)
            policy_dict["name"] = policy_dict.get("policyName", "Unnamed Policy")
            policy_dict["area_id"] = policy_dict.get("policyArea")
            all_policies.append(policy_dict)
        
        logger.info(f"Master policies (no dedup): {len(all_policies)} total")
        
        return {
            "success": True,
            "policies": all_policies,
            "total_count": len(all_policies),
            "message": "No deduplication applied"
        }
    
    except Exception as e:
        logger.error(f"Error fetching policies: {str(e)}")
        return {
            "success": False,
            "policies": [],
            "total_count": 0,
            "error": str(e)
        }

@app.get("/api/debug/policy-data-analysis")
async def debug_policy_data_analysis():
    """Comprehensive analysis of policy data in database"""
    try:
        # Check master policies
        master_total = await master_policies_collection.count_documents({})
        master_active = await master_policies_collection.count_documents({"master_status": "active"})
        
        # Check for different field variations in master
        master_samples = []
        async for doc in master_policies_collection.find({}).limit(5):
            sample = convert_objectid(doc)
            master_samples.append({
                "country": sample.get("country"),
                "policyArea": sample.get("policyArea"),
                "policyName": sample.get("policyName"),
                "name": sample.get("name"),
                "master_status": sample.get("master_status"),
                "visibility": sample.get("visibility"),
                "moved_to_master_at": sample.get("moved_to_master_at"),
                "has_visibility_field": "visibility" in sample
            })
        
        # Check temp submissions
        temp_total = await temp_submissions_collection.count_documents({})
        temp_approved = 0
        temp_samples = []
        
        async for submission in temp_submissions_collection.find({}).limit(3):
            sample = convert_objectid(submission)
            temp_samples.append({
                "country": sample.get("country"),
                "submission_status": sample.get("submission_status"),
                "policyAreas_type": type(sample.get("policyAreas", {})).__name__,
                "has_policyInitiatives": "policyInitiatives" in sample,
                "created_at": sample.get("created_at")
            })
            
            # Count approved policies in this submission
            if "policyAreas" in sample:
                policy_areas = sample["policyAreas"]
                if isinstance(policy_areas, list):
                    for area in policy_areas:
                        for policy in area.get("policies", []):
                            if policy.get("status") == "approved":
                                temp_approved += 1
                elif isinstance(policy_areas, dict):
                    for area_id, policies in policy_areas.items():
                        if isinstance(policies, list):
                            for policy in policies:
                                if policy.get("status") == "approved":
                                    temp_approved += 1
        
        # Check field variations
        field_analysis = {}
        async for doc in master_policies_collection.find({}).limit(100):
            for field in ["visibility", "master_status", "policyArea", "country", "policyName"]:
                if field not in field_analysis:
                    field_analysis[field] = {"present": 0, "missing": 0, "values": set()}
                
                if field in doc:
                    field_analysis[field]["present"] += 1
                    if doc[field]:
                        field_analysis[field]["values"].add(str(doc[field])[:50])  # Limit string length
                else:
                    field_analysis[field]["missing"] += 1
        
        # Convert sets to lists for JSON serialization
        for field in field_analysis:
            field_analysis[field]["unique_values"] = list(field_analysis[field]["values"])[:10]  # Limit to 10 values
            del field_analysis[field]["values"]
        
        return {
            "master_policies": {
                "total": master_total,
                "active": master_active,
                "inactive": master_total - master_active,
                "samples": master_samples
            },
            "temp_submissions": {
                "total": temp_total,
                "approved_policies_count": temp_approved,
                "samples": temp_samples
            },
            "field_analysis": field_analysis,
            "recommendations": [
                "Remove visibility filter completely" if any(f["missing"] > 0 for f in field_analysis.values()) else "All fields present",
                "Check data migration" if temp_approved > 0 else "No unmigrated approved policies",
                "Update deduplication logic" if master_total != master_active else "All master policies are active"
            ]
        }
    
    except Exception as e:
        logger.error(f"Debug analysis error: {str(e)}")
        return {"error": str(e)}

@app.post("/api/admin/fix-visibility")
async def fix_visibility_issue(admin_user: dict = Depends(get_admin_user)):
    """Remove visibility restrictions from all active master policies"""
    try:
        # Remove visibility field from all active policies
        result = await master_policies_collection.update_many(
            {"master_status": "active"},
            {"$unset": {"visibility": ""}}
        )
        
        # Also ensure all are marked as active
        result2 = await master_policies_collection.update_many(
            {"master_status": {"$exists": False}},
            {"$set": {"master_status": "active"}}
        )
        
        return {
            "success": True,
            "removed_visibility_from": result.modified_count,
            "set_active_status": result2.modified_count,
            "message": "Fixed visibility restrictions"
        }
    
    except Exception as e:
        logger.error(f"Fix visibility error: {str(e)}")
        return {"success": False, "error": str(e)}

# Enhanced utility endpoints
@app.get("/api/countries")
async def get_countries():
    """Get list of all available countries"""
    return {"countries": COUNTRIES, "total": len(COUNTRIES)}

@app.get("/api/policy-areas")
async def get_policy_areas():
    """Get list of all policy areas with enhanced metadata"""
    return {"policy_areas": POLICY_AREAS, "total": len(POLICY_AREAS)}

# for debug historical data
@app.get("/api/debug/master-policies-timeline")
async def debug_master_policies_timeline():
    """Debug endpoint to check policies by date"""
    try:
        # Get policies grouped by date
        date_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$moved_to_master_at"
                    }
                },
                "count": {"$sum": 1},
                "countries": {"$addToSet": "$country"},
                "sample_policies": {"$push": "$policyName"}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 10}
        ]
        
        timeline = []
        async for doc in master_policies_collection.aggregate(date_pipeline):
            timeline.append({
                "date": doc["_id"],
                "policy_count": doc["count"],
                "countries": doc["countries"],
                "sample_policies": doc["sample_policies"][:3]  # First 3 policies
            })
        
        # Get total stats
        total_active = await master_policies_collection.count_documents({"master_status": "active"})
        
        # Check for policies without visibility field
        no_visibility = await master_policies_collection.count_documents({
            "master_status": "active",
            "visibility": {"$exists": False}
        })
        
        # Check for policies with different visibility values
        visibility_stats = {}
        async for doc in master_policies_collection.aggregate([
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$visibility", "count": {"$sum": 1}}}
        ]):
            visibility_stats[doc["_id"] or "null"] = doc["count"]
        
        return {
            "total_active_policies": total_active,
            "policies_without_visibility": no_visibility,
            "visibility_distribution": visibility_stats,
            "recent_timeline": timeline
        }
    
    except Exception as e:
        logger.error(f"Debug timeline error: {str(e)}")
        return {"error": str(e)}

#see db
@app.get("/api/debug/database-content")
async def debug_database_content():
    """Debug endpoint to see all database content"""
    try:
        # Check all collections
        collections_info = {}
        
        # Check users
        users_count = await users_collection.count_documents({})
        collections_info["users_collection"] = {
            "count": users_count,
            "sample": await users_collection.find_one({}) if users_count > 0 else None
        }
        
        # Check temp_submissions
        temp_count = await temp_submissions_collection.count_documents({})
        collections_info["temp_submissions_collection"] = {
            "count": temp_count,
            "sample": await temp_submissions_collection.find_one({}) if temp_count > 0 else None
        }
        
        # Check master_policies
        master_count = await master_policies_collection.count_documents({})
        collections_info["master_policies_collection"] = {
            "count": master_count,
            "sample": await master_policies_collection.find_one({}) if master_count > 0 else None
        }
        
        # Check for any other collections that might contain policies
        all_collections = await db.list_collection_names()
        collections_info["all_collections"] = all_collections
        
        # Check for any documents with policy-like fields
        policy_like_docs = []
        for collection_name in all_collections:
            if collection_name not in ["users", "temp_submissions", "master_policies", "admin_actions", "files", "otp_codes"]:
                collection = db[collection_name]
                count = await collection.count_documents({})
                if count > 0:
                    sample = await collection.find_one({})
                    policy_like_docs.append({
                        "collection": collection_name,
                        "count": count,
                        "sample": convert_objectid(sample)
                    })
        
        collections_info["other_collections"] = policy_like_docs
        
        return {
            "database_name": "ai_policy_database",
            "collections": collections_info,
            "total_collections": len(all_collections)
        }
    
    except Exception as e:
        logger.error(f"Error checking database content: {str(e)}")
        return {"error": str(e)}
    
# format conversion
@app.post("/api/admin/migrate-old-data")
async def migrate_old_data(admin_user: dict = Depends(get_admin_user)):
    """Migrate old policy data to new master format"""
    try:
        migrated_count = 0
        
        # Check for old format submissions in temp_submissions
        async for submission in temp_submissions_collection.find({}):
            logger.info(f"Processing submission: {submission.get('_id')}")
            
            # Handle different data formats
            if "policyAreas" in submission:
                # New format
                policy_areas = submission["policyAreas"]
                if isinstance(policy_areas, list):
                    # Current format: list of {area_id, area_name, policies}
                    for area in policy_areas:
                        area_id = area.get("area_id")
                        policies = area.get("policies", [])
                        
                        for policy_index, policy in enumerate(policies):
                            if policy.get("status") == "approved":
                                await migrate_policy_to_master(submission, area_id, policy_index, policy)
                                migrated_count += 1
                
                elif isinstance(policy_areas, dict):
                    # Old format: {area_id: [policies]}
                    for area_id, policies in policy_areas.items():
                        if isinstance(policies, list):
                            for policy_index, policy in enumerate(policies):
                                if policy.get("status") == "approved":
                                    await migrate_policy_to_master(submission, area_id, policy_index, policy)
                                    migrated_count += 1
            
            # Handle even older formats
            elif "policyInitiatives" in submission:
                policies = submission["policyInitiatives"]
                if isinstance(policies, list):
                    for policy_index, policy in enumerate(policies):
                        area_id = policy.get("policyArea", "unknown")
                        if policy.get("status") == "approved":
                            await migrate_policy_to_master(submission, area_id, policy_index, policy)
                            migrated_count += 1
        
        return {
            "success": True,
            "migrated_policies": migrated_count,
            "message": f"Successfully migrated {migrated_count} policies to master database"
        }
    
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "migrated_policies": 0
        }

@app.post("/api/admin/repair-historical-data")
async def repair_historical_data(admin_user: dict = Depends(get_admin_user)):
    """Repair historical data that might be missing primary keys"""
    try:
        repaired_count = 0
        
        # Find policies without proper primary keys
        async for policy in master_policies_collection.find({
            "master_status": "active",
            "$or": [
                {"original_submission_id": {"$exists": False}},
                {"policy_index": {"$exists": False}},
                {"policyArea": {"$exists": False}}
            ]
        }):
            policy_id = policy["_id"]
            updates = {}
            
            # Generate missing fields
            if not policy.get("original_submission_id"):
                # Create a synthetic submission ID based on policy content
                synthetic_id = f"legacy_{policy.get('country', 'unknown')}_{policy.get('policyArea', 'unknown')}"
                updates["original_submission_id"] = synthetic_id
            
            if policy.get("policy_index") is None:
                # Use a timestamp-based index for ordering
                created_time = policy.get("moved_to_master_at", datetime.utcnow())
                updates["policy_index"] = int(created_time.timestamp())
            
            if not policy.get("policyArea"):
                # Try to infer from area_name or set as unknown
                area_name = policy.get("area_name", "")
                inferred_area = next((area["id"] for area in POLICY_AREAS if area["name"] == area_name), "unknown")
                updates["policyArea"] = inferred_area
            
            # Apply updates
            if updates:
                await master_policies_collection.update_one(
                    {"_id": policy_id},
                    {"$set": updates}
                )
                repaired_count += 1
                logger.info(f"Repaired policy: {policy.get('policyName')} with updates: {updates}")
        
        return {
            "success": True,
            "repaired_policies": repaired_count,
            "message": f"Successfully repaired {repaired_count} historical policies"
        }
    
    except Exception as e:
        logger.error(f"Error repairing historical data: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "repaired_policies": 0
        }

async def migrate_policy_to_master(submission: dict, area_id: str, policy_index: int, policy: dict):
    """Helper function to migrate a single policy to master database"""
    try:
        # Check if already exists
        existing = await master_policies_collection.find_one({
            "original_submission_id": str(submission["_id"]),
            "policyArea": area_id,
            "policy_index": policy_index
        })
        
        if existing:
            logger.info(f"Policy already exists in master: {policy.get('policyName')}")
            return
        
        # Get area info
        area_info = next((area for area in POLICY_AREAS if area["id"] == area_id), None)
        user_count = await users_collection.count_documents({})
        submission_count = await temp_submissions_collection.count_documents({})
        master_count = await master_policies_collection.count_documents({"master_status": "active"})
        
        return {
            "status": "healthy", 
            "database": "connected", 
            "timestamp": datetime.utcnow(),
            "version": "4.0.0",
            "statistics": {
                "total_users": user_count,
                "total_submissions": submission_count,
                "active_policies": master_count
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.get("/")
async def root():
    """Enhanced root endpoint"""
    return {
        "message": "Enhanced AI Policy Database API with Database-Only Chatbot", 
        "version": "4.1.0",
        "status": "operational",
        "features": [
            "🔐 Complete Authentication System with Email Verification",
            "🤖 Database-Only AI Policy Chatbot (NEW!)",
            "🚀 Enhanced Google OAuth Integration", 
            "📝 Multi-Policy Area Submission System",
            "🗺️ Real-time Map Visualization",
            "👨‍💼 Advanced Admin Dashboard",
            "📊 Policy Scoring and Analytics",
            "📧 Improved Email System with Templates",
            "🔄 Automatic Policy-to-Master Migration",
            "🌍 Enhanced Country and Area Support",
            "⚡ Performance Optimizations",
            "🔍 Advanced Database Search and Filtering"
        ],
        "chatbot_features": [
            "🔍 Country-based policy search",
            "📋 Policy area exploration", 
            "📝 Policy name search",
            "🌍 Complete database coverage",
            "💬 Natural language queries",
            "📊 Real-time policy statistics",
            "🚫 Database-only responses (no external AI generation)"
        ],
        "endpoints": {
            "authentication": "/api/auth/*",
            "submissions": "/api/submit-enhanced-form",
            "admin": "/api/admin/*",
            "policies": "/api/public/master-policies",
            "chatbot": "/api/chat",
            "health": "/api/health"
        }
    }

@app.post("/api/auth/admin-login")
async def admin_login(login_data: UserLogin):
    """Admin login endpoint with enhanced security"""
    try:
        # Find user
        user = await users_collection.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        # Check if user is admin
        if not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Access denied. Admin privileges required.")
        
        # Verify password
        if not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        # Update last login
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Log admin action
        admin_log = {
            "action": "admin_login",
            "admin_id": str(user["_id"]),
            "admin_email": user["email"],
            "timestamp": datetime.utcnow(),
            "ip_address": "unknown"  # You can get this from request headers if needed
        }
        await admin_actions_collection.insert_one(admin_log)
        
        logger.info(f"Admin logged in successfully: {login_data.email}")
        
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
                "is_super_admin": user.get("is_super_admin", False),
                "is_verified": user.get("is_verified", False)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Admin login failed: {str(e)}")

@app.get("/api/admin/submissions")
async def get_admin_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query("all"),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all submissions for admin review with pagination"""
    try:
        # Build filter
        filter_dict = {}
        if status != "all":
            filter_dict["submission_status"] = status
        
        # Calculate pagination
        skip_count = (page - 1) * limit
        
        # Get submissions with pagination
        submissions_cursor = temp_submissions_collection.find(filter_dict).sort("created_at", -1).skip(skip_count).limit(limit)
        submissions = []
        
        async for submission in submissions_cursor:
            submission = convert_objectid(submission)
            submissions.append(submission)
        
        # Get total count for pagination
        total_count = await temp_submissions_collection.count_documents(filter_dict)
        total_pages = (total_count + limit - 1) // limit
        
        logger.info(f"Admin fetched {len(submissions)} submissions (page {page}/{total_pages})")
        
        return {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error fetching admin submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching submissions: {str(e)}")

@app.get("/api/admin/statistics")
async def get_admin_statistics(admin_user: dict = Depends(get_admin_user)):
    """Get comprehensive admin statistics"""
    try:
        # Count submissions by status
        pending_submissions = await temp_submissions_collection.count_documents({"submission_status": "pending"})
        partially_approved = await temp_submissions_collection.count_documents({"submission_status": "partially_approved"})
        fully_approved = await temp_submissions_collection.count_documents({"submission_status": "fully_approved"})
        under_review = await temp_submissions_collection.count_documents({"submission_status": "under_review"})
        
        # Count total users
        total_users = await users_collection.count_documents({})
        verified_users = await users_collection.count_documents({"is_verified": True})
        
        # Count master policies
        total_approved_policies = await master_policies_collection.count_documents({"master_status": "active"})
        
        # Count total submissions
        total_submissions = await temp_submissions_collection.count_documents({})
        
        # Country distribution
        country_pipeline = [
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        country_stats = {}
        async for doc in temp_submissions_collection.aggregate(country_pipeline):
            country_stats[doc["_id"]] = doc["count"]
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_submissions = await temp_submissions_collection.count_documents({
            "created_at": {"$gte": seven_days_ago}
        })
        
        statistics = {
            "pending_submissions": pending_submissions,
            "partially_approved": partially_approved,
            "fully_approved": fully_approved,
            "under_review": under_review,
            "total_users": total_users,
            "verified_users": verified_users,
            "total_approved_policies": total_approved_policies,
            "total_submissions": total_submissions,
            "recent_submissions": recent_submissions,
            "country_distribution": country_stats,
            "success": True
        }
        
        logger.info(f"Admin statistics fetched: {total_submissions} total submissions, {total_approved_policies} approved policies")
        
        return statistics
    
    except Exception as e:
        logger.error(f"Error fetching admin statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@app.post("/api/admin/move-to-master")
async def move_to_master(
    request: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Move approved policy to master database"""
    try:
        submission_id = request.get("submission_id")
        area_id = request.get("area_id")
        policy_index = request.get("policy_index")
        
        if not all([submission_id, area_id, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Find the submission
        submission = await temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Call the internal function we already have
        await move_policy_to_master_internal(submission, area_id, policy_index, admin_user)
        
        return {"success": True, "message": "Policy moved to master database successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving policy to master: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error moving policy: {str(e)}")

@app.delete("/api/admin/delete-policy")
async def delete_policy(
    request: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a policy from a submission"""
    try:
        submission_id = request.get("submission_id")
        policy_area = request.get("policy_area")
        policy_index = request.get("policy_index")
        
        if not all([submission_id, policy_area, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Find the submission
        submission = await temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Find and remove the policy
        policy_areas = submission.get("policyAreas", [])
        policy_found = False
        
        for i, area in enumerate(policy_areas):
            if area.get("area_id") == policy_area:
                if policy_index < len(area.get("policies", [])):
                    # Remove the policy
                    del policy_areas[i]["policies"][policy_index]
                    policy_found = True
                    
                    # If no policies left in this area, remove the area
                    if not policy_areas[i]["policies"]:
                        del policy_areas[i]
                    
                    break
        
        if not policy_found:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Update the submission
        await temp_submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {
                "policyAreas": policy_areas,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Log admin action
        admin_log = {
            "action": "delete_policy",
            "submission_id": submission_id,
            "policy_area": policy_area,
            "policy_index": policy_index,
            "admin_id": str(admin_user["_id"]),
            "admin_email": admin_user["email"],
            "timestamp": datetime.utcnow()
        }
        await admin_actions_collection.insert_one(admin_log)
        
        # Update overall submission status
        await update_submission_status(submission_id)
        
        logger.info(f"Policy deleted by admin {admin_user['email']}")
        return {"success": True, "message": "Policy deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting policy: {str(e)}")

@app.put("/api/admin/edit-policy")
async def edit_policy(
    request: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Edit a policy in a submission"""
    try:
        submission_id = request.get("submission_id")
        policy_area = request.get("policy_area")
        policy_index = request.get("policy_index")
        updated_policy = request.get("updated_policy")
        
        if not all([submission_id, policy_area, policy_index is not None, updated_policy]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Find the submission
        submission = await temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Find and update the policy
        policy_areas = submission.get("policyAreas", [])
        policy_found = False
        
        for i, area in enumerate(policy_areas):
            if area.get("area_id") == policy_area:
                if policy_index < len(area.get("policies", [])):
                    # Update the policy
                    policy_areas[i]["policies"][policy_index] = {
                        **policy_areas[i]["policies"][policy_index],
                        **updated_policy,
                        "updated_at": datetime.utcnow(),
                        "updated_by": admin_user["email"]
                    }
                    policy_found = True
                    break
        
        if not policy_found:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Update the submission
        await temp_submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {
                "policyAreas": policy_areas,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Log admin action
        admin_log = {
            "action": "edit_policy",
            "submission_id": submission_id,
            "policy_area": policy_area,
            "policy_index": policy_index,
            "admin_id": str(admin_user["_id"]),
            "admin_email": admin_user["email"],
            "timestamp": datetime.utcnow(),
            "changes": updated_policy
        }
        await admin_actions_collection.insert_one(admin_log)
        
        logger.info(f"Policy edited by admin {admin_user['email']}")
        return {"success": True, "message": "Policy updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error editing policy: {str(e)}")

# Add this new public endpoint for the world map
@app.get("/api/public/master-policies")
async def get_public_master_policies(
    limit: int = Query(1000, ge=1, le=1000),
    country: str = None,
    area: str = None
):
    """Enhanced public endpoint for master policies with better country stats"""
    try:
        filter_dict = {"master_status": "active", "visibility": "public"}
        
        if country:
            filter_dict["country"] = country
        if area:
            filter_dict["policyArea"] = area
        
        # Get policies with enhanced information
        projection = {
            "country": 1,
            "policyArea": 1,
            "area_name": 1,
            "area_icon": 1,
            "area_color": 1,
            "policyName": 1,
            "policyId": 1,
            "policyDescription": 1,
            "status": 1,
            "master_status": 1,
            "policy_score": 1,
            "completeness_score": 1,
            "moved_to_master_at": 1,
            "implementation": 1,
            "evaluation": 1,
            "participation": 1,
            "alignment": 1,
            "targetGroups": 1,
            "visibility": 1
        }
        
        policies_cursor = master_policies_collection.find(
            filter_dict, 
            projection
        ).limit(limit).sort("moved_to_master_at", -1)
        
        policies = []
        async for doc in policies_cursor:
            policy_dict = convert_objectid(doc)
            # Ensure consistent field names
            policy_dict["name"] = policy_dict.get("policyName", "Unnamed Policy")
            policy_dict["area_id"] = policy_dict.get("policyArea")
            policies.append(policy_dict)
        
        # Get total count
        total_count = await master_policies_collection.count_documents(filter_dict)
        
        logger.info(f"Public master policies fetched: {len(policies)} policies")
        
        return {
            "success": True,
            "policies": policies,
            "total_count": total_count
        }
    
    except Exception as e:
        logger.error(f"Error fetching public master policies: {str(e)}")
        return {
            "success": False,
            "policies": [],
            "total_count": 0,
            "error": str(e)
        }
# Also add a specific endpoint for country policy details (public)
@app.get("/api/public/country-policies/{country_name}")
async def get_country_policies_detailed(country_name: str):
    """Get detailed policies for a specific country with proper grouping"""
    try:
        filter_dict = {
            "master_status": "active",
            "visibility": "public", 
            "country": country_name
        }
        
        # Get all policies for the country
        policies_cursor = master_policies_collection.find(filter_dict).sort("moved_to_master_at", -1)
        policies = []
        
        async for doc in policies_cursor:
            policy_dict = convert_objectid(doc)
            # Ensure compatibility with frontend
            policy_dict["name"] = policy_dict.get("policyName", "Unnamed Policy")
            policy_dict["policy_name"] = policy_dict.get("policyName", "Unnamed Policy") 
            policy_dict["type"] = policy_dict.get("area_name", policy_dict.get("policyArea", "Unknown"))
            policy_dict["year"] = policy_dict.get("implementation", {}).get("deploymentYear", "TBD")
            policies.append(policy_dict)
        
        # Group by policy area
        policies_by_area = {}
        for policy in policies:
            area_id = policy.get("policyArea", "unknown")
            area_name = policy.get("area_name", area_id)
            
            if area_id not in policies_by_area:
                policies_by_area[area_id] = {
                    "area_id": area_id,
                    "area_name": area_name,
                    "area_icon": policy.get("area_icon", "📄"),
                    "policies": []
                }
            policies_by_area[area_id]["policies"].append(policy)
        
        return {
            "success": True,
            "country": country_name,
            "total_policies": len(policies),
            "policy_areas": list(policies_by_area.values())
        }
    
    except Exception as e:
        logger.error(f"Error fetching country policies: {str(e)}")
        return {
            "success": False,
            "country": country_name, 
            "total_policies": 0,
            "policy_areas": [],
            "error": str(e)
        }   
# Add this at the end of main.py

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Database-only chat endpoint"""
    try:
        response = await chat_endpoint(request)
        return response
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/api/chat/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        response = await get_conversation_endpoint(conversation_id)
        return response
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@app.delete("/api/chat/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    try:
        response = await delete_conversation_endpoint(conversation_id)
        return response
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@app.get("/api/chat/conversations")
async def get_conversations(limit: int = 20):
    """Get list of conversations"""
    try:
        response = await get_conversations_endpoint(limit)
        return response
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@app.get("/api/chat/policy-search")
async def policy_search(q: str):
    """Enhanced policy search for chatbot sidebar"""
    try:
        response = await policy_search_endpoint(q)
        return response
    except Exception as e:
        logger.error(f"Policy search error: {str(e)}")
        return {"policies": []}

@app.get("/api/debug/chatbot-test")
async def test_chatbot():
    """Test chatbot functionality"""
    try:
        from chatbot import chatbot_instance
        
        if not chatbot_instance:
            return {"error": "Chatbot not initialized"}
        
        # Test basic searches
        test_results = {}
        
        # Test country search
        countries = await chatbot_instance.get_countries_list()
        test_results["countries_count"] = len(countries)
        test_results["sample_countries"] = countries[:5]
        
        # Test policy areas
        areas = await chatbot_instance.get_policy_areas_list()
        test_results["areas_count"] = len(areas)
        test_results["sample_areas"] = areas[:5]
        
        # Test policy search
        if countries:
            first_country = countries[0]
            policies = await chatbot_instance.search_policies_by_country(first_country)
            test_results["sample_country_policies"] = len(policies)
            test_results["sample_country"] = first_country
        
        return {
            "chatbot_status": "initialized",
            "database_connection": "ok",
            "test_results": test_results
        }
    
    except Exception as e:
        logger.error(f"Chatbot test error: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")