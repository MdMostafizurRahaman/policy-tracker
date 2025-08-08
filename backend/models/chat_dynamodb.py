"""
DynamoDB Chat Model
Replaces MongoDB chat model with DynamoDB operations
"""
from typing import Optional, Dict, List, Any
import uuid
from datetime import datetime
from config.dynamodb import get_dynamodb
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)

class ChatMessage:
    """Chat message model for DynamoDB operations"""
    
    def __init__(self, **kwargs):
        self.message_id = kwargs.get('message_id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.policy_id = kwargs.get('policy_id')
        self.session_id = kwargs.get('session_id', str(uuid.uuid4()))
        self.message_type = kwargs.get('message_type', 'user')  # 'user' or 'ai'
        self.content = kwargs.get('content')
        self.metadata = kwargs.get('metadata', {})
        self.attachments = kwargs.get('attachments', [])
        self.ai_context = kwargs.get('ai_context', {})
        self.confidence_score = kwargs.get('confidence_score')
        self.response_time = kwargs.get('response_time')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.is_deleted = kwargs.get('is_deleted', False)
        self.feedback = kwargs.get('feedback', {})
    
    def to_dict(self) -> Dict:
        """Convert chat message object to dictionary"""
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'policy_id': self.policy_id,
            'session_id': self.session_id,
            'message_type': self.message_type,
            'content': self.content,
            'metadata': self.metadata,
            'attachments': self.attachments,
            'ai_context': self.ai_context,
            'confidence_score': self.confidence_score,
            'response_time': self.response_time,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_deleted': self.is_deleted,
            'feedback': self.feedback
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        """Create chat message object from dictionary"""
        return cls(**data)
    
    async def save(self) -> bool:
        """Save chat message to DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            self.updated_at = datetime.utcnow().isoformat()
            
            return await dynamodb.insert_item('chat_messages', self.to_dict())
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}")
            return False
    
    async def update(self, update_data: Dict) -> bool:
        """Update chat message in DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            
            # Update local object
            for key, value in update_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            self.updated_at = datetime.utcnow().isoformat()
            update_data['updated_at'] = self.updated_at
            
            return await dynamodb.update_item(
                'chat_messages', 
                {'message_id': self.message_id}, 
                update_data
            )
        except Exception as e:
            logger.error(f"Error updating chat message: {str(e)}")
            return False
    
    async def delete(self) -> bool:
        """Soft delete chat message in DynamoDB"""
        try:
            return await self.update({'is_deleted': True})
        except Exception as e:
            logger.error(f"Error deleting chat message: {str(e)}")
            return False
    
    async def hard_delete(self) -> bool:
        """Hard delete chat message from DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            return await dynamodb.delete_item('chat_messages', {'message_id': self.message_id})
        except Exception as e:
            logger.error(f"Error hard deleting chat message: {str(e)}")
            return False
    
    @staticmethod
    async def find_by_id(message_id: str) -> Optional['ChatMessage']:
        """Find chat message by ID"""
        try:
            dynamodb = await get_dynamodb()
            message_data = await dynamodb.get_item('chat_messages', {'message_id': message_id})
            
            if message_data and not message_data.get('is_deleted', False):
                return ChatMessage.from_dict(message_data)
            return None
        except Exception as e:
            logger.error(f"Error finding chat message by ID: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_session_id(session_id: str, limit: Optional[int] = None) -> List['ChatMessage']:
        """Find chat messages by session ID"""
        try:
            dynamodb = await get_dynamodb()
            messages_data = await dynamodb.query_items(
                'chat_messages',
                Key('session_id').eq(session_id),
                index_name='session-created-index',
                limit=limit
            )
            
            # Filter out deleted messages
            active_messages = [
                msg_data for msg_data in messages_data 
                if not msg_data.get('is_deleted', False)
            ]
            
            return [ChatMessage.from_dict(msg_data) for msg_data in active_messages]
        except Exception as e:
            logger.error(f"Error finding chat messages by session ID: {str(e)}")
            return []
    
    @staticmethod
    async def find_by_user_id(user_id: str, limit: Optional[int] = None) -> List['ChatMessage']:
        """Find chat messages by user ID"""
        try:
            dynamodb = await get_dynamodb()
            messages_data = await dynamodb.query_items(
                'chat_messages',
                Key('user_id').eq(user_id),
                index_name='user-created-index',
                limit=limit
            )
            
            # Filter out deleted messages
            active_messages = [
                msg_data for msg_data in messages_data 
                if not msg_data.get('is_deleted', False)
            ]
            
            return [ChatMessage.from_dict(msg_data) for msg_data in active_messages]
        except Exception as e:
            logger.error(f"Error finding chat messages by user ID: {str(e)}")
            return []
    
    @staticmethod
    async def find_by_policy_id(policy_id: str, limit: Optional[int] = None) -> List['ChatMessage']:
        """Find chat messages by policy ID"""
        try:
            dynamodb = await get_dynamodb()
            messages_data = await dynamodb.scan_items(
                'chat_messages',
                filter_expression=Attr('policy_id').eq(policy_id) & Attr('is_deleted').eq(False),
                limit=limit
            )
            
            return [ChatMessage.from_dict(msg_data) for msg_data in messages_data]
        except Exception as e:
            logger.error(f"Error finding chat messages by policy ID: {str(e)}")
            return []
    
    @staticmethod
    async def get_recent_messages(user_id: str, limit: int = 50) -> List['ChatMessage']:
        """Get recent messages for a user"""
        try:
            dynamodb = await get_dynamodb()
            messages_data = await dynamodb.query_items(
                'chat_messages',
                Key('user_id').eq(user_id),
                index_name='user-created-index',
                limit=limit,
                scan_index_forward=False  # Sort in descending order
            )
            
            # Filter out deleted messages
            active_messages = [
                msg_data for msg_data in messages_data 
                if not msg_data.get('is_deleted', False)
            ]
            
            return [ChatMessage.from_dict(msg_data) for msg_data in active_messages]
        except Exception as e:
            logger.error(f"Error getting recent messages: {str(e)}")
            return []
    
    @staticmethod
    async def create_message(user_id: str, content: str, message_type: str = 'user',
                           session_id: Optional[str] = None, policy_id: Optional[str] = None,
                           metadata: Dict = None) -> Optional['ChatMessage']:
        """Create a new chat message"""
        try:
            message = ChatMessage(
                user_id=user_id,
                content=content,
                message_type=message_type,
                session_id=session_id or str(uuid.uuid4()),
                policy_id=policy_id,
                metadata=metadata or {}
            )
            
            if await message.save():
                return message
            return None
        except Exception as e:
            logger.error(f"Error creating chat message: {str(e)}")
            return None
    
    @staticmethod
    async def create_ai_response(user_id: str, content: str, session_id: str,
                               confidence_score: Optional[float] = None,
                               response_time: Optional[float] = None,
                               ai_context: Dict = None) -> Optional['ChatMessage']:
        """Create an AI response message"""
        try:
            message = ChatMessage(
                user_id=user_id,
                content=content,
                message_type='ai',
                session_id=session_id,
                confidence_score=confidence_score,
                response_time=response_time,
                ai_context=ai_context or {}
            )
            
            if await message.save():
                return message
            return None
        except Exception as e:
            logger.error(f"Error creating AI response: {str(e)}")
            return None
    
    async def add_feedback(self, feedback_type: str, rating: Optional[int] = None,
                          comment: Optional[str] = None) -> bool:
        """Add feedback to the message"""
        try:
            feedback_data = {
                'type': feedback_type,
                'rating': rating,
                'comment': comment,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return await self.update({'feedback': feedback_data})
        except Exception as e:
            logger.error(f"Error adding feedback: {str(e)}")
            return False

class ChatSession:
    """Chat session model for managing conversation sessions"""
    
    def __init__(self, **kwargs):
        self.session_id = kwargs.get('session_id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.title = kwargs.get('title', 'New Chat')
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.last_message_at = kwargs.get('last_message_at')
        self.message_count = kwargs.get('message_count', 0)
        self.metadata = kwargs.get('metadata', {})
    
    @staticmethod
    async def create_session(user_id: str, title: str = 'New Chat') -> str:
        """Create a new chat session and return session ID"""
        session_id = str(uuid.uuid4())
        try:
            dynamodb = await get_dynamodb()
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'title': title,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'message_count': 0,
                'metadata': {}
            }
            
            await dynamodb.insert_item('chat_sessions', session_data)
            return session_id
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            return session_id  # Return session_id even if save fails
    
    @staticmethod
    async def get_user_sessions(user_id: str, limit: int = 20) -> List[Dict]:
        """Get chat sessions for a user"""
        try:
            dynamodb = await get_dynamodb()
            sessions_data = await dynamodb.query_items(
                'chat_sessions',
                Key('user_id').eq(user_id),
                index_name='user-updated-index',
                limit=limit,
                scan_index_forward=False
            )
            
            return sessions_data
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []
