"""
DynamoDB Policy Model
Replaces MongoDB policy model with DynamoDB operations
"""
from typing import Optional, Dict, List, Any
import uuid
from datetime import datetime
from config.dynamodb import get_dynamodb
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)

class Policy:
    """Policy model for DynamoDB operations"""
    
    def __init__(self, **kwargs):
        self.policy_id = kwargs.get('policy_id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.content = kwargs.get('content')
        self.category = kwargs.get('category')
        self.tags = kwargs.get('tags', [])
        self.status = kwargs.get('status', 'draft')
        self.file_paths = kwargs.get('file_paths', [])
        self.file_metadata = kwargs.get('file_metadata', {})
        self.ai_analysis = kwargs.get('ai_analysis', {})
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.published_at = kwargs.get('published_at')
        self.version = kwargs.get('version', 1)
        self.is_public = kwargs.get('is_public', False)
    
    def to_dict(self) -> Dict:
        """Convert policy object to dictionary"""
        return {
            'policy_id': self.policy_id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'category': self.category,
            'tags': self.tags,
            'status': self.status,
            'file_paths': self.file_paths,
            'file_metadata': self.file_metadata,
            'ai_analysis': self.ai_analysis,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'published_at': self.published_at,
            'version': self.version,
            'is_public': self.is_public
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Policy':
        """Create policy object from dictionary"""
        return cls(**data)
    
    async def save(self) -> bool:
        """Save policy to DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            self.updated_at = datetime.utcnow().isoformat()
            
            return await dynamodb.insert_item('policies', self.to_dict())
        except Exception as e:
            logger.error(f"Error saving policy: {str(e)}")
            return False
    
    async def update(self, update_data: Dict) -> bool:
        """Update policy in DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            
            # Update local object
            for key, value in update_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Increment version if content changed
            if 'content' in update_data or 'title' in update_data:
                self.version += 1
                update_data['version'] = self.version
            
            return await dynamodb.update_item(
                'policies', 
                {'policy_id': self.policy_id}, 
                update_data
            )
        except Exception as e:
            logger.error(f"Error updating policy: {str(e)}")
            return False
    
    async def delete(self) -> bool:
        """Delete policy from DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            return await dynamodb.delete_item('policies', {'policy_id': self.policy_id})
        except Exception as e:
            logger.error(f"Error deleting policy: {str(e)}")
            return False
    
    @staticmethod
    async def find_by_id(policy_id: str) -> Optional['Policy']:
        """Find policy by ID"""
        try:
            dynamodb = await get_dynamodb()
            policy_data = await dynamodb.get_item('policies', {'policy_id': policy_id})
            
            if policy_data:
                return Policy.from_dict(policy_data)
            return None
        except Exception as e:
            logger.error(f"Error finding policy by ID: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_user_id(user_id: str, limit: Optional[int] = None) -> List['Policy']:
        """Find policies by user ID"""
        try:
            dynamodb = await get_dynamodb()
            policies_data = await dynamodb.query_items(
                'policies',
                Key('user_id').eq(user_id),
                index_name='user-created-index',
                limit=limit
            )
            
            return [Policy.from_dict(policy_data) for policy_data in policies_data]
        except Exception as e:
            logger.error(f"Error finding policies by user ID: {str(e)}")
            return []
    
    @staticmethod
    async def find_public_policies(limit: Optional[int] = None) -> List['Policy']:
        """Find public policies"""
        try:
            dynamodb = await get_dynamodb()
            policies_data = await dynamodb.scan_items(
                'policies',
                filter_expression=Attr('is_public').eq(True),
                limit=limit
            )
            
            return [Policy.from_dict(policy_data) for policy_data in policies_data]
        except Exception as e:
            logger.error(f"Error finding public policies: {str(e)}")
            return []
    
    @staticmethod
    async def search_policies(query: str, user_id: Optional[str] = None) -> List['Policy']:
        """Search policies by title or content"""
        try:
            dynamodb = await get_dynamodb()
            
            # Build filter expression
            filter_expr = Attr('title').contains(query) | Attr('content').contains(query)
            
            if user_id:
                filter_expr = filter_expr & Attr('user_id').eq(user_id)
            
            policies_data = await dynamodb.scan_items(
                'policies',
                filter_expression=filter_expr
            )
            
            return [Policy.from_dict(policy_data) for policy_data in policies_data]
        except Exception as e:
            logger.error(f"Error searching policies: {str(e)}")
            return []
    
    @staticmethod
    async def find_by_category(category: str, limit: Optional[int] = None) -> List['Policy']:
        """Find policies by category"""
        try:
            dynamodb = await get_dynamodb()
            policies_data = await dynamodb.scan_items(
                'policies',
                filter_expression=Attr('category').eq(category),
                limit=limit
            )
            
            return [Policy.from_dict(policy_data) for policy_data in policies_data]
        except Exception as e:
            logger.error(f"Error finding policies by category: {str(e)}")
            return []
    
    @staticmethod
    async def get_all_policies(limit: Optional[int] = None) -> List['Policy']:
        """Get all policies"""
        try:
            dynamodb = await get_dynamodb()
            policies_data = await dynamodb.scan_items('policies', limit=limit)
            
            return [Policy.from_dict(policy_data) for policy_data in policies_data]
        except Exception as e:
            logger.error(f"Error getting all policies: {str(e)}")
            return []
    
    @staticmethod
    async def create_policy(user_id: str, title: str, description: str = "", 
                           content: str = "", category: str = "general") -> Optional['Policy']:
        """Create a new policy"""
        try:
            policy = Policy(
                user_id=user_id,
                title=title,
                description=description,
                content=content,
                category=category
            )
            
            if await policy.save():
                return policy
            return None
        except Exception as e:
            logger.error(f"Error creating policy: {str(e)}")
            return None
    
    async def publish(self) -> bool:
        """Publish the policy"""
        try:
            update_data = {
                'status': 'published',
                'published_at': datetime.utcnow().isoformat(),
                'is_public': True
            }
            
            return await self.update(update_data)
        except Exception as e:
            logger.error(f"Error publishing policy: {str(e)}")
            return False
    
    async def unpublish(self) -> bool:
        """Unpublish the policy"""
        try:
            update_data = {
                'status': 'draft',
                'is_public': False
            }
            
            return await self.update(update_data)
        except Exception as e:
            logger.error(f"Error unpublishing policy: {str(e)}")
            return False
