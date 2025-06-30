"""
Authentication service
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config.settings import settings
from models.user import UserCreate, UserResponse
from bson import ObjectId
import random
import string

class AuthService:
    def __init__(self, db):
        self.db = db
        self.users_collection = db.users
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create new user"""
        # Check if user already exists
        existing_user = await self.users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = self.hash_password(user_data.password)
        
        # Generate OTP
        otp = self.generate_otp()
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "password": hashed_password,
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "country": user_data.country,
            "is_verified": False,
            "is_admin": False,
            "google_auth": False,
            "otp": otp,
            "otp_expires": datetime.utcnow() + timedelta(minutes=10),
            "created_at": datetime.utcnow()
        }
        
        result = await self.users_collection.insert_one(user_doc)
        return {"user_id": str(result.inserted_id), "otp": otp}
    
    async def verify_user_email(self, email: str, otp: str) -> bool:
        """Verify user email with OTP"""
        user = await self.users_collection.find_one({
            "email": email,
            "otp": otp,
            "otp_expires": {"$gt": datetime.utcnow()}
        })
        
        if user:
            await self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"is_verified": True}, "$unset": {"otp": "", "otp_expires": ""}}
            )
            return True
        return False
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        """Authenticate user login"""
        user = await self.users_collection.find_one({"email": email})
        
        if not user or not self.verify_password(password, user["password"]):
            return None
            
        if not user.get("is_verified", False):
            raise ValueError("Email not verified")
        
        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            firstName=user["firstName"],
            lastName=user["lastName"],
            country=user["country"],
            is_verified=user.get("is_verified", False),
            is_admin=user.get("is_admin", False),
            google_auth=user.get("google_auth", False),
            created_at=user["created_at"]
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user:
                return UserResponse(
                    id=str(user["_id"]),
                    email=user["email"],
                    firstName=user["firstName"],
                    lastName=user["lastName"],
                    country=user["country"],
                    is_verified=user.get("is_verified", False),
                    is_admin=user.get("is_admin", False),
                    google_auth=user.get("google_auth", False),
                    created_at=user["created_at"]
                )
        except:
            pass
        return None
