import google.generativeai as genai
import asyncio
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import HTTPException

from ..models.chat_models import ChatMessage, ChatRequest, ChatResponse, ChatConversation
from ..database.helpers import convert_objectid as convert_objectid_chat
from ..database.connection import get_db

class PolicyChatbot:
    def __init__(self, db_client):
        self.db = db_client.ai_policy_database
        self.conversations_collection = self.db.chat_conversations
        self.master_policies_collection = self.db.master_policies
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.system_prompt = """
        You are an AI Policy Expert Assistant for a global AI policy database. Your role is to help users understand AI policies, governance frameworks, and related topics.
        [Previous system prompt content...]
        """

    async def get_policy_context(self, query: str) -> str:
        """Get relevant policy context from the database"""
        try:
            keywords = query.lower().split()
            search_conditions = []
            
            for keyword in keywords:
                search_conditions.extend([
                    {"policyName": {"$regex": keyword, "$options": "i"}},
                    {"policyDescription": {"$regex": keyword, "$options": "i"}},
                    {"country": {"$regex": keyword, "$options": "i"}},
                    {"policyArea": {"$regex": keyword, "$options": "i"}}
                ])
            
            if search_conditions:
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
            await self.conversations_collection.update_one(
                {"conversation_id": conversation.conversation_id},
                {"$set": conversation.dict()},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def generate_response(self, message: str, conversation_history: List[ChatMessage], context: str = "") -> str:
        """Generate a response using Gemini API"""
        try:
            # Prepare the conversation for Gemini
            chat_history = [msg.dict() for msg in conversation_history]
            return await generate_gemini_response(
                model=self.model,
                system_prompt=self.system_prompt,
                conversation_history=chat_history,
                user_message=message,
                context=context
            )
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
        """Get list of recent conversations"""
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
        
# Initialize chatbot instance
chatbot_instance = None

def init_chatbot(db_client):
    global chatbot_instance
    chatbot_instance = PolicyChatbot(db_client)
    return chatbot_instance

# Example in main.py
from backend.chatbot.chatbot import init_chatbot
from backend.database.connection import get_db_client

@app.on_event("startup")
async def startup_event():
    db_client = get_db_client()
    init_chatbot(db_client)