"""
Authentication Middleware for FastAPI with DynamoDB
"""
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from config.settings import settings
from models.user_dynamodb import User
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # auto_error=False makes it optional

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user from DynamoDB"""
    try:
        if credentials is None:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Find user in DynamoDB
        user = await User.find_by_id(user_id)
        if user is None:
            # Fallback to email lookup
            user = await User.find_by_email(email)
            
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Convert user to dict for response
        user_dict = user.to_dict()
        user_dict.pop('password_hash', None)  # Remove password from response
        
        return user_dict
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated admin user"""
    user = await get_current_user(credentials)
    
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None"""
    try:
        if credentials is None:
            return None
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None - alias for compatibility"""
    return await get_current_user_optional(credentials)
