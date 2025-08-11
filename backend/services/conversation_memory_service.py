"""
Conversation Memory Service
==========================

This service provides conversation context and memory management for the chatbot.
It maintains conversation threads and provides context-aware responses.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import json
from dataclasses import dataclass, asdict
from config.dynamodb import get_dynamodb, DynamoDBClient

@dataclass
class ConversationMessage:
    """Represents a single message in a conversation"""
    message_id: str
    conversation_id: str
    user_id: Optional[str]
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ConversationThread:
    """Represents a complete conversation thread"""
    conversation_id: str
    user_id: Optional[str]
    messages: List[ConversationMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class ConversationMemoryService:
    """Service for managing conversation memory and context"""
    
    def __init__(self):
        self.db: Optional[DynamoDBClient] = None
        self.max_context_messages = 10  # Maximum messages to include in context
        self.context_time_limit = timedelta(hours=24)  # Time limit for conversation context
    
    async def ensure_db_connection(self):
        """Ensure database connection is established"""
        if self.db is None:
            self.db = await get_dynamodb()
    
    async def get_conversation_context(
        self, 
        conversation_id: str, 
        include_messages: int = None
    ) -> List[ConversationMessage]:
        """
        Get conversation context (previous messages) for a conversation
        
        Args:
            conversation_id: The conversation ID
            include_messages: Number of recent messages to include (default: max_context_messages)
        
        Returns:
            List of conversation messages in chronological order
        """
        await self.ensure_db_connection()
        
        try:
            if include_messages is None:
                include_messages = self.max_context_messages
            
            # Query messages from the conversation
            table = self.db.dynamodb.Table("conversation_messages")
            
            response = table.query(
                IndexName="conversation-timestamp-index",
                KeyConditionExpression="conversation_id = :conv_id",
                ExpressionAttributeValues={":conv_id": conversation_id},
                ScanIndexForward=False,  # Most recent first
                Limit=include_messages
            )
            
            messages = []
            for item in reversed(response.get('Items', [])):  # Reverse to get chronological order
                # Parse timestamp
                timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                
                # Check if message is within time limit
                if datetime.utcnow() - timestamp <= self.context_time_limit:
                    message = ConversationMessage(
                        message_id=item['message_id'],
                        conversation_id=item['conversation_id'],
                        user_id=item.get('user_id'),
                        role=item['role'],
                        content=item['content'],
                        timestamp=timestamp,
                        metadata=item.get('metadata', {})
                    )
                    messages.append(message)
            
            return messages
            
        except Exception as e:
            print(f"❌ Error getting conversation context: {e}")
            return []
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Add a new message to a conversation
        
        Args:
            conversation_id: The conversation ID
            role: 'user' or 'assistant'
            content: The message content
            user_id: The user ID (optional)
            metadata: Additional metadata (optional)
        
        Returns:
            The created ConversationMessage
        """
        await self.ensure_db_connection()
        
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            message = ConversationMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                content=content,
                timestamp=timestamp,
                metadata=metadata or {}
            )
            
            # Store in DynamoDB
            from boto3.dynamodb.conditions import Key
            
            # Use the low-level client for put_item
            item = {
                'message_id': {'S': message_id},
                'conversation_id': {'S': conversation_id},
                'role': {'S': role},
                'content': {'S': content},
                'timestamp': {'S': timestamp.isoformat()},
                'ttl': {'N': str(int((timestamp + timedelta(days=90)).timestamp()))}
            }
            
            if user_id:
                item['user_id'] = {'S': user_id}
            if metadata:
                item['metadata'] = {'S': json.dumps(metadata)}
            
            # Use client.put_item instead of table.put_item
            self.db.client.put_item(
                TableName='conversation_messages',
                Item=item
            )
            
            # Update conversation thread metadata
            await self._update_conversation_metadata(conversation_id, user_id)
            
            return message
            
        except Exception as e:
            print(f"❌ Error adding message: {e}")
            raise e
    
    async def _update_conversation_metadata(self, conversation_id: str, user_id: Optional[str]):
        """Update conversation thread metadata"""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Try to get existing conversation
            try:
                response = self.db.client.get_item(
                    TableName='conversation_threads',
                    Key={'conversation_id': {'S': conversation_id}}
                )
                
                if 'Item' in response:
                    # Update existing conversation
                    message_count = int(response['Item'].get('message_count', {}).get('N', '0')) + 1
                else:
                    # Create new conversation thread
                    message_count = 1
            except:
                # Default to new conversation
                message_count = 1
            
            # Prepare item for DynamoDB
            item = {
                'conversation_id': {'S': conversation_id},
                'updated_at': {'S': timestamp},
                'message_count': {'N': str(message_count)},
                'ttl': {'N': str(int((datetime.utcnow() + timedelta(days=90)).timestamp()))}
            }
            
            if user_id:
                item['user_id'] = {'S': user_id}
            
            if message_count == 1:
                item['created_at'] = {'S': timestamp}
            
            # Use client.put_item
            self.db.client.put_item(
                TableName='conversation_threads',
                Item=item
            )
            
        except Exception as e:
            print(f"❌ Error updating conversation metadata: {e}")
    
    async def get_conversation_thread(self, conversation_id: str) -> Optional[ConversationThread]:
        """Get complete conversation thread"""
        await self.ensure_db_connection()
        
        try:
            # Get conversation metadata
            thread_table = self.db.dynamodb.Table("conversation_threads")
            thread_response = thread_table.get_item(Key={'conversation_id': conversation_id})
            
            if 'Item' not in thread_response:
                return None
            
            thread_data = thread_response['Item']
            
            # Get all messages
            messages = await self.get_conversation_context(conversation_id, include_messages=100)
            
            thread = ConversationThread(
                conversation_id=conversation_id,
                user_id=thread_data.get('user_id'),
                messages=messages,
                created_at=datetime.fromisoformat(thread_data['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(thread_data['updated_at'].replace('Z', '+00:00')),
                metadata=thread_data.get('metadata', {})
            )
            
            return thread
            
        except Exception as e:
            print(f"❌ Error getting conversation thread: {e}")
            return None
    
    async def format_conversation_context(self, messages: List[ConversationMessage]) -> str:
        """
        Format conversation messages into a context string for AI consumption
        
        Args:
            messages: List of conversation messages
        
        Returns:
            Formatted context string
        """
        if not messages:
            return ""
        
        context_parts = ["**Previous Conversation:**"]
        
        for message in messages:
            role_label = "User" if message.role == "user" else "Assistant"
            context_parts.append(f"{role_label}: {message.content}")
        
        context_parts.append("**Current Query:**")
        return "\n".join(context_parts)
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[ConversationThread]:
        """Get all conversation threads for a user"""
        await self.ensure_db_connection()
        
        try:
            table = self.db.dynamodb.Table("conversation_threads")
            
            response = table.query(
                IndexName="user-updated-index",
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={":user_id": user_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            threads = []
            for item in response.get('Items', []):
                # Get messages for this conversation
                messages = await self.get_conversation_context(
                    item['conversation_id'], 
                    include_messages=5  # Just get a few recent messages
                )
                
                thread = ConversationThread(
                    conversation_id=item['conversation_id'],
                    user_id=item['user_id'],
                    messages=messages,
                    created_at=datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00')),
                    metadata=item.get('metadata', {})
                )
                threads.append(thread)
            
            return threads
            
        except Exception as e:
            print(f"❌ Error getting user conversations: {e}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        await self.ensure_db_connection()
        
        try:
            # Delete all messages
            message_table = self.db.dynamodb.Table("conversation_messages")
            
            # Get all messages for this conversation
            response = message_table.query(
                IndexName="conversation-timestamp-index",
                KeyConditionExpression="conversation_id = :conv_id",
                ExpressionAttributeValues={":conv_id": conversation_id}
            )
            
            # Delete each message
            for item in response.get('Items', []):
                message_table.delete_item(
                    Key={'message_id': item['message_id']}
                )
            
            # Delete conversation thread
            thread_table = self.db.dynamodb.Table("conversation_threads")
            thread_table.delete_item(Key={'conversation_id': conversation_id})
            
            return True
            
        except Exception as e:
            print(f"❌ Error deleting conversation: {e}")
            return False
    
    async def ensure_tables_exist(self):
        """Ensure required DynamoDB tables exist"""
        await self.ensure_db_connection()
        
        try:
            # Create conversation_messages table
            try:
                self.db.dynamodb.create_table(
                    TableName='conversation_messages',
                    KeySchema=[
                        {'AttributeName': 'message_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'message_id', 'AttributeType': 'S'},
                        {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'conversation-timestamp-index',
                            'KeySchema': [
                                {'AttributeName': 'conversation_id', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                        }
                    ],
                    ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                )
                print("✅ Created conversation_messages table")
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"⚠️ Error creating conversation_messages table: {e}")
            
            # Create conversation_threads table
            try:
                self.db.dynamodb.create_table(
                    TableName='conversation_threads',
                    KeySchema=[
                        {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                        {'AttributeName': 'user_id', 'AttributeType': 'S'},
                        {'AttributeName': 'updated_at', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'user-updated-index',
                            'KeySchema': [
                                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                                {'AttributeName': 'updated_at', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                        }
                    ],
                    ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                )
                print("✅ Created conversation_threads table")
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"⚠️ Error creating conversation_threads table: {e}")
                    
        except Exception as e:
            print(f"❌ Error ensuring tables exist: {e}")

# Create singleton instance
conversation_memory_service = ConversationMemoryService()
