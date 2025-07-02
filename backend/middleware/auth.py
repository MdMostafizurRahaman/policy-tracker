"""
Authentication Middleware
Handles JWT token verification and user authentication
"""
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import settings
from config.database import get_users_collection
import logging

# We'll import this locally to avoid circular imports
def convert_objectid(obj):
    """Convert ObjectId to string recursively"""
    from bson import ObjectId
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        users_collection = get_users_collection()
        from bson import ObjectId
        try:
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            # Fallback to email lookup if user_id format is invalid
            email = payload.get("email")
            if email:
                user = await users_collection.find_one({"email": email})
            else:
                user = None
                
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

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
