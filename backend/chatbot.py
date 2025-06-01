from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import asyncio
import motor.motor_asyncio
from bson import ObjectId

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)

# Pydantic Models for Chatbot
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime

class ChatConversation(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

class PolicyChatbot:
    def __init__(self, db_client):
        self.db = db_client.ai_policy_database
        self.conversations_collection = self.db.chat_conversations
        self.master_policies_collection = self.db.master_policies
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # System prompt for the chatbot
        self.system_prompt = """
        You are an AI Policy Expert Assistant for a global AI policy database. Your role is to help users understand AI policies, governance frameworks, and related topics.

        Your capabilities include:
        1. Answering questions about AI policies and governance
        2. Providing information about specific countries' AI policies
        3. Explaining policy frameworks, implementation strategies, and evaluation metrics
        4. Discussing AI ethics, safety, and regulatory approaches
        5. Helping users understand policy trends and comparisons

        Guidelines:
        - Be informative, accurate, and helpful
        - Use clear, professional language
        - When discussing specific policies, reference the database when possible
        - Provide context and explanations for complex topics
        - If you don't have specific information, be honest about limitations
        - Focus on educational and informational responses
        - Avoid giving legal advice - instead, provide general information and suggest consulting experts

        Remember: You have access to a database of AI policies from various countries. Use this context to provide relevant and specific information when available.
        """

    async def get_policy_context(self, query: str) -> str:
        """Get relevant policy context from the database based on the query"""
        try:
            # Simple keyword-based search (you can enhance this with vector search later)
            keywords = query.lower().split()
            
            # Build search query for MongoDB
            search_conditions = []
            for keyword in keywords:
                search_conditions.extend([
                    {"policyName": {"$regex": keyword, "$options": "i"}},
                    {"policyDescription": {"$regex": keyword, "$options": "i"}},
                    {"country": {"$regex": keyword, "$options": "i"}},
                    {"policyArea": {"$regex": keyword, "$options": "i"}}
                ])
            
            if search_conditions:
                # Find relevant policies
                cursor = self.master_policies_collection.find(
                    {
                        "$and": [
                            {"master_status": {"$ne": "deleted"}},
                            {"$or": search_conditions}
                        ]
                    }
                ).limit(5)
                
                policies = []
                async for policy in cursor:
                    policies.append({
                        "country": policy.get("country", ""),
                        "name": policy.get("policyName", ""),
                        "area": policy.get("policyArea", ""),
                        "description": policy.get("policyDescription", "")[:300] + "..." if len(policy.get("policyDescription", "")) > 300 else policy.get("policyDescription", ""),
                        "year": policy.get("implementation", {}).get("deploymentYear", "N/A")
                    })
                
                if policies:
                    context = "\n\nRelevant policies from the database:\n"
                    for policy in policies:
                        context += f"- {policy['country']}: {policy['name']} ({policy['area']}, {policy['year']})\n  {policy['description']}\n\n"
                    return context
            
            return ""
            
        except Exception as e:
            print(f"Error getting policy context: {e}")
            return ""

    async def get_conversation(self, conversation_id: str) -> Optional[ChatConversation]:
        """Retrieve a conversation from the database"""
        try:
            conversation_doc = await self.conversations_collection.find_one(
                {"conversation_id": conversation_id}
            )
            if conversation_doc:
                return ChatConversation(**conversation_doc)
            return None
        except Exception as e:
            print(f"Error retrieving conversation: {e}")
            return None

    async def save_conversation(self, conversation: ChatConversation):
        """Save or update a conversation in the database"""
        try:
            conversation_dict = conversation.dict()
            await self.conversations_collection.update_one(
                {"conversation_id": conversation.conversation_id},
                {"$set": conversation_dict},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def generate_response(self, message: str, conversation_history: List[ChatMessage], context: str = "") -> str:
        """Generate a response using Gemini API"""
        try:
            # Prepare the conversation for Gemini
            chat_history = []
            
            # Add system prompt
            full_prompt = self.system_prompt
            if context:
                full_prompt += context
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                if msg.role == "user":
                    chat_history.append({"role": "user", "parts": [msg.content]})
                else:
                    chat_history.append({"role": "model", "parts": [msg.content]})
            
            # Add current message
            chat_history.append({"role": "user", "parts": [message]})
            
            # Start chat with history
            chat = self.model.start_chat(history=chat_history[:-1])
            
            # Generate response
            full_message = f"{full_prompt}\n\nUser: {message}"
            response = await asyncio.to_thread(chat.send_message, message)
            
            return response.text
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again later."

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat function"""
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(ObjectId())
            
            # Get existing conversation or create new one
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                conversation = ChatConversation(
                    conversation_id=conversation_id,
                    messages=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            
            # Get policy context if needed
            policy_context = await self.get_policy_context(request.message)
            full_context = request.context or ""
            if policy_context:
                full_context += policy_context
            
            # Generate response
            response_text = await self.generate_response(
                request.message, 
                conversation.messages, 
                full_context
            )
            
            # Add messages to conversation
            user_message = ChatMessage(
                role="user",
                content=request.message,
                timestamp=datetime.utcnow()
            )
            assistant_message = ChatMessage(
                role="assistant", 
                content=response_text,
                timestamp=datetime.utcnow()
            )
            
            conversation.messages.extend([user_message, assistant_message])
            conversation.updated_at = datetime.utcnow()
            
            # Save conversation
            await self.save_conversation(conversation)
            
            return ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

    async def get_conversation_history(self, conversation_id: str) -> List[ChatMessage]:
        """Get conversation history"""
        try:
            conversation = await self.get_conversation(conversation_id)
            return conversation.messages if conversation else []
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            result = await self.conversations_collection.delete_one(
                {"conversation_id": conversation_id}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    async def get_user_conversations(self, limit: int = 20) -> List[Dict]:
        """Get list of recent conversations (you can add user filtering later)"""
        try:
            cursor = self.conversations_collection.find().sort("updated_at", -1).limit(limit)
            conversations = []
            async for conv in cursor:
                # Get last message for preview
                last_message = conv["messages"][-1] if conv["messages"] else None
                conversations.append({
                    "conversation_id": conv["conversation_id"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "message_count": len(conv["messages"]),
                    "last_message": last_message["content"][:100] + "..." if last_message and len(last_message["content"]) > 100 else last_message["content"] if last_message else ""
                })
            return conversations
        except Exception as e:
            print(f"Error getting user conversations: {e}")
            return []

# Helper function to convert ObjectId to string for JSON serialization
def convert_objectid_chat(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_chat(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_chat(item) for item in obj]
    return obj

# Initialize chatbot instance (will be done in main.py)
chatbot_instance = None

def init_chatbot(db_client):
    """Initialize chatbot with database client"""
    global chatbot_instance
    chatbot_instance = PolicyChatbot(db_client)
    return chatbot_instance

# FastAPI route functions (to be imported in main.py)
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint"""
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    response = await chatbot_instance.chat(request)
    return response

async def get_conversation_endpoint(conversation_id: str):
    """Get conversation history endpoint"""
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    messages = await chatbot_instance.get_conversation_history(conversation_id)
    return {"conversation_id": conversation_id, "messages": [convert_objectid_chat(msg.dict()) for msg in messages]}

async def delete_conversation_endpoint(conversation_id: str):
    """Delete conversation endpoint"""
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    success = await chatbot_instance.delete_conversation(conversation_id)
    return {"success": success, "message": "Conversation deleted" if success else "Conversation not found"}

async def get_conversations_endpoint(limit: int = 20):
    """Get conversations list endpoint"""
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    conversations = await chatbot_instance.get_user_conversations(limit)
    return {"conversations": convert_objectid_chat(conversations)}