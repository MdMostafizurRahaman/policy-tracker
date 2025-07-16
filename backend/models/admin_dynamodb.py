"""
DynamoDB Admin Model
Replaces MongoDB admin model with DynamoDB operations
"""
from typing import Optional, Dict, List, Any
import uuid
from datetime import datetime
from config.dynamodb import get_dynamodb
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)

class AdminData:
    """Admin data model for DynamoDB operations"""
    
    def __init__(self, **kwargs):
        self.admin_id = kwargs.get('admin_id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.data_type = kwargs.get('data_type')  # 'system_config', 'user_stats', 'audit_log', etc.
        self.data_key = kwargs.get('data_key')
        self.data_value = kwargs.get('data_value')
        self.metadata = kwargs.get('metadata', {})
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.expires_at = kwargs.get('expires_at')
        self.is_active = kwargs.get('is_active', True)
    
    def to_dict(self) -> Dict:
        """Convert admin data object to dictionary"""
        return {
            'admin_id': self.admin_id,
            'user_id': self.user_id,
            'data_type': self.data_type,
            'data_key': self.data_key,
            'data_value': self.data_value,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'expires_at': self.expires_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AdminData':
        """Create admin data object from dictionary"""
        return cls(**data)
    
    async def save(self) -> bool:
        """Save admin data to DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            self.updated_at = datetime.utcnow().isoformat()
            
            return await dynamodb.insert_item('admin_data', self.to_dict())
        except Exception as e:
            logger.error(f"Error saving admin data: {str(e)}")
            return False
    
    async def update(self, update_data: Dict) -> bool:
        """Update admin data in DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            
            # Update local object
            for key, value in update_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            self.updated_at = datetime.utcnow().isoformat()
            update_data['updated_at'] = self.updated_at
            
            return await dynamodb.update_item(
                'admin_data', 
                {'admin_id': self.admin_id}, 
                update_data
            )
        except Exception as e:
            logger.error(f"Error updating admin data: {str(e)}")
            return False
    
    async def delete(self) -> bool:
        """Delete admin data from DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            return await dynamodb.delete_item('admin_data', {'admin_id': self.admin_id})
        except Exception as e:
            logger.error(f"Error deleting admin data: {str(e)}")
            return False
    
    @staticmethod
    async def find_by_id(admin_id: str) -> Optional['AdminData']:
        """Find admin data by ID"""
        try:
            dynamodb = await get_dynamodb()
            admin_data = await dynamodb.get_item('admin_data', {'admin_id': admin_id})
            
            if admin_data and admin_data.get('is_active', True):
                return AdminData.from_dict(admin_data)
            return None
        except Exception as e:
            logger.error(f"Error finding admin data by ID: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_key(data_type: str, data_key: str) -> Optional['AdminData']:
        """Find admin data by type and key"""
        try:
            dynamodb = await get_dynamodb()
            admin_data_list = await dynamodb.scan_items(
                'admin_data',
                filter_expression=Attr('data_type').eq(data_type) & 
                                 Attr('data_key').eq(data_key) & 
                                 Attr('is_active').eq(True)
            )
            
            if admin_data_list:
                return AdminData.from_dict(admin_data_list[0])
            return None
        except Exception as e:
            logger.error(f"Error finding admin data by key: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_type(data_type: str, limit: Optional[int] = None) -> List['AdminData']:
        """Find admin data by type"""
        try:
            dynamodb = await get_dynamodb()
            admin_data_list = await dynamodb.scan_items(
                'admin_data',
                filter_expression=Attr('data_type').eq(data_type) & Attr('is_active').eq(True),
                limit=limit
            )
            
            return [AdminData.from_dict(data) for data in admin_data_list]
        except Exception as e:
            logger.error(f"Error finding admin data by type: {str(e)}")
            return []
    
    @staticmethod
    async def create_or_update(data_type: str, data_key: str, data_value: Any,
                              user_id: Optional[str] = None, metadata: Dict = None) -> Optional['AdminData']:
        """Create or update admin data"""
        try:
            # Try to find existing record
            existing = await AdminData.find_by_key(data_type, data_key)
            
            if existing:
                # Update existing record
                update_data = {
                    'data_value': data_value,
                    'metadata': metadata or {}
                }
                if await existing.update(update_data):
                    return existing
            else:
                # Create new record
                admin_data = AdminData(
                    user_id=user_id,
                    data_type=data_type,
                    data_key=data_key,
                    data_value=data_value,
                    metadata=metadata or {}
                )
                
                if await admin_data.save():
                    return admin_data
            
            return None
        except Exception as e:
            logger.error(f"Error creating/updating admin data: {str(e)}")
            return None

class SystemConfig:
    """System configuration management"""
    
    @staticmethod
    async def get_config(key: str, default_value: Any = None) -> Any:
        """Get system configuration value"""
        try:
            admin_data = await AdminData.find_by_key('system_config', key)
            if admin_data:
                return admin_data.data_value
            return default_value
        except Exception as e:
            logger.error(f"Error getting system config: {str(e)}")
            return default_value
    
    @staticmethod
    async def set_config(key: str, value: Any, user_id: Optional[str] = None) -> bool:
        """Set system configuration value"""
        try:
            admin_data = await AdminData.create_or_update(
                'system_config', key, value, user_id
            )
            return admin_data is not None
        except Exception as e:
            logger.error(f"Error setting system config: {str(e)}")
            return False
    
    @staticmethod
    async def get_all_configs() -> Dict[str, Any]:
        """Get all system configurations"""
        try:
            configs = await AdminData.find_by_type('system_config')
            return {config.data_key: config.data_value for config in configs}
        except Exception as e:
            logger.error(f"Error getting all system configs: {str(e)}")
            return {}

class UserStats:
    """User statistics management"""
    
    @staticmethod
    async def update_user_stat(user_id: str, stat_key: str, value: Any) -> bool:
        """Update user statistic"""
        try:
            composite_key = f"{user_id}:{stat_key}"
            admin_data = await AdminData.create_or_update(
                'user_stats', composite_key, value, user_id
            )
            return admin_data is not None
        except Exception as e:
            logger.error(f"Error updating user stat: {str(e)}")
            return False
    
    @staticmethod
    async def get_user_stat(user_id: str, stat_key: str, default_value: Any = 0) -> Any:
        """Get user statistic"""
        try:
            composite_key = f"{user_id}:{stat_key}"
            admin_data = await AdminData.find_by_key('user_stats', composite_key)
            if admin_data:
                return admin_data.data_value
            return default_value
        except Exception as e:
            logger.error(f"Error getting user stat: {str(e)}")
            return default_value
    
    @staticmethod
    async def get_user_stats(user_id: str) -> Dict[str, Any]:
        """Get all statistics for a user"""
        try:
            dynamodb = await get_dynamodb()
            user_stats = await dynamodb.scan_items(
                'admin_data',
                filter_expression=Attr('data_type').eq('user_stats') & 
                                 Attr('user_id').eq(user_id) & 
                                 Attr('is_active').eq(True)
            )
            
            stats = {}
            for stat in user_stats:
                # Extract stat key from composite key (user_id:stat_key)
                stat_key = stat['data_key'].split(':', 1)[1] if ':' in stat['data_key'] else stat['data_key']
                stats[stat_key] = stat['data_value']
            
            return stats
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}

class AuditLog:
    """Audit logging for admin actions"""
    
    @staticmethod
    async def log_action(user_id: str, action: str, details: Dict = None,
                        resource_type: str = None, resource_id: str = None) -> bool:
        """Log an admin action"""
        try:
            log_id = str(uuid.uuid4())
            log_data = {
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details or {},
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': details.get('ip_address') if details else None
            }
            
            admin_data = AdminData(
                user_id=user_id,
                data_type='audit_log',
                data_key=log_id,
                data_value=log_data
            )
            
            return await admin_data.save()
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
            return False
    
    @staticmethod
    async def get_audit_logs(user_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        try:
            dynamodb = await get_dynamodb()
            
            if user_id:
                filter_expr = Attr('data_type').eq('audit_log') & Attr('user_id').eq(user_id)
            else:
                filter_expr = Attr('data_type').eq('audit_log')
            
            logs_data = await dynamodb.scan_items(
                'admin_data',
                filter_expression=filter_expr,
                limit=limit
            )
            
            # Sort by timestamp descending
            logs_data.sort(
                key=lambda x: x.get('data_value', {}).get('timestamp', ''),
                reverse=True
            )
            
            return [log['data_value'] for log in logs_data]
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return []
