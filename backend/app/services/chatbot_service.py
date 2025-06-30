"""
Enhanced chatbot service with complete functionality from original chatbot.py
"""
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import re
import difflib
import uuid
from models.chat import ChatMessage, ChatRequest, ChatResponse, ChatConversation

class DatabasePolicyChatbot:
    def __init__(self, db):
        self.db = db
        self.conversations_collection = db.chat_conversations
        self.master_policies_collection = db.master_policies
        self.temp_submissions_collection = db.temp_submissions
        
        # Common greetings and help responses
        self.greeting_responses = [
            "hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"
        ]
        
        self.help_keywords = [
            "help", "what can you do", "commands", "how to use", "guide"
        ]
        
        # Non-database query patterns (to reject)
        self.non_database_patterns = [
            r'\btemperature\b', r'\bweather\b', r'\bclimate\b', r'\bhot\b', r'\bcold\b',
            r'\blocation\b', r'\blatitude\b', r'\blongitude\b', r'\baddress\b',
            r'\bpopulation\b', r'\beconomy\b', r'\bGDP\b', r'\bcurrency\b',
            r'\btime\b', r'\bdate\b', r'\btimezone\b', r'\btoday\b',
            r'\bsports\b', r'\bfootball\b', r'\bcricket\b', r'\bmovie\b',
            r'\bfood\b', r'\brecipe\b', r'\bcooking\b', r'\brestaurant\b',
            r'\bnews\b', r'\bcurrent events\b', r'\bbreaking\b',
            r'\bhistory\b(?!\s+of\s+AI|AI)', r'\bculture\b', r'\btradition\b',
            r'\btourism\b', r'\btravel\b', r'\bhotel\b', r'\bflight\b'
        ]

    def is_non_database_query(self, message: str) -> bool:
        """Check if the query is asking for non-database information"""
        message_lower = message.lower()
        
        # Check against non-database patterns
        for pattern in self.non_database_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        return False

    def find_closest_country_match(self, query: str, countries: List[str]) -> Optional[str]:
        """Find the closest matching country name using fuzzy matching"""
        query_lower = query.lower().strip()
        
        # First try exact match
        for country in countries:
            if country.lower() == query_lower:
                return country
        
        # Try partial match
        for country in countries:
            if query_lower in country.lower() or country.lower() in query_lower:
                return country
        
        # Try fuzzy matching for typos
        matches = difflib.get_close_matches(query_lower, [c.lower() for c in countries], n=1, cutoff=0.6)
        if matches:
            # Find the original country name
            for country in countries:
                if country.lower() == matches[0]:
                    return country
        
        return None

    async def search_policies_by_country(self, country_name: str) -> List[Dict]:
        """Search policies by country name - Enhanced with better matching"""
        try:
            # Create flexible regex pattern for country matching
            country_variations = [
                country_name,
                country_name.replace("United States", "USA"),
                country_name.replace("USA", "United States"),
                country_name.replace("United Kingdom", "UK"),
                country_name.replace("UK", "United Kingdom")
            ]
            
            policies = []
            
            # Try different country name variations
            for variant in country_variations:
                master_filter = {
                    "master_status": "active",
                    "country": {"$regex": f"^{re.escape(variant)}$", "$options": "i"}
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
            
            # Remove duplicates
            unique_policies = []
            seen = set()
            for policy in policies:
                key = (policy['name'], policy['country'])
                if key not in seen:
                    seen.add(key)
                    unique_policies.append(policy)
            
            return unique_policies
        except Exception as e:
            print(f"Error searching policies by country: {e}")
            return []

    async def get_countries_list(self) -> List[str]:
        """Get list of all countries with policies"""
        try:
            countries = set()
            
            async for policy in self.master_policies_collection.find(
                {"master_status": "active"}, 
                {"country": 1}
            ):
                if policy.get("country"):
                    countries.add(policy["country"])
            
            return sorted(list(countries))
        except Exception as e:
            print(f"Error getting countries list: {e}")
            return []

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

⚠️ **Important**: I only provide information from our AI policy database."""

    def get_greeting_response(self) -> str:
        """Generate greeting response"""
        return """👋 **Hello! Welcome to the AI Policy Database Assistant!**

I'm here to help you explore AI policies from around the world.

🔍 **What would you like to search for?**
• Type a **country name** to see all its AI policies
• Type **"help"** for detailed search options
• Type **"countries"** to see all available countries

What AI policies would you like to explore? 🚀"""

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
                for country in countries[:20]:  # Limit to first 20
                    response += f"• {country}\n"
                if len(countries) > 20:
                    response += f"... and {len(countries) - 20} more countries.\n"
                response += f"\n💡 Type any country name to see its AI policies!"
                return response
            else:
                return "Sorry, no countries found in our database."
        
        # Search for policies by country
        countries = await self.get_countries_list()
        matched_country = self.find_closest_country_match(message, countries)
        if matched_country:
            policies = await self.search_policies_by_country(matched_country)
            if policies:
                response = f"🔍 **Found {len(policies)} AI policies for {matched_country}:**\n\n"
                for policy in policies[:10]:  # Limit to 10 policies
                    response += f"  {policy['area_icon']} **{policy['name']}**\n"
                    response += f"     📋 Area: {policy['area']}\n"
                    response += f"     📅 Year: {policy['year']}\n"
                    response += f"     ✅ Status: {policy['status']}\n\n"
                return response
            else:
                return f"❌ No policies found for {matched_country}."
        
        # If nothing found, provide helpful response
        return f"""❌ **Sorry, I couldn't find any AI policies related to '{message}' in our database.**

🔍 **Try searching for:**
• **Country names**: United States, Germany, Japan, etc.
• Type **"countries"** to see all available countries
• Type **"help"** for more options

What AI policies would you like to explore? 🚀"""

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat function - database only responses"""
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or str(ObjectId())
            
            # Process query using database only
            response_text = await self.process_query(request.message)
            
            return ChatResponse(
                response=response_text,
                conversation_id=conversation_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# Global chatbot instance
chatbot_instance = None

def init_chatbot(db):
    """Initialize chatbot with database client"""
    global chatbot_instance
    chatbot_instance = DatabasePolicyChatbot(db)
    return chatbot_instance

def get_chatbot_service():
    """Dependency to get chatbot service"""
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    return chatbot_instance
