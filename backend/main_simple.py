"""
Simplified Main Application - Working Version
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Create app
app = FastAPI(title="AI Policy Tracker", version="1.0.0")

# Add CORS - more restrictive for production
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://your-frontend-domain.onrender.com",  # Replace with actual domain
]

# In development, allow all origins
if os.getenv("ENVIRONMENT") == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Policy Tracker API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Simple auth endpoint for testing
@app.post("/api/auth/admin-login")
async def admin_login(credentials: dict):
    email = credentials.get("email")
    password = credentials.get("password")
    
    # Simple hardcoded admin check for testing
    if email == "admin@gmail.com" and password == "admin123":
        return {
            "access_token": "test-token-123",
            "token_type": "bearer",
            "user": {
                "id": "1",
                "firstName": "Admin",
                "lastName": "User",
                "email": email,
                "country": "Global",
                "is_admin": True,
                "is_super_admin": True,
                "is_verified": True
            }
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Also add regular login for other components
@app.post("/api/auth/login")
async def regular_login(credentials: dict):
    email = credentials.get("email")
    password = credentials.get("password")
    
    # Debug logging
    print(f"🔐 Login attempt - Email: '{email}', Password: '{password}'")
    print(f"📊 Expected emails: ['admin@gmail.com', 'test@test.com']")
    
    # Simple hardcoded check for testing
    if (email == "admin@gmail.com" and password == "admin123") or (email == "test@test.com" and password == "test123"):
        print(f"✅ Login successful for: {email}")
        return {
            "access_token": "test-token-123",
            "token_type": "bearer",
            "user": {
                "id": "1",
                "firstName": "Test" if email == "test@test.com" else "Admin",
                "lastName": "User",
                "email": email,
                "country": "Global",
                "is_admin": email == "admin@gmail.com",
                "is_verified": True
            }
        }
    else:
        print(f"❌ Login failed for: {email}")
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Add register endpoint
@app.post("/api/auth/register")
async def register_user(user_data: dict):
    """Register a new user"""
    email = user_data.get("email")
    password = user_data.get("password")
    firstName = user_data.get("firstName")
    lastName = user_data.get("lastName")
    country = user_data.get("country")
    confirmPassword = user_data.get("confirmPassword", password)  # Default to password if not provided
    
    # Check if email already exists (simple check for demo)
    existing_users = ["admin@gmail.com", "test@test.com"]
    if email in existing_users:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Simulate successful registration
    return {
        "message": "User registered successfully",
        "email_sent": True,
        "otp_for_dev": "123456",  # For development
        "user": {
            "id": "new_user_123",
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "country": country,
            "is_verified": False
        }
    }

# Add OTP verification endpoint
@app.post("/api/auth/verify-email")
async def verify_email(verification_data: dict):
    """Verify email with OTP"""
    email = verification_data.get("email")
    otp = verification_data.get("otp")
    
    # Simple OTP check (in real app, verify against database)
    if otp == "123456":
        return {
            "message": "Email verified successfully",
            "access_token": "verified-token-123",
            "user": {
                "id": "verified_user_123",
                "email": email,
                "is_verified": True
            }
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid OTP")

# Add forgot password endpoint
@app.post("/api/auth/forgot-password")
async def forgot_password(request_data: dict):
    """Send password reset code"""
    email = request_data.get("email")
    
    # Simulate sending reset code
    return {
        "message": "Password reset code sent to your email",
        "email_sent": True,
        "reset_code_for_dev": "reset123"  # For development
    }

# Add reset password endpoint
@app.post("/api/auth/reset-password")
async def reset_password(reset_data: dict):
    """Reset password with code"""
    email = reset_data.get("email")
    code = reset_data.get("code")
    new_password = reset_data.get("newPassword")
    
    # Simple code check
    if code == "reset123":
        return {
            "message": "Password reset successfully",
            "access_token": "reset-success-token",
            "user": {
                "id": "reset_user_123",
                "email": email,
                "is_verified": True
            }
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid reset code")

# Add resend OTP endpoint
@app.post("/api/auth/resend-otp")
async def resend_otp(request_data: dict):
    """Resend OTP code"""
    email = request_data.get("email")
    
    return {
        "message": "OTP resent successfully",
        "email_sent": True,
        "otp_for_dev": "123456"  # For development
    }

# Missing endpoints that frontend is calling
@app.get("/api/countries")
async def get_countries():
    """Return list of countries"""
    return [
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

@app.get("/api/public/master-policies")
async def get_master_policies(limit: int = 1000, country: str = None, area: str = None):
    """Return sample master policies"""
    sample_policies = [
        {
            "id": 1,
            "title": "GDPR - General Data Protection Regulation",
            "country": "European Union",
            "area": "Data Protection",
            "description": "Comprehensive data protection regulation",
            "status": "active",
            "year": 2018
        },
        {
            "id": 2,
            "title": "AI Ethics Guidelines",
            "country": "United States",
            "area": "Artificial Intelligence",
            "description": "Guidelines for ethical AI development",
            "status": "draft",
            "year": 2023
        },
        {
            "id": 3,
            "title": "Climate Action Framework",
            "country": "Canada",
            "area": "Environment",
            "description": "National climate action policy",
            "status": "active",
            "year": 2022
        }
    ]
    
    # Apply filters if provided
    if country:
        sample_policies = [p for p in sample_policies if country.lower() in p["country"].lower()]
    if area:
        sample_policies = [p for p in sample_policies if area.lower() in p["area"].lower()]
    
    return sample_policies[:limit]

@app.get("/api/chat/conversations")
async def get_chat_conversations():
    """Return sample chat conversations"""
    return {
        "conversations": [
            {
                "id": "1",
                "title": "GDPR Questions",
                "last_message": "What are the key requirements of GDPR?",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ]
    }

@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Simple chat endpoint"""
    message = request.get("message", "")
    
    # Simple responses based on keywords
    if "gdpr" in message.lower():
        response = "GDPR (General Data Protection Regulation) is a comprehensive data protection law that applies to organizations operating in the EU. Key requirements include consent management, data subject rights, and breach notification."
    elif "ai" in message.lower():
        response = "AI policies typically cover areas like algorithmic transparency, bias prevention, data usage, and ethical considerations in AI development and deployment."
    elif "climate" in message.lower():
        response = "Climate policies often include carbon emission targets, renewable energy requirements, environmental impact assessments, and sustainable development frameworks."
    else:
        response = f"Thank you for your question about: '{message}'. I can help you with information about various policies including GDPR, AI guidelines, and climate action frameworks."
    
    return {
        "response": response,
        "timestamp": "2024-01-15T10:30:00Z",
        "message_id": "msg_123"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main_simple:app", host="0.0.0.0", port=port, reload=False)
