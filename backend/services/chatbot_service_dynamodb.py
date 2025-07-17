"""
DynamoDB Chatbot service for AI policy database queries.
Hybrid approach: Uses GROQ AI for intelligent responses while restricting to policy data only.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
import requests
from dotenv import load_dotenv

from models.chat import ChatMessage, ChatRequest, ChatResponse, ChatConversation
from config.dynamodb import get_dynamodb
from utils.helpers import convert_objectid

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)


class ChatbotService:
    def __init__(self):
        self._db = None
        
        # GROQ AI configuration
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_api_url = os.getenv('GROQ_API_URL', "https://api.groq.com/openai/v1/chat/completions")
        
        # Policy data cache
        self.policy_cache = None
        self.last_cache_update = None
        
        # Fallback responses if AI fails
        self.greeting_responses = [
            "Hello! I'm your AI Policy Assistant. I can help you explore the AI policies we have in our database. What would you like to know?",
            "Hi there! I specialize in AI policy information from our curated database. What specific policies or countries are you interested in?",
            "Welcome! I'm here to help you understand AI policies from around the world. What can I help you find today?",
        ]
        
        self.help_responses = [
            "I can help you with information from our AI policy database:\n• Find policies by country (we have data from India, Bangladesh, Germany, and more)\n• Search policy descriptions and details\n• Explain policy areas like AI Safety, CyberSafety\n• Provide information about policy implementation, evaluation, and participation\n\nWhat specific information are you looking for?",
        ]
        
        # Response templates for no data found
        self.no_data_responses = [
            "I don't have information about that in our current policy database. I can only help with AI policies we have stored. Would you like to know what countries or policy areas I do have information about?",
            "That's not something I can find in our AI policy database. I'm specialized in the policies we've collected and verified. Can I help you with information about AI Safety, CyberSafety, or policies from India, Bangladesh, or Germany instead?",
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
                role="user",
                content=request.message,
                timestamp=datetime.utcnow()
            )
            conversation.messages.append(user_message)
            
            # Generate AI response
            response_text = await self._generate_response(request.message, conversation.messages)
            
            # Add AI response to conversation
            ai_message = ChatMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow()
            )
            conversation.messages.append(ai_message)
            
            # Save updated conversation
            await self._save_conversation(conversation)
            
            return ChatResponse(
                response=response_text,
                conversation_id=conversation.conversation_id,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            print(f"Chat error: {e}")
            return ChatResponse(
                response="I'm experiencing some technical difficulties. Please try again.",
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat()
            )

    async def _get_or_create_conversation(self, conversation_id: Optional[str], user_id: Optional[str]) -> ChatConversation:
        """Get existing conversation or create new one"""
        try:
            if conversation_id:
                db = await self.get_db()
                conversation_data = await db.get_item('chat_sessions', {'session_id': conversation_id})
                if conversation_data:
                    # Convert data to proper format for Pydantic model
                    conversation_data['conversation_id'] = conversation_data.get('session_id', conversation_id)
                    conversation_data['messages'] = [
                        ChatMessage(**msg) if isinstance(msg, dict) else msg 
                        for msg in conversation_data.get('messages', [])
                    ]
                    # Parse datetime strings back to datetime objects
                    if 'created_at' in conversation_data and isinstance(conversation_data['created_at'], str):
                        try:
                            conversation_data['created_at'] = datetime.fromisoformat(conversation_data['created_at'].replace('Z', '+00:00'))
                        except:
                            conversation_data['created_at'] = datetime.utcnow()
                    if 'updated_at' in conversation_data and isinstance(conversation_data['updated_at'], str):
                        try:
                            conversation_data['updated_at'] = datetime.fromisoformat(conversation_data['updated_at'].replace('Z', '+00:00'))
                        except:
                            conversation_data['updated_at'] = datetime.utcnow()
                    
                    # Remove non-model fields
                    conversation_data = {k: v for k, v in conversation_data.items() 
                                       if k in ['conversation_id', 'messages', 'created_at', 'updated_at']}
                    return ChatConversation(**conversation_data)
            
            # Create new conversation
            new_conversation = ChatConversation(
                conversation_id=str(uuid.uuid4()),
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            return new_conversation
            
        except Exception as e:
            print(f"Error getting/creating conversation: {e}")
            return ChatConversation(
                conversation_id=str(uuid.uuid4()),
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

    async def _save_conversation(self, conversation: ChatConversation):
        """Save conversation to database"""
        try:
            db = await self.get_db()
            conversation.updated_at = datetime.utcnow()
            
            # Properly serialize messages with datetime objects
            serialized_messages = []
            for msg in conversation.messages:
                msg_dict = msg.dict()
                # Convert timestamp to ISO string if it exists
                if 'timestamp' in msg_dict and msg_dict['timestamp']:
                    if hasattr(msg_dict['timestamp'], 'isoformat'):
                        msg_dict['timestamp'] = msg_dict['timestamp'].isoformat()
                    else:
                        msg_dict['timestamp'] = str(msg_dict['timestamp'])
                serialized_messages.append(msg_dict)
            
            conversation_data = {
                'session_id': conversation.conversation_id,
                'messages': serialized_messages,
                'created_at': conversation.created_at.isoformat() if hasattr(conversation.created_at, 'isoformat') else str(conversation.created_at),
                'updated_at': conversation.updated_at.isoformat() if hasattr(conversation.updated_at, 'isoformat') else str(conversation.updated_at)
            }
            
            await db.insert_item('chat_sessions', conversation_data)
            
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def _generate_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate intelligent response using GROQ AI with policy data context"""
        message_lower = message.lower().strip()
        
        # Simple greetings - use direct response
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']) and len(message.split()) <= 2:
            return self.greeting_responses[0]
        
        # Get policy data from cache or database
        await self._update_policy_cache()
        
        # Dynamic country detection based on actual database content
        mentioned_country = None
        mentioned_area = None
        
        if self.policy_cache:
            # Get all countries from the database
            countries_in_db = set()
            policy_areas_in_db = set()
            
            for policy in self.policy_cache['map_policies']:
                country = policy.get('country', '').lower()
                area = policy.get('policy_area', '').lower()
                if country:
                    countries_in_db.add(country)
                if area:
                    policy_areas_in_db.add(area)
            
            # Check for country-specific queries
            for country in countries_in_db:
                if country in message_lower:
                    mentioned_country = country
                    break
            
            # Check for policy area queries
            for area in policy_areas_in_db:
                if area in message_lower:
                    mentioned_area = area
                    break
            
            # Also check for common country variations
            if 'united states' in message_lower or 'usa' in message_lower or 'us' in message_lower:
                for country in countries_in_db:
                    if 'united states' in country:
                        mentioned_country = country
                        break
            
            if 'uk' in message_lower or 'united kingdom' in message_lower or 'britain' in message_lower:
                for country in countries_in_db:
                    if 'united kingdom' in country or 'uk' in country:
                        mentioned_country = country
                        break
        
        # Search for relevant policies
        relevant_policies = await self._find_relevant_policies(message_lower, mentioned_country, mentioned_area)
        
        # Check if asking about available data
        if any(word in message_lower for word in ['what countries', 'which countries', 'what policies', 'what data', 'countries', 'areas']):
            return await self._get_available_data_summary()
        
        # Use GROQ AI to generate intelligent response
        if self.groq_api_key and (relevant_policies or mentioned_country or mentioned_area):
            try:
                ai_response = await self._get_groq_response(message, relevant_policies, conversation_history)
                if ai_response and "I don't have" not in ai_response and "I can't" not in ai_response:
                    return ai_response
            except Exception as e:
                print(f"GROQ API error: {e}")
        
        # Fallback to structured response if AI fails or no relevant data
        if relevant_policies:
            return self._format_policy_response(relevant_policies, message_lower, mentioned_country, mentioned_area)
        
        # No relevant data found
        import random
        return random.choice(self.no_data_responses)

    async def _update_policy_cache(self):
        """Update local cache of policy data"""
        try:
            if self.policy_cache is None or (self.last_cache_update and 
                (datetime.utcnow() - self.last_cache_update).seconds > 300):  # 5 minute cache
                
                db = await self.get_db()
                map_policies = await db.scan_table('map_policies')
                main_policies = await db.scan_table('policies')
                
                self.policy_cache = {
                    'map_policies': [p for p in map_policies if p.get('status') == 'approved'],
                    'main_policies': [p for p in main_policies if p.get('status') == 'approved']
                }
                self.last_cache_update = datetime.utcnow()
                
        except Exception as e:
            print(f"Error updating policy cache: {e}")
            if self.policy_cache is None:
                self.policy_cache = {'map_policies': [], 'main_policies': []}

    async def _find_relevant_policies(self, query: str, country: str = None, area: str = None) -> List[Dict]:
        """Find policies relevant to the query"""
        relevant = []
        
        if not self.policy_cache:
            return relevant
        
        # Define policy-related keywords - if none are found, return empty
        policy_keywords = [
            'policy', 'policies', 'regulation', 'regulations', 'governance', 'framework', 'law', 'laws',
            'ai', 'artificial intelligence', 'cyber', 'cybersafety', 'safety', 'security', 'government',
            'implementation', 'deployment', 'strategy', 'initiative', 'guidelines', 'standards'
        ]
        
        # Check if query contains any policy-related keywords
        has_policy_keywords = any(keyword in query for keyword in policy_keywords)
        
        # If we have a specific country or area mentioned, we should search regardless of policy keywords
        # This fixes the issue where "United States" alone wouldn't return results
        if not has_policy_keywords and not country and not area:
            return relevant
        
        # Search map policies
        for policy in self.policy_cache['map_policies']:
            relevance_score = 0
            
            # Country matching - this is the most important for country queries
            if country:
                policy_country = policy.get('country', '').lower()
                if country == 'uk' or country == 'united kingdom':
                    if any(uk_term in policy_country for uk_term in ['uk', 'united kingdom', 'britain', 'england']):
                        relevance_score += 10
                elif country in policy_country:
                    relevance_score += 10
            
            # Policy area matching
            policy_area = policy.get('policy_area', '').lower()
            if area:
                if 'ai safety' in area and 'ai safety' in policy_area:
                    relevance_score += 8
                elif 'cyber' in area and 'cyber' in policy_area:
                    relevance_score += 8
            
            # Content matching - search for any term in the query
            policy_name = policy.get('policy_name', '').lower()
            policy_desc = policy.get('policy_description', '').lower()
            policy_country_text = policy.get('country', '').lower()
            
            # Check for keyword matches in all fields
            keywords = query.split()
            for keyword in keywords:
                if len(keyword) > 2:  # Skip very short words
                    if keyword in policy_name:
                        relevance_score += 3
                    if keyword in policy_desc:
                        relevance_score += 2
                    if keyword in policy_area:
                        relevance_score += 2
                    if keyword in policy_country_text:
                        relevance_score += 5  # Higher weight for country matches
            
            # Only include if we have a meaningful relevance score
            if relevance_score > 0:
                policy['relevance_score'] = relevance_score
                relevant.append(policy)
        
        # Sort by relevance and return top 3
        relevant.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return relevant[:3]

    async def _get_available_data_summary(self) -> str:
        """Get summary of available policy data"""
        await self._update_policy_cache()
        
        if not self.policy_cache:
            return "I'm having trouble accessing our policy database right now. Please try again in a moment."
        
        # Count by country
        country_counts = {}
        area_counts = {}
        
        for policy in self.policy_cache['map_policies']:
            country = policy.get('country', 'Unknown')
            area = policy.get('policy_area', 'Unknown')
            
            country_counts[country] = country_counts.get(country, 0) + 1
            area_counts[area] = area_counts.get(area, 0) + 1
        
        total_policies = len(self.policy_cache['map_policies'])
        
        response = f"I have information about {total_policies} AI policies in our database:\n\n"
        
        if country_counts:
            response += "**Countries covered:**\n"
            for country, count in sorted(country_counts.items()):
                response += f"• {country}: {count} {'policy' if count == 1 else 'policies'}\n"
        
        if area_counts:
            response += "\n**Policy areas:**\n"
            for area, count in sorted(area_counts.items()):
                response += f"• {area}: {count} {'policy' if count == 1 else 'policies'}\n"
        
        response += "\nFeel free to ask me about any of these countries or policy areas!"
        return response

    async def _get_groq_response(self, message: str, relevant_policies: List[Dict], conversation_history: List[ChatMessage]) -> str:
        """Get intelligent response from GROQ AI with policy context"""
        try:
            if not self.groq_api_key:
                return None
            
            # Prepare policy context for AI
            policy_context = ""
            if relevant_policies:
                policy_context = "\n\nRELEVANT POLICY DATA:\n"
                for i, policy in enumerate(relevant_policies[:3], 1):
                    policy_context += f"{i}. {policy.get('policy_name', 'N/A')}\n"
                    policy_context += f"   Country: {policy.get('country', 'N/A')}\n"
                    policy_context += f"   Area: {policy.get('policy_area', 'N/A')}\n"
                    policy_context += f"   Description: {policy.get('policy_description', 'N/A')[:200]}...\n"
                    
                    # Add implementation details
                    implementation = policy.get('implementation', {})
                    if implementation:
                        deployment_year = implementation.get('deploymentYear')
                        if deployment_year and deployment_year != 'N/A':
                            policy_context += f"   Deployment Year: {deployment_year}\n"
                    
                    # Add target groups
                    target_groups = policy.get('target_groups', [])
                    if target_groups:
                        policy_context += f"   Target Groups: {', '.join(target_groups)}\n"
                    
                    policy_context += "\n"
            
            # Prepare conversation context
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an AI Policy Assistant specialized in providing information about AI policies from a curated database. 

IMPORTANT RESTRICTIONS:
- Only answer questions related to AI policies, governance, regulations, and related topics
- Base your responses ONLY on the policy data provided in the context
- If no relevant policy data is provided, politely redirect to asking about available policy topics
- Do not make up or hallucinate policy information
- Be conversational and helpful, but stay focused on the policy database
- If asked about non-policy topics (weather, sports, etc.), politely decline and redirect to policy topics

AVAILABLE COUNTRIES: India, Bangladesh, Germany
AVAILABLE POLICY AREAS: AI Safety, CyberSafety
TOTAL POLICIES: 6 policies in the database

{policy_context}

Respond in a helpful, conversational manner while staying strictly within the bounds of the provided policy data."""
                }
            ]
            
            # Add recent conversation history
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append({"role": msg.role, "content": msg.content})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama3-8b-8192",  # Current supported model
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(self.groq_api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                return ai_response
            else:
                print(f"GROQ API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"GROQ API exception: {e}")
            return None
        """Search for policies in the database"""
        try:
            db = await self.get_db()
            
            # Get all policies from database
            policies = await db.scan_table('map_policies')
            
            # Simple text matching
            matching_policies = []
            query_lower = query.lower()
            
            for policy in policies:
                # Search in various fields using the correct field names for map_policies
                searchable_text = f"{policy.get('country', '')} {policy.get('policy_name', '')} {policy.get('policyName', '')} {policy.get('policy_description', '')} {policy.get('policyDescription', '')}"
                if query_lower in searchable_text.lower():
                    matching_policies.append(policy)
            
            return matching_policies[:5]  # Limit to 5 results
            
        except Exception as e:
            print(f"Policy search error: {e}")
            return []

    def _format_policy_response(self, policies: List[Dict], query: str, country: str = None, area: str = None) -> str:
        """Format policy information into a human-like response"""
        if not policies:
            return "I don't have any policies matching your query in our database."
        
        response = ""
        
        # Add context based on what was asked
        if country and area:
            response += f"Here's what I found about {area} policies in {country.title()}:\n\n"
        elif country:
            response += f"Here are the AI policies I have for {country.title()}:\n\n"
        elif area:
            response += f"Here are the {area} policies in our database:\n\n"
        else:
            response += "Here are the relevant policies I found:\n\n"
        
        for i, policy in enumerate(policies[:3], 1):  # Limit to top 3
            policy_name = policy.get('policy_name', 'Unnamed Policy')
            country_name = policy.get('country', 'Unknown')
            policy_area = policy.get('policy_area', 'Unknown')
            description = policy.get('policy_description', 'No description available')
            
            # Truncate description if too long
            if len(description) > 200:
                description = description[:200] + "..."
            
            response += f"**{i}. {policy_name}**\n"
            response += f"📍 Country: {country_name}\n"
            response += f"🏷️ Area: {policy_area}\n"
            response += f"📋 Description: {description}\n"
            
            # Add implementation details if available
            implementation = policy.get('implementation', {})
            if implementation and isinstance(implementation, dict):
                deployment_year = implementation.get('deploymentYear')
                if deployment_year and deployment_year != 'N/A':
                    response += f"📅 Deployment Year: {deployment_year}\n"
            
            # Add target groups if available
            target_groups = policy.get('target_groups', [])
            if target_groups and isinstance(target_groups, list):
                response += f"🎯 Target Groups: {', '.join(target_groups)}\n"
            
            response += "\n"
        
        # Add helpful suggestions
        if len(policies) == 1:
            response += "Would you like to know more about this policy's implementation details, evaluation metrics, or target groups?"
        elif len(policies) > 1:
            response += "Would you like more details about any of these policies, or information about other countries or policy areas?"
        
        return response.strip()

    async def get_conversation_history(self, conversation_id: str) -> List[ChatMessage]:
        """Get conversation history by ID"""
        try:
            db = await self.get_db()
            conversation_data = await db.get_item('chat_sessions', {'session_id': conversation_id})
            if conversation_data:
                messages = conversation_data.get('messages', [])
                return [ChatMessage(**msg) if isinstance(msg, dict) else msg for msg in messages]
            return []
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def get_user_conversations(self, limit: int = 20, user_id: Optional[str] = None) -> List[Dict]:
        """Get list of conversations for a user or all conversations"""
        try:
            db = await self.get_db()
            
            # Get all chat sessions and limit them
            sessions = await db.scan_table('chat_sessions')
            
            # Filter by user_id if provided
            if user_id:
                sessions = [s for s in sessions if s.get('user_id') == user_id]
            
            # Sort by created_at descending and limit
            sorted_sessions = sorted(sessions, 
                                   key=lambda x: x.get('created_at', ''), 
                                   reverse=True)[:limit]
            
            # Convert to simple format for frontend
            conversations = []
            for session in sorted_sessions:
                conversations.append({
                    'conversation_id': session.get('session_id'),
                    'title': session.get('title', 'New Conversation'),
                    'created_at': session.get('created_at'),
                    'updated_at': session.get('updated_at'),
                    'message_count': len(session.get('messages', []))
                })
            
            return conversations
        except Exception as e:
            print(f"Error getting user conversations: {e}")
            return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            db = await self.get_db()
            success = await db.delete_item('chat_sessions', {'session_id': conversation_id})
            return success
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    async def search_policies(self, query: str) -> List[Dict]:
        """Search for policies based on query - enhanced for sidebar search"""
        await self._update_policy_cache()
        
        # Use the same logic as the main chat to detect countries and areas
        message_lower = query.lower()
        mentioned_country = None
        mentioned_area = None
        
        if self.policy_cache:
            # Get all countries from the database
            countries_in_db = set()
            policy_areas_in_db = set()
            
            for policy in self.policy_cache['map_policies']:
                country = policy.get('country', '').lower()
                area = policy.get('policy_area', '').lower()
                if country:
                    countries_in_db.add(country)
                if area:
                    policy_areas_in_db.add(area)
            
            # Check for country-specific queries
            for country in countries_in_db:
                if country in message_lower:
                    mentioned_country = country
                    break
            
            # Check for policy area queries
            for area in policy_areas_in_db:
                if area in message_lower:
                    mentioned_area = area
                    break
            
            # Also check for common country variations
            if 'united states' in message_lower or 'usa' in message_lower or 'us' in message_lower:
                for country in countries_in_db:
                    if 'united states' in country:
                        mentioned_country = country
                        break
            
            if 'uk' in message_lower or 'united kingdom' in message_lower or 'britain' in message_lower:
                for country in countries_in_db:
                    if 'united kingdom' in country or 'uk' in country:
                        mentioned_country = country
                        break
        
        return await self._find_relevant_policies(message_lower, mentioned_country, mentioned_area)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            db = await self.get_db()
            await db.delete_item('chat_sessions', {'session_id': conversation_id})
            return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False


# Global instance
chatbot_service = ChatbotService()
