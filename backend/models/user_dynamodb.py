"""
DynamoDB User Model
Replaces MongoDB user model with DynamoDB operations
"""
from typing import Optional, Dict, List
import uuid
from datetime import datetime
import bcrypt
from config.dynamodb import get_dynamodb
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)

class User:
    """User model for DynamoDB operations"""
    
    def __init__(self, **kwargs):
        self.user_id = kwargs.get('user_id', str(uuid.uuid4()))
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.name = kwargs.get('name')
        self.firstName = kwargs.get('firstName')
        self.lastName = kwargs.get('lastName')
        self.country = kwargs.get('country')
        self.role = kwargs.get('role', 'user')
        self.is_active = kwargs.get('is_active', True)
        self.is_email_verified = kwargs.get('is_email_verified', False)
        self.email_verification_otp = kwargs.get('email_verification_otp')
        self.otp_expiry = kwargs.get('otp_expiry')
        self.password_reset_otp = kwargs.get('password_reset_otp')
        self.password_reset_otp_expiry = kwargs.get('password_reset_otp_expiry')
        self.google_id = kwargs.get('google_id')
        self.profile_picture = kwargs.get('profile_picture')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.last_login = kwargs.get('last_login')
        self.login_count = kwargs.get('login_count', 0)
    
    def to_dict(self) -> Dict:
        """Convert user object to dictionary for DynamoDB"""
        data = {
            'user_id': self.user_id,
            'email': self.email,
            'password_hash': self.password_hash,
            'name': self.name,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'country': self.country,
            'role': self.role,
            'is_active': self.is_active,
            'is_email_verified': self.is_email_verified,
            'email_verification_otp': self.email_verification_otp,
            'otp_expiry': self.otp_expiry,
            'password_reset_otp': self.password_reset_otp,
            'password_reset_otp_expiry': self.password_reset_otp_expiry,
            'profile_picture': self.profile_picture,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'login_count': self.login_count
        }
        
        # Only include google_id if it has a value (DynamoDB GSI requirement)
        if self.google_id:
            data['google_id'] = self.google_id
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user object from dictionary"""
        return cls(**data)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    async def save(self) -> bool:
        """Save user to DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            self.updated_at = datetime.utcnow().isoformat()
            
            return await dynamodb.insert_item('users', self.to_dict())
        except Exception as e:
            logger.error(f"Error saving user: {str(e)}")
            return False
    
    async def update(self, update_data: Dict) -> bool:
        """Update user in DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            
            # Update local object
            for key, value in update_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            return await dynamodb.update_item(
                'users', 
                {'user_id': self.user_id}, 
                update_data
            )
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False
    
    async def delete(self) -> bool:
        """Delete user from DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            return await dynamodb.delete_item('users', {'user_id': self.user_id})
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
    
    @staticmethod
    async def find_by_id(user_id: str) -> Optional['User']:
        """Find user by ID"""
        try:
            dynamodb = await get_dynamodb()
            user_data = await dynamodb.get_item('users', {'user_id': user_id})
            
            if user_data:
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_email(email: str) -> Optional['User']:
        """Find user by email"""
        try:
            dynamodb = await get_dynamodb()
            users = await dynamodb.query_items(
                'users',
                Key('email').eq(email),
                index_name='email-index'
            )
            
            if users:
                return User.from_dict(users[0])
            return None
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_google_id(google_id: str) -> Optional['User']:
        """Find user by Google ID"""
        try:
            dynamodb = await get_dynamodb()
            users = await dynamodb.scan_items(
                'users',
                filter_expression=Attr('google_id').eq(google_id)
            )
            
            if users:
                return User.from_dict(users[0])
            return None
        except Exception as e:
            logger.error(f"Error finding user by Google ID: {str(e)}")
            return None
    
    @staticmethod
    async def get_all_users() -> List['User']:
        """Get all users"""
        try:
            dynamodb = await get_dynamodb()
            users_data = await dynamodb.scan_items('users')
            
            return [User.from_dict(user_data) for user_data in users_data]
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []
    
    @staticmethod
    async def create_user(email: str, password: str, name: str, role: str = 'user', firstName: str = None, lastName: str = None, country: str = None, **kwargs) -> Optional['User']:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await User.find_by_email(email)
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return None
            
            # Create new user
            user = User(
                email=email,
                password_hash=User.hash_password(password),
                name=name,
                firstName=firstName,
                lastName=lastName,
                country=country,
                role=role,
                **kwargs
            )
            
            if await user.save():
                return user
            return None
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
