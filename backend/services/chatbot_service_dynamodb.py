"""
DynamoDB Chatbot service for AI policy database queries.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import difflib
import json
import os
import requests
import uuid

from models.chat import ChatMessage, ChatRequest, ChatResponse, ChatConversation
from config.dynamodb import get_dynamodb
from utils.helpers import convert_objectid


class ChatbotService:
    def __init__(self):
        self._db = None
        
        # AI API configuration
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Common greetings and help responses
        self.greeting_responses = [
            "Hello! I'm your AI Policy Assistant. How can I help you explore global AI policies today?",
            "Hi there! I can help you find information about AI policies worldwide. What would you like to know?",
            "Welcome! I'm here to assist you with AI policy information. What questions do you have?",
        ]
        
        self.help_responses = [
            "I can help you with:\n• Finding AI policies by country\n• Searching policy content\n• Comparing policies across regions\n• Understanding policy frameworks\n\nWhat would you like to explore?",
            "Here's what I can do:\n• Search for specific AI policies\n• Provide policy summaries\n• Compare different countries' approaches\n• Answer questions about AI governance\n\nHow can I assist you?",
        ]

    async def get_db(self):
        """Get DynamoDB client"""
        if not self._db:
            self._db = await get_dynamodb()
        return self._db

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process chat request and return response"""
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(request.conversation_id, request.user_id)
            
            # Add user message to conversation
            user_message = ChatMessage(
                id=str(uuid.uuid4()),
                content=request.message,
                is_user=True,
                timestamp=datetime.utcnow()
            )
            conversation.messages.append(user_message)
            
            # Generate AI response
            ai_response_content = await self._generate_response(request.message, conversation.messages)
            
            # Create AI response message
            ai_message = ChatMessage(
                id=str(uuid.uuid4()),
                content=ai_response_content,
                is_user=False,
                timestamp=datetime.utcnow()
            )
            conversation.messages.append(ai_message)
            
            # Save conversation
            await self._save_conversation(conversation)
            
            return ChatResponse(
                message=ai_response_content,
                conversation_id=conversation.id,
                timestamp=ai_message.timestamp
            )
            
        except Exception as e:
            # Return error response
            return ChatResponse(
                message="I apologize, but I'm experiencing technical difficulties. Please try again later.",
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                timestamp=datetime.utcnow()
            )

    async def _get_or_create_conversation(self, conversation_id: Optional[str], user_id: Optional[str]) -> ChatConversation:
        """Get existing conversation or create new one"""
        if conversation_id:
            try:
                db = await self.get_db()
                conversation_data = await db.get_item('chat_sessions', {'session_id': conversation_id})
                if conversation_data:
                    return ChatConversation.from_dict(conversation_data)
            except Exception:
                pass
        
        # Create new conversation
        new_conversation = ChatConversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return new_conversation

    async def _save_conversation(self, conversation: ChatConversation):
        """Save conversation to database"""
        try:
            db = await self.get_db()
            conversation_data = {
                'session_id': conversation.id,
                'user_id': conversation.user_id,
                'messages': [msg.to_dict() for msg in conversation.messages],
                'created_at': conversation.created_at.isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            await db.insert_item('chat_sessions', conversation_data)
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def _generate_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate AI response based on message and context"""
        try:
            # Check for simple patterns first
            message_lower = message.lower().strip()
            
            # Greetings
            if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
                return self.greeting_responses[0]
            
            # Help requests
            if any(help_word in message_lower for help_word in ['help', 'what can you do', 'how can you help']):
                return self.help_responses[0]
            
            # Policy search
            if 'policy' in message_lower or 'policies' in message_lower:
                policies = await self._search_policies(message)
                if policies:
                    return self._format_policy_response(policies, message)
                else:
                    return "I couldn't find specific policies matching your query. Could you try rephrasing your question or being more specific about the country or policy area you're interested in?"
            
            # Default AI response using GROQ API
            if self.groq_api_key:
                return await self._get_ai_response(message, conversation_history)
            else:
                return "I'm here to help with AI policy information. You can ask me about policies by country, search for specific regulations, or get summaries of AI governance frameworks."
                
        except Exception as e:
            return "I apologize, but I'm having trouble processing your request right now. Please try asking about AI policies, regulations, or governance frameworks."

    async def _search_policies(self, query: str) -> List[Dict]:
        """Search for policies in database"""
        try:
            db = await self.get_db()
            policies = await db.scan_table('policies')
            
            # Simple keyword matching for now
            query_lower = query.lower()
            matching_policies = []
            
            for policy in policies:
                policy_text = f"{policy.get('title', '')} {policy.get('description', '')} {policy.get('country', '')}".lower()
                if any(word in policy_text for word in query_lower.split()):
                    matching_policies.append(policy)
            
            return matching_policies[:5]  # Return top 5 matches
            
        except Exception as e:
            print(f"Error searching policies: {e}")
            return []

    def _format_policy_response(self, policies: List[Dict], query: str) -> str:
        """Format policy search results into readable response"""
        if not policies:
            return "I couldn't find any policies matching your query."
        
        response = f"I found {len(policies)} relevant policies:\n\n"
        
        for i, policy in enumerate(policies, 1):
            title = policy.get('title', 'Untitled Policy')
            country = policy.get('country', 'Unknown')
            description = policy.get('description', 'No description available')
            
            response += f"{i}. **{title}** ({country})\n"
            response += f"   {description[:200]}...\n\n"
        
        response += "Would you like more details about any of these policies?"
        return response

    async def _get_ai_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Get AI response from GROQ API"""
        try:
            # Prepare conversation context
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI Policy Assistant. Help users understand global AI policies, regulations, and governance frameworks. Provide accurate, helpful information about AI policy topics."
                }
            ]
            
            # Add recent conversation history
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = "user" if msg.is_user else "assistant"
                messages.append({"role": role, "content": msg.content})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "mixtral-8x7b-32768",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(self.groq_api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return "I'm having trouble connecting to my knowledge base right now. Please try again in a moment."
                
        except Exception as e:
            return "I'm experiencing some technical difficulties. Please try rephrasing your question about AI policies."

    async def get_conversation_history(self, conversation_id: str) -> Optional[ChatConversation]:
        """Get conversation history by ID"""
        try:
            db = await self.get_db()
            conversation_data = await db.get_item('chat_sessions', {'session_id': conversation_id})
            if conversation_data:
                return ChatConversation.from_dict(conversation_data)
            return None
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return None

# Global instance
chatbot_service = ChatbotService()
