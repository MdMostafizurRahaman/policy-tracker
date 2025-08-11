"""
Enhanced Conversational RAG Service
==================================

This service combines conversation memory with RAG capabilities to provide
context-aware responses that remember previous messages in the conversation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json

from services.conversation_memory_service import conversation_memory_service, ConversationMessage
from services.rag_chatbot_service import RAGChatbotService
from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat import ChatRequest, ChatResponse, ChatMessage

class ConversationalRAGService:
    """Service that combines conversation memory with RAG for context-aware responses"""
    
    def __init__(self):
        self.memory_service = conversation_memory_service
        self.rag_service = RAGChatbotService()
        self.enhanced_chatbot = EnhancedChatbotService()
        self.max_context_length = 4000  # Maximum characters for context
        self.use_rag_for_general = False  # Disable RAG temporarily due to OpenAI quota
        self.use_policy_bot_for_policy = True  # Use enhanced policy bot for policy queries
        self.openai_available = False  # Track OpenAI availability
    
    async def initialize(self):
        """Initialize all services and ensure database tables exist"""
        try:
            # Ensure conversation memory tables exist
            await self.memory_service.ensure_tables_exist()
            
            # Initialize RAG service
            await self.rag_service.ensure_db_connection()
            
            print("✅ Conversational RAG service initialized")
        except Exception as e:
            print(f"❌ Error initializing conversational RAG service: {e}")
    
    async def chat_with_memory(self, request: ChatRequest) -> ChatResponse:
        """
        Process chat request with full conversation memory and context
        
        Args:
            request: ChatRequest containing message and conversation details
        
        Returns:
            ChatResponse with context-aware response
        """
        try:
            # Ensure initialization
            await self.initialize()
            
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(uuid.uuid4())
            user_id = request.user_id
            user_message = request.message
            
            # 1. Get conversation context (previous messages)
            conversation_context = await self.memory_service.get_conversation_context(
                conversation_id=conversation_id,
                include_messages=10  # Get last 10 messages for context
            )
            
            # 2. Add current user message to conversation
            current_message = await self.memory_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                user_id=user_id,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            
            # 3. Determine query type and generate response
            response_text = await self._generate_contextual_response(
                user_message=user_message,
                conversation_context=conversation_context,
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            # 4. Add assistant response to conversation
            await self.memory_service.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_text,
                user_id=user_id,
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_used": len(conversation_context) > 0,
                    "context_messages": len(conversation_context)
                }
            )
            
            # 5. Create response
            return ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                message_id=current_message.message_id,
                timestamp=datetime.utcnow(),
                metadata={
                    "conversation_context_used": len(conversation_context) > 0,
                    "context_messages_count": len(conversation_context),
                    "response_source": "conversational_rag"
                }
            )
            
        except Exception as e:
            print(f"❌ Error in conversational chat: {e}")
            # Fallback response
            return ChatResponse(
                response="I apologize, but I'm experiencing technical difficulties. Please try again.",
                conversation_id=conversation_id,
                message_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                metadata={"error": str(e), "response_source": "fallback"}
            )
    
    async def _generate_contextual_response(
        self,
        user_message: str,
        conversation_context: List[ConversationMessage],
        conversation_id: str,
        user_id: Optional[str]
    ) -> str:
        """
        Generate a response using conversation context and appropriate AI service
        
        Args:
            user_message: Current user message
            conversation_context: Previous messages in conversation
            conversation_id: Conversation ID
            user_id: User ID
        
        Returns:
            Generated response text
        """
        try:
            # Check if this is a policy-related query
            is_policy_query = await self.enhanced_chatbot._is_policy_related_query(user_message)
            
            # Format conversation context
            context_str = await self._format_context_for_ai(conversation_context, user_message)
            
            if is_policy_query and self.use_policy_bot_for_policy:
                # Use enhanced policy chatbot with context
                return await self._generate_policy_response_with_context(
                    user_message, context_str, conversation_id, user_id
                )
            
            elif self.use_rag_for_general and self.openai_available:
                # Use RAG system with conversation context (only if OpenAI is available)
                return await self._generate_rag_response_with_context(
                    user_message, context_str, conversation_id, user_id
                )
            
            else:
                # Use basic enhanced chatbot with context (fallback when OpenAI quota exceeded)
                return await self._generate_basic_response_with_context(
                    user_message, context_str
                )
                
        except Exception as e:
            print(f"❌ Error generating contextual response: {e}")
            return "I apologize, but I'm having trouble processing your request. Please try again."
    
    async def _format_context_for_ai(
        self, 
        conversation_context: List[ConversationMessage], 
        current_message: str
    ) -> str:
        """Format conversation context for AI consumption"""
        if not conversation_context:
            return current_message
        
        context_parts = []
        
        # Add conversation history
        if conversation_context:
            context_parts.append("**Previous Conversation:**")
            for message in conversation_context[-6:]:  # Last 6 messages to avoid too much context
                role_label = "User" if message.role == "user" else "Assistant"
                # Truncate long messages
                content = message.content[:200] + "..." if len(message.content) > 200 else message.content
                context_parts.append(f"{role_label}: {content}")
            
            context_parts.append("\n**Current Question:**")
        
        context_parts.append(current_message)
        
        full_context = "\n".join(context_parts)
        
        # Ensure context doesn't exceed maximum length
        if len(full_context) > self.max_context_length:
            # Truncate from the beginning but keep current message
            truncated = "...[previous conversation truncated]...\n" + current_message
            return truncated
        
        return full_context
    
    async def _generate_policy_response_with_context(
        self,
        user_message: str,
        context: str,
        conversation_id: str,
        user_id: Optional[str]
    ) -> str:
        """Generate policy response with conversation context"""
        try:
            # Create a modified request with context
            contextual_request = ChatRequest(
                message=f"""Based on our previous conversation context:

{context}

Please provide a comprehensive answer considering our conversation history.""",
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            # Get response from enhanced policy chatbot
            response = await self.enhanced_chatbot.chat(contextual_request)
            return response.response
            
        except Exception as e:
            print(f"❌ Error generating policy response with context: {e}")
            # Fallback to basic policy response
            basic_request = ChatRequest(
                message=user_message,
                conversation_id=conversation_id,
                user_id=user_id
            )
            response = await self.enhanced_chatbot.chat(basic_request)
            return response.response
    
    async def _generate_rag_response_with_context(
        self,
        user_message: str,
        context: str,
        conversation_id: str,
        user_id: Optional[str]
    ) -> str:
        """Generate RAG response with conversation context"""
        try:
            # Use RAG system with enhanced context
            rag_response = await self.rag_service.generate_rag_response(
                query=context,  # Pass the full context as query
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            return rag_response
            
        except Exception as e:
            print(f"❌ Error generating RAG response with context: {e}")
            # Fallback to basic RAG response
            return await self.rag_service.generate_rag_response(
                query=user_message,
                conversation_id=conversation_id,
                user_id=user_id
            )
    
    async def _generate_basic_response_with_context(
        self,
        user_message: str,
        context: str
    ) -> str:
        """Generate basic AI response with conversation context using enhanced chatbot"""
        try:
            # Use the enhanced chatbot with context-enhanced message
            contextual_message = f"""Based on our conversation context:

{context}

Please provide a response that takes into account our conversation history."""
            
            # Create a request for the enhanced chatbot
            from models.chat import ChatRequest
            contextual_request = ChatRequest(
                message=contextual_message,
                conversation_id=None,  # Don't create new conversation in enhanced chatbot
                user_id=None
            )
            
            # Use enhanced chatbot which has fallbacks and doesn't require OpenAI embeddings
            response = await self.enhanced_chatbot.chat(contextual_request)
            return response.response
            
        except Exception as e:
            print(f"❌ Error generating basic response with context: {e}")
            # Simple fallback response
            return f"I understand you're asking about: {user_message}. Based on our conversation, I'll try to help with relevant information about policies and governance."
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        try:
            thread = await self.memory_service.get_conversation_thread(conversation_id)
            
            if not thread:
                return {"error": "Conversation not found"}
            
            # Basic statistics
            total_messages = len(thread.messages)
            user_messages = [msg for msg in thread.messages if msg.role == "user"]
            assistant_messages = [msg for msg in thread.messages if msg.role == "assistant"]
            
            # Get recent messages for preview
            recent_messages = thread.messages[-6:] if thread.messages else []
            
            return {
                "conversation_id": conversation_id,
                "total_messages": total_messages,
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat(),
                "recent_messages": [
                    {
                        "role": msg.role,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in recent_messages
                ]
            }
            
        except Exception as e:
            print(f"❌ Error getting conversation summary: {e}")
            return {"error": str(e)}
    
    async def search_conversations_with_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search conversations considering full conversation context"""
        try:
            # Get RAG search results
            rag_results = await self.rag_service.retrieve_relevant_conversations(
                query=query,
                user_id=user_id
            )
            
            # Enhance results with conversation context
            enhanced_results = []
            for result in rag_results[:limit]:
                # Get full conversation thread for context
                thread = await self.memory_service.get_conversation_thread(
                    result.conversation_entry.conversation_id
                )
                
                enhanced_result = {
                    "conversation_id": result.conversation_entry.conversation_id,
                    "relevance_score": result.relevance_score,
                    "similarity_score": result.similarity_score,
                    "keyword_matches": result.keyword_matches,
                    "matched_message": {
                        "user_message": result.conversation_entry.user_message,
                        "bot_response": result.conversation_entry.bot_response,
                        "timestamp": result.conversation_entry.timestamp.isoformat()
                    }
                }
                
                # Add conversation context if available
                if thread:
                    enhanced_result["conversation_context"] = {
                        "total_messages": len(thread.messages),
                        "created_at": thread.created_at.isoformat(),
                        "updated_at": thread.updated_at.isoformat(),
                        "recent_messages": [
                            {
                                "role": msg.role,
                                "content": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                            }
                            for msg in thread.messages[-3:]  # Last 3 messages for context
                        ]
                    }
                
                enhanced_results.append(enhanced_result)
            
            return {
                "query": query,
                "total_results": len(enhanced_results),
                "results": enhanced_results
            }
            
        except Exception as e:
            print(f"❌ Error searching conversations with context: {e}")
            return {"error": str(e)}

# Create singleton instance
conversational_rag_service = ConversationalRAGService()
