"""
Chatbot service for AI policy database queries.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import difflib
from bson import ObjectId

from models.chat import ChatMessage, ChatRequest, ChatResponse, ChatConversation
from config.database import database
from utils.helpers import convert_objectid


class ChatbotService:
    def __init__(self):
        self._db = None
        self._conversations_collection = None
        self._master_policies_collection = None
        self._temp_submissions_collection = None
        
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

    @property
    def db(self):
        if self._db is None:
            self._db = database.db
        return self._db

    @property
    def conversations_collection(self):
        if self._conversations_collection is None:
            self._conversations_collection = self.db.chat_conversations
        return self._conversations_collection

    @property
    def master_policies_collection(self):
        if self._master_policies_collection is None:
            self._master_policies_collection = self.db.master_policies
        return self._master_policies_collection

    @property
    def temp_submissions_collection(self):
        if self._temp_submissions_collection is None:
            self._temp_submissions_collection = self.db.temp_submissions
        return self._temp_submissions_collection

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

    def find_closest_area_match(self, query: str, areas: List[str]) -> Optional[str]:
        """Find the closest matching area name using fuzzy matching"""
        query_lower = query.lower().strip()
        
        # First try exact match
        for area in areas:
            if area.lower() == query_lower:
                return area
        
        # Try partial match
        for area in areas:
            if query_lower in area.lower() or area.lower() in query_lower:
                return area
        
        # Try fuzzy matching
        matches = difflib.get_close_matches(query_lower, [a.lower() for a in areas], n=1, cutoff=0.6)
        if matches:
            for area in areas:
                if area.lower() == matches[0]:
                    return area
        
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
                
                # Also search in temp submissions
                temp_submissions = self.temp_submissions_collection.find({
                    "country": {"$regex": f"^{re.escape(variant)}$", "$options": "i"}
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

    async def search_policies_by_name(self, policy_name: str) -> List[Dict]:
        """Search policies by policy name with fuzzy matching"""
        try:
            policies = []
            
            # Use flexible regex for policy name matching
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
        """Search policies by policy area with fuzzy matching"""
        try:
            policies = []
            
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
        """Get list of all countries with policies"""
        try:
            countries = set()
            
            async for policy in self.master_policies_collection.find(
                {"master_status": "active"}, 
                {"country": 1}
            ):
                if policy.get("country"):
                    countries.add(policy["country"])
            
            async for submission in self.temp_submissions_collection.find({}, {"country": 1}):
                if submission.get("country"):
                    countries.add(submission["country"])
            
            return sorted(list(countries))
        except Exception as e:
            print(f"Error getting countries list: {e}")
            return []

    async def get_policy_areas_list(self) -> List[str]:
        """Get list of all policy areas"""
        try:
            areas = set()
            
            async for policy in self.master_policies_collection.find(
                {"master_status": "active"}, 
                {"area_name": 1, "policyArea": 1}
            ):
                if policy.get("area_name"):
                    areas.add(policy["area_name"])
                elif policy.get("policyArea"):
                    areas.add(policy["policyArea"])
            
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
            return f"""❌ **Sorry, I couldn't find any policies {query_type} '{query}' in our AI policy database.**

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

⚠️ **Important**: I only provide information from our AI policy database. I cannot answer questions about weather, temperature, current events, or other topics not related to AI policies."""
        
        response = f"🔍 **Found {len(policies)} AI policies {query_type} '{query}':**\n\n"
        
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

**⚠️ Important Limitations:**
• I ONLY provide information from our AI policy database
• I cannot answer questions about weather, temperature, current events, news, or other non-policy topics
• If information isn't in our AI policy database, I'll let you know
• All policy information is sourced from official government submissions

Just type your search term and I'll find relevant AI policies for you! 🚀"""

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

⚠️ **Important**: I only provide information from our AI policy database. I cannot help with weather, current events, or other non-policy topics.

What AI policies would you like to explore? 🚀"""

    def get_non_database_response(self) -> str:
        """Response for non-database queries"""
        return """❌ **Sorry, I can only help with AI policy information from our database.**

I'm specifically designed to assist with:
• 🏛️ **AI Policies by Country** (e.g., "United States AI policies")
• 📋 **Policy Areas** (e.g., "AI Safety", "Digital Education")
• 📝 **Specific Policies** (e.g., "AI Act", "National AI Strategy")
• 🌍 **Countries with AI Policies** (type "countries")

⚠️ **I cannot help with:**
• Weather, temperature, or climate information
• Current news or events
• Location or geographic details
• Sports, entertainment, or general knowledge
• Any topics not related to AI policies

🔍 **Try asking about AI policies instead:**
• "What AI policies does Bangladesh have?"
• "Show me AI Safety policies"
• "List all countries with AI policies"
• Type "help" for more options

What AI policies would you like to learn about? 🚀"""

    async def process_query(self, message: str) -> str:
        """Process user query and return database-based response"""
        message_lower = message.lower().strip()
        
        # Check if this is a non-database query first
        if self.is_non_database_query(message):
            return self.get_non_database_response()
        
        # Handle greetings
        if any(greeting in message_lower for greeting in self.greeting_responses):
            return self.get_greeting_response()
        
        # Handle help requests
        if any(help_word in message_lower for help_word in self.help_keywords):
            return self.get_help_response()
        
        # Handle "show me all policies" or similar broad queries
        broad_queries = [
            "show me all policies", "all policies", "show all policies",
            "all ai policies", "show me all ai policies", "list all policies",
            "all countries policies", "show me all countries", "policies from all countries"
        ]
        
        if any(broad_query in message_lower for broad_query in broad_queries):
            # Get a sample of policies from multiple countries
            countries = await self.get_countries_list()
            all_policies = []
            
            # Get policies from first few countries to avoid overwhelming response
            for country in countries[:5]:  # Limit to first 5 countries
                country_policies = await self.search_policies_by_country(country)
                all_policies.extend(country_policies[:3])  # Max 3 policies per country
            
            if all_policies:
                response = f"🌍 **Sample of AI policies from our database (showing {len(all_policies)} from {min(5, len(countries))} countries):**\n\n"
                
                # Group by country
                policies_by_country = {}
                for policy in all_policies:
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
                    response += "\n"
                
                response += f"💡 **For complete coverage:**\n"
                response += f"• Type **'countries'** to see all {len(countries)} countries with policies\n"
                response += f"• Type any specific country name to see all its policies\n"
                response += f"• Type **'areas'** to see all policy areas available\n"
                
                return response
            else:
                return "❌ No policies found in our database."
        
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
        
        # Search for policies with improved matching
        countries = await self.get_countries_list()
        areas = await self.get_policy_areas_list()
        
        # Enhanced country search with fuzzy matching
        matched_country = self.find_closest_country_match(message, countries)
        if matched_country:
            policies = await self.search_policies_by_country(matched_country)
            return await self.format_policies_response(policies, "for country", matched_country)
        
        # Enhanced area search with fuzzy matching
        matched_area = self.find_closest_area_match(message, areas)
        if matched_area:
            policies = await self.search_policies_by_area(matched_area)
            return await self.format_policies_response(policies, "in area", matched_area)
        
        # Try policy name search
        policies = await self.search_policies_by_name(message)
        if policies:
            return await self.format_policies_response(policies, "matching", message)
        
        # If nothing found, provide helpful response
        return f"""❌ **Sorry, I couldn't find any AI policies related to '{message}' in our database.**

🔍 **Try searching for:**
• **Country names**: United States, Germany, Japan, etc.
• **Policy areas**: AI Safety, Digital Education, Cybersafety, etc.
• **Specific policy names**: AI Act, National AI Strategy, etc.

📊 **Quick commands:**
• Type **"countries"** to see all available countries
• Type **"areas"** to see all policy areas  
• Type **"help"** for more search options

💡 **Example searches that work:**
• "United States" (even if you type "United staes" - I'll fix typos!)
• "AI Safety"
• "Digital Education policies"
• "European Union"

⚠️ **Remember**: I only provide information from our AI policy database. I cannot help with weather, current events, or other non-policy topics.

What AI policies would you like to explore? 🚀"""

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
            raise Exception(f"Chat error: {str(e)}")

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

    async def search_policies(self, query: str) -> List[Dict]:
        """Enhanced policy search for the sidebar"""
        try:
            # Search across all policy fields
            policies = []
            
            # Search by country
            countries = await self.get_countries_list()
            matched_country = self.find_closest_country_match(query, countries)
            if matched_country:
                country_policies = await self.search_policies_by_country(matched_country)
                policies.extend(country_policies)
            
            # Search by policy name
            name_policies = await self.search_policies_by_name(query)
            policies.extend(name_policies)
            
            # Search by area
            areas = await self.get_policy_areas_list()
            matched_area = self.find_closest_area_match(query, areas)
            if matched_area:
                area_policies = await self.search_policies_by_area(matched_area)
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
            
            return unique_policies[:10]  # Limit to 10 results
            
        except Exception as e:
            print(f"Error in policy search: {e}")
            return []


# Create singleton instance
chatbot_service = ChatbotService()
