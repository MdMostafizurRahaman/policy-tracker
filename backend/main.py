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

# Load environment variables
load_dotenv()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# JWT and Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME",)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD",)
FROM_EMAIL = os.getenv("FROM_EMAIL")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Initialize FastAPI app
app = FastAPI(title="Enhanced AI Policy Database API", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://policy-tracker-f.onrender.com", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.ai_policy_database

# Collections
users_collection = db.users
temp_submissions_collection = db.temp_submissions
master_policies_collection = db.master_policies
admin_actions_collection = db.admin_actions
files_collection = db.files
otp_collection = db.otp_codes

# Legacy collections for backward compatibility
legacy_temp_policies_collection = db.temp_policies
legacy_policies_collection = db.policyInitiatives

# Security
security = HTTPBearer()

# Policy Areas Configuration (10 main areas)
POLICY_AREAS = [
    {
        "id": "ai-safety",
        "name": "AI Safety",
        "description": "Policies ensuring AI systems are safe and beneficial",
        "icon": "shield",
        "color": "from-red-500 to-pink-600"
    },
    {
        "id": "cyber-safety",
        "name": "CyberSafety",
        "description": "Cybersecurity and digital safety policies",
        "icon": "security",
        "color": "from-blue-500 to-cyan-600"
    },
    {
        "id": "digital-education",
        "name": "Digital Education",
        "description": "Educational technology and digital literacy policies",
        "icon": "education",
        "color": "from-green-500 to-emerald-600"
    },
    {
        "id": "digital-inclusion",
        "name": "Digital Inclusion",
        "description": "Bridging the digital divide and ensuring equal access",
        "icon": "inclusion",
        "color": "from-purple-500 to-indigo-600"
    },
    {
        "id": "digital-leisure",
        "name": "Digital Leisure",
        "description": "Gaming, entertainment, and digital recreation policies",
        "icon": "entertainment",
        "color": "from-yellow-500 to-orange-600"
    },
    {
        "id": "disinformation",
        "name": "(Dis)Information",
        "description": "Combating misinformation and promoting truth",
        "icon": "information",
        "color": "from-gray-500 to-slate-600"
    },
    {
        "id": "digital-work",
        "name": "Digital Work",
        "description": "Future of work and digital employment policies",
        "icon": "work",
        "color": "from-teal-500 to-blue-600"
    },
    {
        "id": "mental-health",
        "name": "Mental Health",
        "description": "Digital wellness and mental health policies",
        "icon": "health",
        "color": "from-pink-500 to-rose-600"
    },
    {
        "id": "physical-health",
        "name": "Physical Health",
        "description": "Healthcare technology and physical wellness policies",
        "icon": "medical",
        "color": "from-emerald-500 to-green-600"
    },
    {
        "id": "social-media-gaming",
        "name": "Social Media/Gaming Regulation",
        "description": "Social media platforms and gaming regulation",
        "icon": "social",
        "color": "from-indigo-500 to-purple-600"
    }
]

# Load countries data
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

# Pydantic Models
class UserRegistration(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    confirmPassword: str
    country: str

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

class PasswordReset(BaseModel):
    email: EmailStr
    otp: str
    newPassword: str
    confirmPassword: str

class SubPolicy(BaseModel):
    policyName: str
    policyId: str = ""
    policyDescription: str = ""
    targetGroups: List[str] = []
    policyFile: Optional[Dict] = None
    policyLink: str = ""
    implementation: Dict = {}
    evaluation: Dict = {}
    participation: Dict = {}
    alignment: Dict = {}
    status: str = "pending"
    admin_notes: str = ""

class PolicyArea(BaseModel):
    area_id: str
    area_name: str
    policies: List[SubPolicy] = []

class EnhancedSubmission(BaseModel):
    user_id: str
    user_email: str
    user_name: str
    country: str
    policyAreas: List[PolicyArea]
    submission_status: str = "pending"

class PolicyStatusUpdate(BaseModel):
    submission_id: str
    area_id: str
    policy_index: int
    status: str
    admin_notes: str = ""

# Utility Functions
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

def pydantic_to_dict(obj):
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
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

async def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await users_collection.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return convert_objectid(user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# File handling
async def save_file_to_db(file: UploadFile, metadata: Dict = None) -> str:
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
        return str(result.inserted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

async def get_file_from_db(file_id: str):
    try:
        file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        return file_doc
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

# Database Migration Function
async def migrate_legacy_data():
    """Migrate existing data to new schema while preserving it"""
    try:
        # Check if migration has already been done
        migration_check = await db.migrations.find_one({"name": "legacy_to_enhanced"})
        if migration_check:
            return
        
        # Migrate legacy submissions
        legacy_submissions = await legacy_temp_policies_collection.find({}).to_list(None)
        
        for submission in legacy_submissions:
            # Create user if doesn't exist
            user_email = submission.get("user_email", "legacy@user.com")
            existing_user = await users_collection.find_one({"email": user_email})
            
            if not existing_user:
                user_doc = {
                    "firstName": submission.get("user_name", "Legacy").split()[0],
                    "lastName": " ".join(submission.get("user_name", "User").split()[1:]) or "User",
                    "email": user_email,
                    "password": hash_password("temporary123"),  # Temporary password
                    "country": submission.get("country", "Unknown"),
                    "is_admin": False,
                    "is_verified": True,
                    "created_at": submission.get("created_at", datetime.utcnow()),
                    "updated_at": datetime.utcnow(),
                    "is_legacy": True
                }
                user_result = await users_collection.insert_one(user_doc)
                user_id = str(user_result.inserted_id)
            else:
                user_id = str(existing_user["_id"])
            
            # Transform old policy structure to new structure
            new_submission = {
                "user_id": user_id,
                "user_email": user_email,
                "user_name": submission.get("user_name", "Legacy User"),
                "country": submission.get("country", "Unknown"),
                "policyAreas": [],
                "submission_status": submission.get("submission_status", "pending"),
                "created_at": submission.get("created_at", datetime.utcnow()),
                "updated_at": submission.get("updated_at", datetime.utcnow()),
                "is_legacy": True
            }
            
            # Convert old policyInitiatives to new structure
            old_policies = submission.get("policyInitiatives", [])
            for policy in old_policies:
                policy_area = policy.get("policyArea", "ai-safety")
                
                # Find or create policy area
                area_found = False
                for area in new_submission["policyAreas"]:
                    if area["area_id"] == policy_area:
                        area["policies"].append(policy)
                        area_found = True
                        break
                
                if not area_found:
                    area_info = next((area for area in POLICY_AREAS if area["id"] == policy_area), POLICY_AREAS[0])
                    new_submission["policyAreas"].append({
                        "area_id": policy_area,
                        "area_name": area_info["name"],
                        "policies": [policy]
                    })
            
            # Insert migrated submission
            await temp_submissions_collection.insert_one(new_submission)
        
        # Mark migration as complete
        await db.migrations.insert_one({
            "name": "legacy_to_enhanced",
            "completed_at": datetime.utcnow(),
            "legacy_submissions_migrated": len(legacy_submissions)
        })
        
        print(f"Migration completed: {len(legacy_submissions)} submissions migrated")
        
    except Exception as e:
        print(f"Migration error: {e}")

# Initialize super admin on startup
async def initialize_super_admin():
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
            print("Super admin created successfully")
        else:
            # Update password if changed
            if not verify_password(SUPER_ADMIN_PASSWORD, existing_admin["password"]):
                await users_collection.update_one(
                    {"email": SUPER_ADMIN_EMAIL},
                    {"$set": {"password": hash_password(SUPER_ADMIN_PASSWORD)}}
                )
            print("Super admin already exists")
    except Exception as e:
        print(f"Error initializing super admin: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    await initialize_super_admin()
    await migrate_legacy_data()

# Authentication Endpoints
@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    try:
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
        
        # Check for existing OTP
        existing_otp = await otp_collection.find_one({
            "email": user_data.email,
            "type": "email_verification",
            "expires_at": {"$gt": datetime.utcnow()}
        })
        if existing_otp:
            otp = existing_otp["otp"]
        else:
            # Always generate a new OTP and remove previous ones
            await otp_collection.delete_many({
                "email": user_data.email,
                "type": "email_verification"
            })
            otp = generate_otp()
            otp_doc = {
                "email": user_data.email,
                "otp": otp,
                "type": "email_verification",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10)  # 10 minutes validity
            }
            await otp_collection.insert_one(otp_doc)
        
        # Send verification email
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Welcome to AI Policy Tracker!</h2>
            <p>Hello {user_data.firstName},</p>
            <p>Thank you for registering with AI Policy Tracker. Your verification code is:</p>
            <div style="background: #f3f4f6; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                <h1 style="color: #1f2937; font-size: 32px; margin: 0; letter-spacing: 4px;">{otp}</h1>
            </div>
            <p style="color: #ef4444;"><strong>This code expires in 10 minutes.</strong></p>
            <p>If you didn't create an account, please ignore this email.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 14px;">Best regards,<br>AI Policy Tracker Team</p>
        </div>
        """
        await send_email(user_data.email, "Verify Your Email - AI Policy Tracker", email_body)
        
        return {
            "success": True,
            "message": "User registered successfully. Please check your email for verification code.",
            "user_id": str(result.inserted_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/verify-email")
async def verify_email(verification: OTPVerification):
    try:
        # Find OTP
        otp_doc = await otp_collection.find_one({
            "email": verification.email,
            "otp": verification.otp,
            "type": "email_verification",
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not otp_doc:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        
        # Update user as verified
        await users_collection.update_one(
            {"email": verification.email},
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
        )
        
        # Delete used OTP
        await otp_collection.delete_one({"_id": otp_doc["_id"]})
        
        return {"success": True, "message": "Email verified successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.post("/api/auth/login")
async def login_user(login_data: UserLogin):
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
            raise HTTPException(status_code=401, detail="Please verify your email first")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
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
                "is_admin": user.get("is_admin", False)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/google")
async def google_auth(auth_request: GoogleAuthRequest):
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            auth_request.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        
        email = idinfo['email']
        firstName = idinfo.get('given_name', '')
        lastName = idinfo.get('family_name', '')
        
        # Check if user exists
        user = await users_collection.find_one({"email": email})
        
        if not user:
            # Create new user
            user_doc = {
                "firstName": firstName,
                "lastName": lastName,
                "email": email,
                "password": hash_password(str(uuid.uuid4())),  # Random password for Google users
                "country": "Unknown",
                "is_admin": False,
                "is_verified": True,  # Google accounts are pre-verified
                "google_auth": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(user_doc)
            user_id = str(result.inserted_id)
        else:
            user_id = str(user["_id"])
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "firstName": firstName,
                "lastName": lastName,
                "email": email,
                "country": user.get("country", "Unknown") if user else "Unknown",
                "is_admin": user.get("is_admin", False) if user else False
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@app.post("/api/auth/forgot-password")
async def forgot_password(email_data: dict):
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check if user exists
        user = await users_collection.find_one({"email": email})
        if not user:
            # Don't reveal if email exists or not
            return {"success": True, "message": "If the email exists, a reset code has been sent"}
        
        # Check for existing OTP
        existing_otp = await otp_collection.find_one({
            "email": email,
            "type": "password_reset",
            "expires_at": {"$gt": datetime.utcnow()}
        })
        if existing_otp:
            otp = existing_otp["otp"]
        else:
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
        
        # Send reset email
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626;">Password Reset Request</h2>
            <p>Hello {user['firstName']},</p>
            <p>You requested to reset your password. Your reset code is:</p>
            <div style="background: #fef2f2; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; border: 1px solid #fecaca;">
                <h1 style="color: #991b1b; font-size: 32px; margin: 0; letter-spacing: 4px;">{otp}</h1>
            </div>
            <p style="color: #ef4444;"><strong>This code expires in 10 minutes.</strong></p>
            <p>If you didn't request this reset, please ignore this email.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 14px;">Best regards,<br>AI Policy Tracker Team</p>
        </div>
        """
        await send_email(email, "Password Reset Code - AI Policy Tracker", email_body)
        
        return {"success": True, "message": "Password reset code sent to your email"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

@app.post("/api/auth/reset-password")
async def reset_password(reset_data: PasswordReset):
    try:
        # Validate passwords match
        if reset_data.newPassword != reset_data.confirmPassword:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Find OTP
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
        await users_collection.update_one(
            {"email": reset_data.email},
            {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}}
        )
        
        # Delete used OTP
        await otp_collection.delete_one({"_id": otp_doc["_id"]})
        
        return {"success": True, "message": "Password reset successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

# File Upload Endpoint
@app.post("/api/upload-policy-file")
async def upload_policy_file(
    country: str = Form(...),
    area_id: str = Form(...),
    policy_index: int = Form(...),
    submission_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
        
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail="File type not supported")
        
        # Prepare metadata
        metadata = {
            "country": country,
            "area_id": area_id,
            "policy_index": policy_index,
            "submission_id": submission_id,
            "user_id": current_user["id"],
            "original_filename": file.filename
        }
        
        # Save file to database
        file_id = await save_file_to_db(file, metadata)
        
        return {
            "success": True, 
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size or 0,
            "content_type": file.content_type,
            "message": "File uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# Enhanced Submission Endpoint
@app.post("/api/submit-enhanced-form")
async def submit_enhanced_form(
    submission: EnhancedSubmission,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Validate user owns this submission
        if submission.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unauthorized submission")
        
        # Filter out empty policy areas
        filtered_policy_areas = []
        for area in submission.policyAreas:
            non_empty_policies = [
                policy for policy in area.policies 
                if policy.policyName and policy.policyName.strip()
            ]
            if non_empty_policies:
                area.policies = non_empty_policies
                filtered_policy_areas.append(area)
        
        if not filtered_policy_areas:
            raise HTTPException(status_code=400, detail="At least one policy must be provided")
        
        # Prepare submission document
        submission_dict = pydantic_to_dict(submission)
        submission_dict["policyAreas"] = filtered_policy_areas
        submission_dict["created_at"] = datetime.utcnow()
        submission_dict["updated_at"] = datetime.utcnow()
        submission_dict["submission_status"] = "pending"
        
        # Insert into temporary collection
        result = await temp_submissions_collection.insert_one(submission_dict)
        
        if result.inserted_id:
            # Count total policies
            total_policies = sum(len(area.policies) for area in filtered_policy_areas)
            
            return {
                "success": True, 
                "message": "Enhanced submission successful and is pending admin review", 
                "submission_id": str(result.inserted_id),
                "total_policies": total_policies,
                "policy_areas_count": len(filtered_policy_areas)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert data into database")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

# Get Countries Endpoint
@app.get("/api/countries")
async def get_countries():
    """Get list of all available countries"""
    return {"countries": COUNTRIES, "total": len(COUNTRIES)}

# Get Policy Areas Endpoint
@app.get("/api/policy-areas")
async def get_policy_areas():
    """Get list of all policy areas"""
    return {"policy_areas": POLICY_AREAS, "total": len(POLICY_AREAS)}

# Enhanced Admin Endpoints
@app.get("/api/admin/submissions")
async def get_enhanced_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    area_id: Optional[str] = Query(None),
    admin_user: dict = Depends(get_admin_user)
):
    try:
        skip = (page - 1) * limit
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["submission_status"] = status
        if area_id:
            filter_dict["policyAreas.area_id"] = area_id
        
        # Get submissions with user data
        pipeline = [
            {"$match": filter_dict},
            {"$lookup": {
                "from": "users",
                "let": {"user_id": {"$toObjectId": "$user_id"}},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}}],
                "as": "user_data"
            }},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        cursor = temp_submissions_collection.aggregate(pipeline)
        submissions = []
        
        async for doc in cursor:
            doc = convert_objectid(doc)
            # Add user data to submission
            if doc.get("user_data") and len(doc["user_data"]) > 0:
                user = doc["user_data"][0]
                doc["user_name"] = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                doc["user_email"] = user.get("email", "")
                doc["user_country"] = user.get("country", "")
            doc.pop("user_data", None)  # Remove the lookup data
            submissions.append(doc)
        
        # Get total count
        total_count = await temp_submissions_collection.count_documents(filter_dict)
        
        return {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching submissions: {str(e)}")

@app.put("/api/admin/update-enhanced-policy-status")
async def update_enhanced_policy_status(
    status_update: PolicyStatusUpdate,
    admin_user: dict = Depends(get_admin_user)
):
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
            "admin_id": admin_user["id"],
            "admin_email": admin_user["email"],
            "admin_notes": admin_notes,
            "timestamp": datetime.utcnow()
        }
        await admin_actions_collection.insert_one(admin_log)
        
        # Update overall submission status
        await update_submission_status(submission_id)
        
        return {"success": True, "message": f"Policy status updated to {new_status}"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")

@app.get("/api/admin/statistics")
async def get_enhanced_statistics(admin_user: dict = Depends(get_admin_user)):
    try:
        # Basic submission statistics
        stats = {
            "pending_submissions": await temp_submissions_collection.count_documents({"submission_status": "pending"}),
            "partially_approved": await temp_submissions_collection.count_documents({"submission_status": "partially_approved"}),
            "fully_approved": await temp_submissions_collection.count_documents({"submission_status": "fully_approved"}),
            "total_users": await users_collection.count_documents({}),
            "verified_users": await users_collection.count_documents({"is_verified": True}),
            "total_approved_policies": await master_policies_collection.count_documents({"master_status": {"$ne": "deleted"}}),
            "total_temp_submissions": await temp_submissions_collection.count_documents({})
        }
        
        # Policy area distribution
        policy_area_distribution = {}
        for area in POLICY_AREAS:
            count = await temp_submissions_collection.count_documents({
                "policyAreas.area_id": area["id"]
            })
            policy_area_distribution[area["id"]] = count
        
        stats["policy_area_distribution"] = policy_area_distribution
        
        # Recent admin actions
        cursor = admin_actions_collection.find().sort("timestamp", -1).limit(10)
        recent_actions = []
        async for action in cursor:
            action = convert_objectid(action)
            recent_actions.append(action)
        
        stats["recent_actions"] = recent_actions
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

async def update_submission_status(submission_id: str):
    """Update the overall status of a submission based on policy statuses"""
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
                
                if all(status == "approved" for status in policy_statuses):
                    new_status = "fully_approved"
                elif all(status in ["approved", "rejected"] for status in policy_statuses):
                    new_status = "fully_processed"
                elif any(status == "approved" for status in policy_statuses):
                    new_status = "partially_approved"
                else:
                    new_status = "pending"
        
        await temp_submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {"submission_status": new_status, "updated_at": datetime.utcnow()}}
        )
    except Exception as e:
        print(f"Error updating submission status: {e}")

# File Download Endpoint
@app.get("/api/file/{file_id}")
async def download_file(file_id: str):
    try:
        file_doc = await get_file_from_db(file_id)
        
        content_type = file_doc.get("content_type") or mimetypes.guess_type(file_doc["filename"])[0] or "application/octet-stream"
        file_data = file_doc["file_data"]
        
        def iterfile():
            yield file_data
        
        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={file_doc['filename']}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

# User Profile Endpoint
@app.get("/api/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    try:
        user_data = await users_collection.find_one({"_id": ObjectId(current_user["id"])})
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = convert_objectid(user_data)
        user_data.pop("password", None)  # Remove password from response
        
        return {"success": True, "user": user_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

# Health Check
@app.get("/api/health")
async def health_check():
    try:
        await db.command("ping")
        return {
            "status": "healthy", 
            "database": "connected", 
            "timestamp": datetime.utcnow(),
            "version": "3.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Enhanced AI Policy Database API is running", 
        "version": "3.0.0",
        "features": [
            "Complete Authentication System with Email Verification",
            "Google OAuth Integration",
            "Enhanced Policy Area Structure",
            "Backward Compatible Database Migration", 
            "Advanced File Upload System",
            "Comprehensive Admin Dashboard",
            "User Management with Roles"
        ]
    }

# Add these endpoints to your FastAPI app (main.py)

@app.get("/api/admin/master-policies")
async def get_master_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    country: Optional[str] = Query(None),
    policy_area: Optional[str] = Query(None),
    admin_user: dict = Depends(get_admin_user)
):
    """Get approved policies from master database with filtering"""
    try:
        skip = (page - 1) * limit
        
        # Build filter
        filter_dict = {"master_status": {"$ne": "deleted"}}
        if country:
            filter_dict["country"] = {"$regex": country, "$options": "i"}
        if policy_area:
            filter_dict["policyArea"] = policy_area
        
        # Get policies with user data
        pipeline = [
            {"$match": filter_dict},
            {"$lookup": {
                "from": "users",
                "let": {"user_id": {"$toObjectId": "$user_id"}},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}}],
                "as": "user_data"
            }},
            {"$sort": {"moved_to_master_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        cursor = master_policies_collection.aggregate(pipeline)
        policies = []
        
        async for doc in cursor:
            doc = convert_objectid(doc)
            # Add user data to policy
            if doc.get("user_data") and len(doc["user_data"]) > 0:
                user = doc["user_data"][0]
                doc["user_name"] = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                doc["user_email"] = user.get("email", "")
            doc.pop("user_data", None)  # Remove the lookup data
            policies.append(doc)
        
        # Get total count
        total_count = await master_policies_collection.count_documents(filter_dict)
        
        return {
            "policies": policies,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching master policies: {str(e)}")

@app.delete("/api/admin/master-policy/{policy_id}")
async def delete_master_policy(
    policy_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Soft delete a policy from master database"""
    try:
        result = await master_policies_collection.update_one(
            {"_id": ObjectId(policy_id)},
            {"$set": {
                "master_status": "deleted",
                "deleted_at": datetime.utcnow(),
                "deleted_by": admin_user["id"]
            }}
        )
        
        if result.modified_count == 1:
            # Log admin action
            admin_log = {
                "action": "master_policy_deleted",
                "master_policy_id": policy_id,
                "admin_id": admin_user["id"],
                "admin_email": admin_user["email"],
                "timestamp": datetime.utcnow()
            }
            await admin_actions_collection.insert_one(admin_log)
            
            return {"success": True, "message": "Policy deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Policy not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting policy: {str(e)}")

@app.get("/api/admin/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all users (admin only)"""
    try:
        skip = (page - 1) * limit
        
        # Build filter
        filter_dict = {}
        if search:
            filter_dict["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"firstName": {"$regex": search, "$options": "i"}},
                {"lastName": {"$regex": search, "$options": "i"}},
                {"country": {"$regex": search, "$options": "i"}}
            ]
        
        # Get users
        cursor = users_collection.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit)
        
        users = []
        async for doc in cursor:
            doc = convert_objectid(doc)
            doc.pop("password", None)  # Never return passwords
            users.append(doc)
        
        # Get total count
        total_count = await users_collection.count_documents(filter_dict)
        
        return {
            "users": users,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.put("/api/admin/users/{user_id}/toggle-admin")
async def toggle_admin_status(
    user_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Toggle admin status for a user (super admin only)"""
    try:
        # Only super admin can perform this action
        if not admin_user.get("is_super_admin", False):
            raise HTTPException(status_code=403, detail="Super admin access required")
        
        # Cannot modify self
        if user_id == admin_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot modify your own admin status")
        
        # Get user
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Toggle admin status
        new_status = not user.get("is_admin", False)
        
        await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "is_admin": new_status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Log admin action
        admin_log = {
            "action": "admin_status_toggled",
            "target_user_id": user_id,
            "target_user_email": user["email"],
            "new_status": new_status,
            "admin_id": admin_user["id"],
            "admin_email": admin_user["email"],
            "timestamp": datetime.utcnow()
        }
        await admin_actions_collection.insert_one(admin_log)
        
        return {
            "success": True,
            "message": f"Admin status {'enabled' if new_status else 'disabled'}",
            "is_admin": new_status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating admin status: {str(e)}")

@app.get("/api/admin/submission/{submission_id}")
async def get_submission_details(
    submission_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get detailed view of a specific submission"""
    try:
        # Get submission with user data
        pipeline = [
            {"$match": {"_id": ObjectId(submission_id)}},
            {"$lookup": {
                "from": "users",
                "let": {"user_id": {"$toObjectId": "$user_id"}},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}}],
                "as": "user_data"
            }}
        ]
        
        cursor = temp_submissions_collection.aggregate(pipeline)
        submission = await cursor.next()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        submission = convert_objectid(submission)
        
        # Add user data to submission
        if submission.get("user_data") and len(submission["user_data"]) > 0:
            user = submission["user_data"][0]
            submission["user_name"] = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            submission["user_email"] = user.get("email", "")
            submission["user_country"] = user.get("country", "")
        submission.pop("user_data", None)  # Remove the lookup data
        
        return submission
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching submission: {str(e)}")

@app.post("/api/admin/move-to-master")
async def move_policy_to_master(
    move_request: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Move approved policy to master database"""
    try:
        submission_id = move_request.get("submission_id")
        area_id = move_request.get("area_id")
        policy_index = move_request.get("policy_index")
        
        if not all([submission_id, area_id, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Find the submission
        submission = await temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Get the policy
        policy = None
        for area in submission.get("policyAreas", []):
            if area["area_id"] == area_id:
                if policy_index < len(area["policies"]):
                    policy = area["policies"][policy_index]
                    break
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Only move if approved
        if policy.get("status") != "approved":
            raise HTTPException(status_code=400, detail="Only approved policies can be moved to master database")
        
        # Prepare policy for master DB
        master_policy = {
            **policy,
            "country": submission["country"],
            "user_id": submission["user_id"],
            "user_email": submission.get("user_email", ""),
            "user_name": submission.get("user_name", ""),
            "original_submission_id": submission_id,
            "moved_to_master_at": datetime.utcnow(),
            "approved_by": admin_user["id"],
            "approved_by_email": admin_user["email"],
            "master_status": "active"
        }
        
        # Insert into master collection
        result = await master_policies_collection.insert_one(master_policy)
        
        if result.inserted_id:
            # Log the action
            admin_log = {
                "action": "moved_to_master",
                "submission_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index,
                "master_policy_id": str(result.inserted_id),
                "admin_id": admin_user["id"],
                "admin_email": admin_user["email"],
                "timestamp": datetime.utcnow()
            }
            await admin_actions_collection.insert_one(admin_log)
            
            return {
                "success": True,
                "message": "Policy moved to master database",
                "master_id": str(result.inserted_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to move policy to master database")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move to master failed: {str(e)}")

@app.get("/api/test-email")
async def test_email():
    result = await send_email("ai.signup003@gmail.com", "Test Email", "This is a test.")
    return {"sent": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)