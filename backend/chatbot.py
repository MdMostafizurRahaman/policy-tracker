from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import asyncio
import motor.motor_asyncio
from bson import ObjectId
import re

# Load environment variables
load_dotenv()

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

class DatabasePolicyChatbot:
    def __init__(self, db_client):
        self.db = db_client.ai_policy_database
        self.conversations_collection = self.db.chat_conversations
        self.master_policies_collection = self.db.master_policies
        self.temp_submissions_collection = self.db.temp_submissions
        
        # Common greetings and help responses
        self.greeting_responses = [
            "hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"
        ]
        
        self.help_keywords = [
            "help", "what can you do", "commands", "how to use", "guide"
        ]

    async def search_policies_by_country(self, country_name: str) -> List[Dict]:
        """Search policies by country name - FIXED: Remove visibility filter"""
        try:
            # FIXED: Only use master_status filter, no visibility filter
            master_filter = {
                "master_status": "active",
                "country": {"$regex": f"^{re.escape(country_name)}$", "$options": "i"}
            }
            
            policies = []
            async for policy in self.master_policies_collection.find(master_filter):
                policies.append({
                    "name": policy.get("policyName", "Unnamed Policy"),
                    "country": policy.get("country", ""),
                    "area": policy.get("area_name", policy.get("policyArea", "")),
                    "description": policy.get("policyDescription", "No description available"),
                    "year": policy.get("implementation", {}).get("deploymentYear", "TBD"),
                    "status": policy.get("status", "Active"),
                    "area_icon": policy.get("area_icon", "📄"),
                    "source": "master"
                })
            
            # Also search in temp submissions for approved policies
            temp_submissions = self.temp_submissions_collection.find({
                "country": {"$regex": f"^{re.escape(country_name)}$", "$options": "i"}
            })
            
            async for submission in temp_submissions:
                if "policyAreas" in submission:
                    policy_areas = submission["policyAreas"]
                    if isinstance(policy_areas, list):
                        for area in policy_areas:
                            for policy in area.get("policies", []):
                                if policy.get("status") == "approved":
                                    policies.append({
                                        "name": policy.get("policyName", "Unnamed Policy"),
                                        "country": submission.get("country", ""),
                                        "area": area.get("area_name", area.get("area_id", "")),
                                        "description": policy.get("policyDescription", "No description available"),
                                        "year": policy.get("implementation", {}).get("deploymentYear", "TBD"),
                                        "status": "Approved",
                                        "area_icon": "📄",
                                        "source": "temp"
                                    })
            
            return policies
        except Exception as e:
            print(f"Error searching policies by country: {e}")
            return []

    async def search_policies_by_name(self, policy_name: str) -> List[Dict]:
        """Search policies by policy name - FIXED: Remove visibility filter"""
        try:
            policies = []
            
            # Search in master policies - FIXED: Remove visibility filter
            master_filter = {
                "master_status": "active",
                "policyName": {"$regex": re.escape(policy_name), "$options": "i"}
            }
            
            async for policy in self.master_policies_collection.find(master_filter):
                policies.append({
                    "name": policy.get("policyName", "Unnamed Policy"),
                    "country": policy.get("country", ""),
                    "area": policy.get("area_name", policy.get("policyArea", "")),
                    "description": policy.get("policyDescription", "No description available"),
                    "year": policy.get("implementation", {}).get("deploymentYear", "TBD"),
                    "status": policy.get("status", "Active"),
                    "area_icon": policy.get("area_icon", "📄"),
                    "source": "master"
                })
            
            # Also search in temp submissions
            async for submission in self.temp_submissions_collection.find({}):
                if "policyAreas" in submission:
                    policy_areas = submission["policyAreas"]
                    if isinstance(policy_areas, list):
                        for area in policy_areas:
                            for policy in area.get("policies", []):
                                if (policy.get("status") == "approved" and 
                                    policy_name.lower() in policy.get("policyName", "").lower()):
                                    policies.append({
                                        "name": policy.get("policyName", "Unnamed Policy"),
                                        "country": submission.get("country", ""),
                                        "area": area.get("area_name", area.get("area_id", "")),
                                        "description": policy.get("policyDescription", "No description available"),
                                        "year": policy.get("implementation", {}).get("deploymentYear", "TBD"),
                                        "status": "Approved",
                                        "area_icon": "📄",
                                        "source": "temp"
                                    })
            
            return policies
        except Exception as e:
            print(f"Error searching policies by name: {e}")
            return []

    async def search_policies_by_area(self, area_name: str) -> List[Dict]:
        """Search policies by policy area - FIXED: Remove visibility filter"""
        try:
            policies = []
            
            # Search in master policies - FIXED: Remove visibility filter
            master_filter = {
                "master_status": "active",
                "$or": [
                    {"policyArea": {"$regex": re.escape(area_name), "$options": "i"}},
                    {"area_name": {"$regex": re.escape(area_name), "$options": "i"}}
                ]
            }
            
            async for policy in self.master_policies_collection.find(master_filter):
                policies.append({
                    "name": policy.get("policyName", "Unnamed Policy"),
                    "country": policy.get("country", ""),
                    "area": policy.get("area_name", policy.get("policyArea", "")),
                    "description": policy.get("policyDescription", "No description available"),
                    "year": policy.get("implementation", {}).get("deploymentYear", "TBD"),
                    "status": policy.get("status", "Active"),
                    "area_icon": policy.get("area_icon", "📄"),
                    "source": "master"
                })
            
            # Also search in temp submissions
            async for submission in self.temp_submissions_collection.find({}):
                if "policyAreas" in submission:
                    policy_areas = submission["policyAreas"]
                    if isinstance(policy_areas, list):
                        for area in policy_areas:
                            if (area_name.lower() in area.get("area_name", "").lower() or 
                                area_name.lower() in area.get("area_id", "").lower()):
                                for policy in area.get("policies", []):
                                    if policy.get("status") == "approved":
                                        policies.append({
                                            "name": policy.get("policyName", "Unnamed Policy"),
                                            "country": submission.get("country", ""),
                                            "area": area.get("area_name", area.get("area_id", "")),
                                            "description": policy.get("policyDescription", "No description available"),
                                            "year": policy.get("implementation", {}).get("deploymentYear", "TBD"),
                                            "status": "Approved",
                                            "area_icon": "📄",
                                            "source": "temp"
                                        })
            
            return policies
        except Exception as e:
            print(f"Error searching policies by area: {e}")
            return []

    async def get_countries_list(self) -> List[str]:
        """Get list of all countries with policies - FIXED: Remove visibility filter"""
        try:
            countries = set()
            
            # Get from master policies - FIXED: Remove visibility filter
            async for policy in self.master_policies_collection.find(
                {"master_status": "active"}, 
                {"country": 1}
            ):
                if policy.get("country"):
                    countries.add(policy["country"])
            
            # Get from temp submissions
            async for submission in self.temp_submissions_collection.find({}, {"country": 1}):
                if submission.get("country"):
                    countries.add(submission["country"])
            
            return sorted(list(countries))
        except Exception as e:
            print(f"Error getting countries list: {e}")
            return []

    async def get_policy_areas_list(self) -> List[str]:
        """Get list of all policy areas - FIXED: Remove visibility filter"""
        try:
            areas = set()
            
            # Get from master policies - FIXED: Remove visibility filter
            async for policy in self.master_policies_collection.find(
                {"master_status": "active"}, 
                {"area_name": 1, "policyArea": 1}
            ):
                if policy.get("area_name"):
                    areas.add(policy["area_name"])
                elif policy.get("policyArea"):
                    areas.add(policy["policyArea"])
            
            # Get from temp submissions
            async for submission in self.temp_submissions_collection.find({}, {"policyAreas": 1}):
                if "policyAreas" in submission:
                    policy_areas = submission["policyAreas"]
                    if isinstance(policy_areas, list):
                        for area in policy_areas:
                            if area.get("area_name"):
                                areas.add(area["area_name"])
            
            return sorted(list(areas))
        except Exception as e:
            print(f"Error getting policy areas list: {e}")
            return []

    async def format_policies_response(self, policies: List[Dict], query_type: str, query: str) -> str:
        """Format policies into a readable response"""
        if not policies:
            return f"""❌ **Sorry, I couldn't find any policies {query_type} '{query}' in our database.**

🔍 **Try searching for:**
• **Country names**: United States, Germany, Japan, etc.
• **Policy areas**: AI Safety, Digital Education, Cybersafety, etc.
• **Specific policy names**: AI Act, National AI Strategy, etc.

📊 **Quick commands:**
• Type **"countries"** to see all available countries
• Type **"areas"** to see all policy areas  
• Type **"help"** for more search options

💡 **Example searches that work:**
• "United States"
• "AI Safety"
• "Digital Education policies"
• "European Union"

Our database only contains verified AI policies from official sources."""
        
        response = f"🔍 **Found {len(policies)} policies {query_type} '{query}':**\n\n"
        
        # Group by country for better organization
        policies_by_country = {}
        for policy in policies:
            country = policy["country"]
            if country not in policies_by_country:
                policies_by_country[country] = []
            policies_by_country[country].append(policy)
        
        for country, country_policies in policies_by_country.items():
            response += f"🌍 **{country}** ({len(country_policies)} policies):\n"
            
            for policy in country_policies:
                response += f"  {policy['area_icon']} **{policy['name']}**\n"
                response += f"     📋 Area: {policy['area']}\n"
                response += f"     📅 Year: {policy['year']}\n"
                response += f"     ✅ Status: {policy['status']}\n"
                if policy['description'] and len(policy['description']) > 10:
                    desc = policy['description'][:150] + "..." if len(policy['description']) > 150 else policy['description']
                    response += f"     📝 Description: {desc}\n"
                response += "\n"
            response += "\n"
        
        # Add helpful suggestions
        response += "💡 **Need more information?** Try searching for:\n"
        response += "• Specific country names (e.g., 'United States', 'Germany')\n"
        response += "• Policy areas (e.g., 'AI Safety', 'Digital Education')\n"
        response += "• Specific policy names\n"
        response += "• Type 'countries' to see all available countries\n"
        response += "• Type 'areas' to see all policy areas"
        
        return response

    def get_help_response(self) -> str:
        """Generate help response"""
        return """🤖 **AI Policy Database Assistant Help**

I can help you find AI policies from our database! Here's what I can do:

**🔍 Search Commands:**
• **Country Search**: Type any country name (e.g., "United States", "Germany", "Japan")
• **Policy Name Search**: Type part of a policy name (e.g., "AI Act", "Strategy")
• **Policy Area Search**: Type policy areas (e.g., "AI Safety", "Digital Education")

**📊 List Commands:**
• **"countries"** - See all countries with policies in our database
• **"areas"** - See all policy areas available
• **"help"** - Show this help message

**💡 Example Searches:**
• "United States" → Find all US AI policies
• "AI Safety" → Find all AI safety policies
• "GDPR" → Find GDPR-related policies
• "Digital Education" → Find digital education policies

**ℹ️ Important Notes:**
• I only show information from our verified policy database
• If a policy isn't in our database, I'll let you know
• All policy information is sourced from official submissions

Just type your search term and I'll find relevant policies for you! 🚀"""

    def get_greeting_response(self) -> str:
        """Generate greeting response"""
        return """👋 **Hello! Welcome to the AI Policy Database Assistant!**

I'm here to help you explore AI policies from around the world. I have access to a comprehensive database of AI governance frameworks, regulations, and policy initiatives.

🔍 **What would you like to search for?**
• Type a **country name** to see all its AI policies
• Type a **policy name** to find specific policies  
• Type a **policy area** like "AI Safety" or "Digital Education"
• Type **"help"** for detailed search options
• Type **"countries"** to see all available countries

**Example searches:**
• "European Union" 
• "AI Safety policies"
• "Digital Education"
• "National AI Strategy"

What would you like to explore? 🚀"""

    async def process_query(self, message: str) -> str:
        """Process user query and return database-based response"""
        message_lower = message.lower().strip()
        
        # Handle greetings
        if any(greeting in message_lower for greeting in self.greeting_responses):
            return self.get_greeting_response()
        
        # Handle help requests
        if any(help_word in message_lower for help_word in self.help_keywords):
            return self.get_help_response()
        
        # Handle list commands
        if message_lower in ["countries", "list countries", "show countries"]:
            countries = await self.get_countries_list()
            if countries:
                response = f"🌍 **Countries with AI policies in our database ({len(countries)} total):**\n\n"
                # Group countries by first letter for better organization
                countries_by_letter = {}
                for country in countries:
                    first_letter = country[0].upper()
                    if first_letter not in countries_by_letter:
                        countries_by_letter[first_letter] = []
                    countries_by_letter[first_letter].append(country)
                
                for letter in sorted(countries_by_letter.keys()):
                    response += f"**{letter}:** {', '.join(countries_by_letter[letter])}\n"
                
                response += f"\n💡 Type any country name to see its AI policies!"
                return response
            else:
                return "Sorry, no countries found in our database."
        
        if message_lower in ["areas", "policy areas", "list areas", "show areas"]:
            areas = await self.get_policy_areas_list()
            if areas:
                response = f"📋 **Policy areas in our database ({len(areas)} total):**\n\n"
                for i, area in enumerate(areas, 1):
                    response += f"{i}. {area}\n"
                response += f"\n💡 Type any policy area to see related policies!"
                return response
            else:
                return "Sorry, no policy areas found in our database."
        
        # Search for policies
        # First try country search
        countries = await self.get_countries_list()
        for country in countries:
            if country.lower() in message_lower or message_lower in country.lower():
                policies = await self.search_policies_by_country(country)
                return await self.format_policies_response(policies, "for country", country)
        
        # Try policy area search
        areas = await self.get_policy_areas_list()
        for area in areas:
            if area.lower() in message_lower or message_lower in area.lower():
                policies = await self.search_policies_by_area(area)
                return await self.format_policies_response(policies, "in area", area)
        
        # Try policy name search
        policies = await self.search_policies_by_name(message)
        if policies:
            return await self.format_policies_response(policies, "matching", message)
        
        # If nothing found, provide helpful response
        return f"""❌ **Sorry, I couldn't find any policies related to '{message}' in our database.**

🔍 **Try searching for:**
• **Country names**: United States, Germany, Japan, etc.
• **Policy areas**: AI Safety, Digital Education, Cybersafety, etc.
• **Specific policy names**: AI Act, National AI Strategy, etc.

📊 **Quick commands:**
• Type **"countries"** to see all available countries
• Type **"areas"** to see all policy areas  
• Type **"help"** for more search options

💡 **Example searches that work:**
• "European Union"
• "AI Safety"
• "Digital Education policies"
• "United States AI"

Our database only contains verified AI policies from official sources. If you don't see a policy, it might not be in our database yet."""

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

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat function - database only responses"""
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
            
            # Process query using database only
            response_text = await self.process_query(request.message)
            
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

# Helper function to convert ObjectId to string for JSON serialization
def convert_objectid_chat(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_chat(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_chat(item) for item in obj]
    return obj

# Initialize chatbot instance
chatbot_instance = None

def init_chatbot(db_client):
    """Initialize chatbot with database client"""
    global chatbot_instance
    chatbot_instance = DatabasePolicyChatbot(db_client)
    return chatbot_instance

# FastAPI route functions
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

async def policy_search_endpoint(q: str):
    """Enhanced policy search endpoint for the sidebar"""
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    try:
        # Search across all policy fields
        policies = []
        
        # Search by country
        countries = await chatbot_instance.get_countries_list()
        for country in countries:
            if q.lower() in country.lower():
                country_policies = await chatbot_instance.search_policies_by_country(country)
                policies.extend(country_policies)
        
        # Search by policy name
        name_policies = await chatbot_instance.search_policies_by_name(q)
        policies.extend(name_policies)
        
        # Search by area
        area_policies = await chatbot_instance.search_policies_by_area(q)
        policies.extend(area_policies)
        
        # Remove duplicates based on name and country
        unique_policies = []
        seen = set()
        for policy in policies:
            key = (policy['name'], policy['country'])
            if key not in seen:
                seen.add(key)
                unique_policies.append({
                    "id": f"{policy['country']}_{policy['name']}".replace(" ", "_"),
                    "name": policy['name'],
                    "country": policy['country'],
                    "area": policy['area'],
                    "description": policy['description'],
                    "year": policy['year'],
                    "area_icon": policy['area_icon']
                })
        
        return {"policies": unique_policies[:10]}  # Limit to 10 results
        
    except Exception as e:
        print(f"Error in policy search: {e}")
        return {"policies": []}