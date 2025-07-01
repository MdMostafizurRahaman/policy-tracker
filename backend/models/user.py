"""
User Models and Schemas
Pydantic models for user-related operations
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime
from config.constants import COUNTRIES

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

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

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

class UserResponse(BaseModel):
    id: str
    firstName: str
    lastName: str
    email: str
    country: str
    is_admin: bool = False
    is_verified: bool = False
    created_at: Optional[datetime] = None
