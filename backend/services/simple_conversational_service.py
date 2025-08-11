"""
Simple Conversational Service (No RAG/Embeddings Required)
==========================================================

This service provides conversation memory without requiring OpenAI embeddings.
It uses the enhanced chatbot service with conversation context.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from services.conversation_memory_service import conversation_memory_service, ConversationMessage
from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat import ChatRequest, ChatResponse

class SimpleConversationalService:
    """Service that provides conversation memory without RAG/embeddings"""
    
    def __init__(self):
        self.memory_service = conversation_memory_service
        self.enhanced_chatbot = EnhancedChatbotService()
        self.max_context_length = 4000  # Maximum characters for context
    
    async def initialize(self):
        """Initialize the service and ensure database tables exist"""
        try:
            # Ensure conversation memory tables exist
            await self.memory_service.ensure_tables_exist()
            print("✅ Simple conversational service initialized")
        except Exception as e:
            print(f"❌ Error initializing simple conversational service: {e}")
    
    async def chat_with_memory(self, request: ChatRequest) -> ChatResponse:
        """
        Process chat request with conversation memory (no RAG/embeddings needed)
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
                include_messages=8  # Get last 8 messages for context
            )
            
            # 2. Add current user message to conversation
            current_message = await self.memory_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                user_id=user_id,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            
            # 3. Generate context-aware response
            response_text = await self._generate_response_with_context(
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
                    "response_source": "simple_conversational",
                    "no_embeddings_required": True
                }
            )
            
        except Exception as e:
            print(f"❌ Error in simple conversational chat: {e}")
            # Fallback response
            return ChatResponse(
                response="I apologize, but I'm experiencing technical difficulties. Please try again.",
                conversation_id=conversation_id,
                message_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                metadata={"error": str(e), "response_source": "fallback"}
            )
    
    async def _generate_response_with_context(
        self,
        user_message: str,
        conversation_context: List[ConversationMessage],
        conversation_id: str,
        user_id: Optional[str]
    ) -> str:
        """Generate response with conversation context using enhanced chatbot"""
        try:
            # Format conversation context for AI
            context_str = await self._format_context_for_ai(conversation_context, user_message)
            
            # Create contextual request for enhanced chatbot
            contextual_request = ChatRequest(
                message=context_str,
                conversation_id=None,  # Don't create nested conversation in enhanced chatbot
                user_id=user_id
            )
            
            # Use enhanced chatbot which has policy knowledge and GROQ fallback
            response = await self.enhanced_chatbot.chat(contextual_request)
            return response.response
            
        except Exception as e:
            print(f"❌ Error generating response with context: {e}")
            return f"I understand you're asking: {user_message}. I'm here to help with policy information and can continue our conversation based on what we've discussed."
    
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
            for message in conversation_context[-6:]:  # Last 6 messages
                role_label = "User" if message.role == "user" else "Assistant"
                # Truncate long messages
                content = message.content[:300] + "..." if len(message.content) > 300 else message.content
                context_parts.append(f"{role_label}: {content}")
            
            context_parts.append("\n**Current Question:**")
        
        context_parts.append(current_message)
        context_parts.append("\n**Instructions:** Please provide a helpful response that considers our conversation history and maintains context continuity.")
        
        full_context = "\n".join(context_parts)
        
        # Ensure context doesn't exceed maximum length
        if len(full_context) > self.max_context_length:
            # Keep current message and instructions, truncate history
            truncated = f"""**Previous conversation context available**

**Current Question:**
{current_message}

**Instructions:** Please provide a helpful response based on our conversation."""
            return truncated
        
        return full_context
    
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

# Create singleton instance
simple_conversational_service = SimpleConversationalService()
