"""
Enhanced Chat Controller with RAG Integration
============================================

This controller integrates the RAG system with the existing chatbot,
providing context-aware responses using conversation history.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from models.chat import ChatRequest, ChatResponse, ChatMessage
from services.rag_chatbot_service import RAGChatbotService
from services.chatbot_service_enhanced import EnhancedChatbotService
from models.rag_models import RAGDatabaseManager

class RAGChatController:
    """Enhanced chat controller with RAG capabilities"""
    
    def __init__(self):
        self.rag_service = RAGChatbotService()
        self.enhanced_chatbot = EnhancedChatbotService()
        # Initialize RAG database manager lazily since DB connection might not be ready
        self.rag_db = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure RAG system is initialized"""
        if not self._initialized:
            await self._initialize_rag_system()
            self._initialized = True
    
    async def _initialize_rag_system(self):
        """Initialize RAG database and system"""
        try:
            # Get database connection
            from config.dynamodb import get_dynamodb
            db_manager = await get_dynamodb()
            self.rag_db = RAGDatabaseManager(db_manager)
            
            await self.rag_db.ensure_rag_tables()
            print("✅ RAG system initialized")
        except Exception as e:
            print(f"❌ Error initializing RAG system: {e}")
    
    async def chat_with_rag(self, request: ChatRequest) -> ChatResponse:
        """Main chat endpoint with RAG enhancement"""
        await self._ensure_initialized()  # Ensure RAG system is ready
        
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Step 1: Check if this is a policy-related query using existing system
            is_policy_query = await self.enhanced_chatbot._is_policy_related_query(request.message)
            
            if is_policy_query:
                # Use enhanced policy chatbot for policy queries
                enhanced_response = await self.enhanced_chatbot.chat(request)
                response_text = enhanced_response.response
                
                # Store policy response in RAG system for future reference
                await self.rag_service.store_conversation(
                    user_message=request.message,
                    bot_response=response_text,
                    conversation_id=conversation_id,
                    user_id=request.user_id
                )
                
                return ChatResponse(
                    response=response_text,
                    conversation_id=enhanced_response.conversation_id,
                    message_id=enhanced_response.message_id,
                    timestamp=enhanced_response.timestamp,
                    metadata={
                        'rag_enabled': True,
                        'query_type': 'policy',
                        'response_source': 'enhanced_policy_chatbot'
                    }
                )
            
            else:
                # Use RAG system for general queries
                rag_response = await self.rag_service.generate_rag_response(
                    query=request.message,
                    conversation_id=conversation_id,
                    user_id=request.user_id
                )
                
                return ChatResponse(
                    response=rag_response,
                    conversation_id=conversation_id,
                    message_id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow(),
                    metadata={
                        'rag_enabled': True,
                        'query_type': 'general',
                        'response_source': 'rag_system'
                    }
                )
            
        except Exception as e:
            print(f"❌ Error in RAG chat: {e}")
            raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
    
    async def chat_with_context_search(self, request: ChatRequest, search_params: Optional[Dict] = None) -> ChatResponse:
        """Chat with explicit context search parameters"""
        try:
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Custom retrieval parameters
            if search_params:
                # Temporarily modify RAG service parameters
                original_max_retrieved = self.rag_service.max_retrieved_conversations
                original_threshold = self.rag_service.similarity_threshold
                
                self.rag_service.max_retrieved_conversations = search_params.get('max_conversations', 5)
                self.rag_service.similarity_threshold = search_params.get('similarity_threshold', 0.7)
            
            # Generate response with custom parameters
            response = await self.rag_service.generate_rag_response(
                query=request.message,
                conversation_id=conversation_id,
                user_id=request.user_id
            )
            
            # Restore original parameters
            if search_params:
                self.rag_service.max_retrieved_conversations = original_max_retrieved
                self.rag_service.similarity_threshold = original_threshold
            
            return ChatResponse(
                response=response,
                conversation_id=conversation_id,
                message_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                metadata={
                    'rag_enabled': True,
                    'custom_search_params': search_params,
                    'response_source': 'rag_custom_search'
                }
            )
            
        except Exception as e:
            print(f"❌ Error in context search chat: {e}")
            raise HTTPException(status_code=500, detail=f"Context search error: {str(e)}")
    
    async def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context and related conversations"""
        try:
            # Get the specific conversation
            conversation = await self.rag_db.get_conversation_by_id(conversation_id)
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Find related conversations
            related_conversations = await self.rag_service.retrieve_relevant_conversations(
                query=conversation.user_message,
                user_id=conversation.user_id
            )
            
            return {
                'conversation': {
                    'id': conversation.conversation_id,
                    'user_message': conversation.user_message,
                    'bot_response': conversation.bot_response,
                    'timestamp': conversation.timestamp.isoformat(),
                    'keywords': conversation.keywords,
                    'metadata': conversation.metadata
                },
                'related_conversations': [
                    {
                        'id': result.conversation_entry.conversation_id,
                        'user_message': result.conversation_entry.user_message,
                        'bot_response': result.conversation_entry.bot_response,
                        'relevance_score': result.relevance_score,
                        'similarity_score': result.similarity_score,
                        'keyword_matches': result.keyword_matches
                    }
                    for result in related_conversations
                ]
            }
            
        except Exception as e:
            print(f"❌ Error getting conversation context: {e}")
            raise HTTPException(status_code=500, detail=f"Context retrieval error: {str(e)}")
    
    async def search_conversations(self, query: str, user_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Search conversations using RAG system"""
        try:
            results = await self.rag_service.retrieve_relevant_conversations(
                query=query,
                user_id=user_id
            )
            
            return {
                'query': query,
                'total_results': len(results),
                'results': [
                    {
                        'conversation_id': result.conversation_entry.conversation_id,
                        'user_message': result.conversation_entry.user_message,
                        'bot_response': result.conversation_entry.bot_response,
                        'timestamp': result.conversation_entry.timestamp.isoformat(),
                        'relevance_score': result.relevance_score,
                        'similarity_score': result.similarity_score,
                        'keyword_matches': result.keyword_matches,
                        'keywords': result.conversation_entry.keywords
                    }
                    for result in results[:limit]
                ]
            }
            
        except Exception as e:
            print(f"❌ Error searching conversations: {e}")
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
    
    async def get_user_conversation_history(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get user's conversation history"""
        try:
            conversations = await self.rag_db.get_user_conversations(user_id, limit)
            
            return {
                'user_id': user_id,
                'total_conversations': len(conversations),
                'conversations': [
                    {
                        'conversation_id': conv.conversation_id,
                        'user_message': conv.user_message,
                        'bot_response': conv.bot_response,
                        'timestamp': conv.timestamp.isoformat(),
                        'keywords': conv.keywords,
                        'metadata': conv.metadata
                    }
                    for conv in conversations
                ]
            }
            
        except Exception as e:
            print(f"❌ Error getting user history: {e}")
            raise HTTPException(status_code=500, detail=f"History retrieval error: {str(e)}")
    
    async def initialize_rag_from_existing_data(self) -> Dict[str, Any]:
        """Initialize RAG system from existing conversation data"""
        try:
            # Run initialization
            await self.rag_service.initialize_from_existing_conversations()
            
            # Get stats
            stats = self.rag_service.get_system_stats()
            db_stats = await self.rag_db.get_database_stats()
            
            return {
                'status': 'success',
                'message': 'RAG system initialized from existing data',
                'rag_stats': stats,
                'database_stats': db_stats
            }
            
        except Exception as e:
            print(f"❌ Error initializing RAG from existing data: {e}")
            raise HTTPException(status_code=500, detail=f"Initialization error: {str(e)}")
    
    async def get_rag_system_status(self) -> Dict[str, Any]:
        """Get comprehensive RAG system status"""
        try:
            rag_stats = self.rag_service.get_system_stats()
            db_stats = await self.rag_db.get_database_stats()
            
            return {
                'status': 'operational',
                'rag_service': rag_stats,
                'database': db_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error getting RAG status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Delete a conversation from RAG system"""
        try:
            success = await self.rag_db.delete_conversation(conversation_id)
            
            if success:
                return {
                    'status': 'success',
                    'message': f'Conversation {conversation_id} deleted successfully'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Conversation {conversation_id} not found or could not be deleted'
                }
                
        except Exception as e:
            print(f"❌ Error deleting conversation: {e}")
            raise HTTPException(status_code=500, detail=f"Deletion error: {str(e)}")

# Create router for RAG endpoints
def create_rag_router() -> APIRouter:
    """Create FastAPI router for RAG endpoints"""
    router = APIRouter(prefix="/rag", tags=["RAG Chat"])
    rag_controller = RAGChatController()
    
    @router.post("/chat", response_model=ChatResponse)
    async def rag_chat(request: ChatRequest):
        """Chat with RAG enhancement"""
        return await rag_controller.chat_with_rag(request)
    
    @router.post("/chat/search")
    async def rag_chat_with_search(request: ChatRequest, search_params: Optional[Dict] = None):
        """Chat with custom search parameters"""
        return await rag_controller.chat_with_context_search(request, search_params)
    
    @router.get("/conversation/{conversation_id}")
    async def get_conversation_context(conversation_id: str):
        """Get conversation context and related conversations"""
        return await rag_controller.get_conversation_context(conversation_id)
    
    @router.get("/search")
    async def search_conversations(query: str, user_id: Optional[str] = None, limit: int = 10):
        """Search conversations using RAG system"""
        return await rag_controller.search_conversations(query, user_id, limit)
    
    @router.get("/history/{user_id}")
    async def get_user_history(user_id: str, limit: int = 50):
        """Get user's conversation history"""
        return await rag_controller.get_user_conversation_history(user_id, limit)
    
    @router.post("/initialize")
    async def initialize_rag():
        """Initialize RAG system from existing data"""
        return await rag_controller.initialize_rag_from_existing_data()
    
    @router.get("/status")
    async def get_rag_status():
        """Get RAG system status"""
        return await rag_controller.get_rag_system_status()
    
    @router.delete("/conversation/{conversation_id}")
    async def delete_conversation(conversation_id: str):
        """Delete a conversation"""
        return await rag_controller.delete_conversation(conversation_id)
    
    return router

# Create the router instance for easy import
router = create_rag_router()
