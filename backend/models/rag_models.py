"""
Enhanced Database Models for RAG Chatbot
========================================

This module extends the existing database models to support RAG functionality:
- Conversation embeddings storage
- Semantic search capabilities
- Keyword indexing
- Performance optimization
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

@dataclass
class ConversationEmbedding:
    """Model for storing conversation embeddings"""
    conversation_id: str
    user_id: str
    user_message: str
    bot_response: str
    embedding: List[float]  # Vector embedding
    keywords: List[str]     # Extracted keywords for search
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dynamo_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'user_message': self.user_message,
            'bot_response': self.bot_response,
            'timestamp': self.timestamp.isoformat(),
            'embedding': self.embedding,
            'keywords': self.keywords,
            'metadata': json.dumps(self.metadata),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
    
    @classmethod
    def from_dynamo_item(cls, item: Dict[str, Any]) -> 'ConversationEmbedding':
        """Create from DynamoDB item"""
        return cls(
            conversation_id=item['conversation_id'],
            user_id=item['user_id'],
            user_message=item['user_message'],
            bot_response=item['bot_response'],
            timestamp=datetime.fromisoformat(item['timestamp']),
            embedding=item.get('embedding', []),
            keywords=item.get('keywords', []),
            metadata=json.loads(item.get('metadata', '{}'))
        )

@dataclass
class RAGSearchResult:
    """Model for RAG search results"""
    conversation: ConversationEmbedding
    similarity_score: float
    keyword_matches: int
    relevance_score: float
    search_type: str  # 'semantic', 'keyword', 'hybrid'

class RAGDatabaseManager:
    """
    Enhanced database manager for RAG functionality
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.embedding_table = 'conversation_embeddings'
        self.keyword_index_table = 'keyword_index'
    
    async def ensure_rag_tables(self):
        """Ensure all RAG-related tables exist"""
        try:
            # Conversation embeddings table
            embedding_table_schema = {
                'TableName': self.embedding_table,
                'KeySchema': [
                    {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'user-timestamp-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                'BillingMode': 'PAY_PER_REQUEST'
            }
            
            # Create tables if they don't exist
            await self._create_table_if_not_exists(embedding_table_schema)
            
            # Keyword index table for fast keyword search
            keyword_table_schema = {
                'TableName': self.keyword_index_table,
                'KeySchema': [
                    {'AttributeName': 'keyword', 'KeyType': 'HASH'},
                    {'AttributeName': 'conversation_id', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'keyword', 'AttributeType': 'S'},
                    {'AttributeName': 'conversation_id', 'AttributeType': 'S'}
                ],
                'BillingMode': 'PAY_PER_REQUEST'
            }
            
            await self._create_table_if_not_exists(keyword_table_schema)
            
            print("✅ RAG database tables initialized successfully")
            
        except Exception as e:
            print(f"❌ Error creating RAG tables: {e}")
            raise
    
    async def _create_table_if_not_exists(self, table_schema: Dict[str, Any]):
        """Create table if it doesn't exist"""
        try:
            table_name = table_schema['TableName']
            
            # Check if table exists
            # Check if tables already exist
            existing_tables = self.db.client.list_tables()['TableNames']
            
            if table_name not in existing_tables:
                # Create the table using client directly
                self.db.client.create_table(**table_schema)
                print(f"✅ Created table: {table_name}")
            else:
                print(f"ℹ️ Table already exists: {table_name}")
                
        except Exception as e:
            print(f"❌ Error creating table {table_schema['TableName']}: {e}")
    
    async def store_conversation_embedding(self, conversation: ConversationEmbedding) -> bool:
        """Store conversation with embedding"""
        try:
            # Store main conversation record
            item = conversation.to_dynamo_item()
            await self.db.put_item(self.embedding_table, item)
            
            # Store keyword index entries
            await self._index_keywords(conversation.conversation_id, conversation.keywords)
            
            return True
            
        except Exception as e:
            print(f"❌ Error storing conversation embedding: {e}")
            return False
    
    async def _index_keywords(self, conversation_id: str, keywords: List[str]):
        """Index keywords for fast search"""
        try:
            for keyword in keywords:
                keyword_item = {
                    'keyword': keyword.lower(),
                    'conversation_id': conversation_id,
                    'indexed_at': datetime.utcnow().isoformat()
                }
                await self.db.put_item(self.keyword_index_table, keyword_item)
                
        except Exception as e:
            print(f"❌ Error indexing keywords: {e}")
    
    async def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Fast keyword-based search using keyword index"""
        try:
            conversation_ids = set()
            keyword_counts = {}
            
            # Query keyword index for each keyword
            for keyword in keywords:
                response = await self.db.query_items(
                    table_name=self.keyword_index_table,
                    key_condition_expression='keyword = :keyword',
                    expression_attribute_values={':keyword': keyword.lower()},
                    limit=100
                )
                
                for item in response:
                    conv_id = item['conversation_id']
                    conversation_ids.add(conv_id)
                    keyword_counts[conv_id] = keyword_counts.get(conv_id, 0) + 1
            
            # Get full conversation records
            conversations = []
            for conv_id in list(conversation_ids)[:limit]:
                conv_data = await self.db.get_item(self.embedding_table, {'conversation_id': conv_id})
                if conv_data:
                    conv_data['keyword_matches'] = keyword_counts.get(conv_id, 0)
                    conversations.append(conv_data)
            
            # Sort by keyword matches
            conversations.sort(key=lambda x: x.get('keyword_matches', 0), reverse=True)
            
            return conversations
            
        except Exception as e:
            print(f"❌ Error in keyword search: {e}")
            return []
    
    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[ConversationEmbedding]:
        """Get conversations for a specific user"""
        try:
            response = await self.db.query_items(
                table_name=self.embedding_table,
                index_name='user-timestamp-index',
                key_condition_expression='user_id = :user_id',
                expression_attribute_values={':user_id': user_id},
                scan_index_forward=False,  # Latest first
                limit=limit
            )
            
            conversations = []
            for item in response:
                conversations.append(ConversationEmbedding.from_dynamo_item(item))
            
            return conversations
            
        except Exception as e:
            print(f"❌ Error getting user conversations: {e}")
            return []
    
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[ConversationEmbedding]:
        """Get specific conversation by ID"""
        try:
            item = await self.db.get_item(self.embedding_table, {'conversation_id': conversation_id})
            
            if item:
                return ConversationEmbedding.from_dynamo_item(item)
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting conversation: {e}")
            return None
    
    async def get_recent_conversations(self, hours: int = 24, limit: int = 100) -> List[ConversationEmbedding]:
        """Get recent conversations across all users"""
        try:
            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            response = await self.db.scan_table(
                table_name=self.embedding_table,
                filter_expression='#ts > :cutoff',
                expression_attribute_names={'#ts': 'timestamp'},
                expression_attribute_values={':cutoff': cutoff_time},
                limit=limit
            )
            
            conversations = []
            for item in response:
                conversations.append(ConversationEmbedding.from_dynamo_item(item))
            
            # Sort by timestamp (latest first)
            conversations.sort(key=lambda x: x.timestamp, reverse=True)
            
            return conversations
            
        except Exception as e:
            print(f"❌ Error getting recent conversations: {e}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and its keyword indices"""
        try:
            # Get conversation to find keywords
            conversation = await self.get_conversation_by_id(conversation_id)
            
            if conversation:
                # Delete keyword indices
                for keyword in conversation.keywords:
                    await self.db.delete_item(
                        self.keyword_index_table,
                        {'keyword': keyword.lower(), 'conversation_id': conversation_id}
                    )
                
                # Delete main record
                await self.db.delete_item(
                    self.embedding_table,
                    {'conversation_id': conversation_id}
                )
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error deleting conversation: {e}")
            return False
    
    async def update_conversation_metadata(self, conversation_id: str, metadata: Dict[str, Any]) -> bool:
        """Update conversation metadata"""
        try:
            await self.db.update_item(
                table_name=self.embedding_table,
                key={'conversation_id': conversation_id},
                update_expression='SET metadata = :metadata, updated_at = :updated_at',
                expression_attribute_values={
                    ':metadata': json.dumps(metadata),
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating conversation metadata: {e}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Count conversations
            embedding_response = await self.db.scan_table(
                table_name=self.embedding_table,
                select='COUNT'
            )
            conversation_count = len(embedding_response)
            
            # Count keyword entries
            keyword_response = await self.db.scan_table(
                table_name=self.keyword_index_table,
                select='COUNT'
            )
            keyword_count = len(keyword_response)
            
            return {
                'total_conversations': conversation_count,
                'total_keyword_entries': keyword_count,
                'embedding_table': self.embedding_table,
                'keyword_index_table': self.keyword_index_table,
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {}

# Utility functions for data migration
async def migrate_existing_conversations_to_rag(db_manager, rag_service):
    """Migrate existing conversations to RAG format"""
    try:
        print("🔄 Starting conversation migration to RAG format...")
        
        # Get existing chat sessions
        sessions = await db_manager.scan_table('chat_sessions')
        
        migrated = 0
        for session in sessions:
            session_id = session.get('session_id', '')
            user_id = session.get('user_id', 'anonymous')
            messages = session.get('messages', [])
            
            # Process message pairs
            for i in range(0, len(messages) - 1, 2):
                if i + 1 < len(messages):
                    user_msg = messages[i]
                    bot_msg = messages[i + 1]
                    
                    if (user_msg.get('role') == 'user' and 
                        bot_msg.get('role') == 'assistant'):
                        
                        # Create conversation ID
                        conv_id = f"{session_id}_{i // 2}"
                        
                        # Store in RAG format
                        success = await rag_service.store_conversation(
                            user_message=user_msg.get('content', ''),
                            bot_response=bot_msg.get('content', ''),
                            conversation_id=conv_id,
                            user_id=user_id
                        )
                        
                        if success:
                            migrated += 1
        
        print(f"✅ Migration completed: {migrated} conversations migrated")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
