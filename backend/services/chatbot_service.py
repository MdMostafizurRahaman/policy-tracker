"""
Chatbot service for AI policy database queries.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import difflib
import json
import os
import requests
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
        
        # AI API configuration
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        
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
        query_lower = query.lower()
        
        # First try exact matches
        for country in countries:
            if query_lower == country.lower():
                return country
        
        # Then try partial matches
        for country in countries:
            if query_lower in country.lower() or country.lower() in query_lower:
                return country
        
        # Finally try fuzzy matching
        matches = difflib.get_close_matches(query, countries, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def find_closest_area_match(self, query: str, areas: List[str]) -> Optional[str]:
        """Find the closest matching area name using fuzzy matching"""
        query_lower = query.lower()
        
        # First try exact matches
        for area in areas:
            if query_lower == area.lower():
                return area
        
        # Then try partial matches
        for area in areas:
            if query_lower in area.lower() or area.lower() in query_lower:
                return area
        
        # Finally try fuzzy matching
        matches = difflib.get_close_matches(query, areas, n=1, cutoff=0.6)
        return matches[0] if matches else None

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
        """Format policies into a readable response without HTML styling"""
        if not policies:
            return f"""No Policies Found

Sorry, I couldn't find any policies {query_type} '{query}' in our AI policy database.

Try searching for:
• Country names: United States, Germany, Japan, etc.
• Policy areas: AI Safety, Digital Education, Cybersafety, etc.
• Specific policy names: AI Act, National AI Strategy, etc.

Quick commands:
• Type "countries" to see all available countries
• Type "areas" to see all policy areas
• Type "help" for more search options"""

        # Group policies by country for better organization
        policies_by_country = {}
        for policy in policies:
            country = policy["country"]
            if country not in policies_by_country:
                policies_by_country[country] = []
            policies_by_country[country].append(policy)

        # Build the response as plain text
        response = f"Found {len(policies)} AI Policies {query_type} \"{query}\"\n\n"

        for country, country_policies in policies_by_country.items():
            response += f"🏛️ {country} ({len(country_policies)} policies)\n"
            response += "=" * (len(country) + 20) + "\n\n"
            
            for policy in country_policies:
                response += f"📄 {policy['name']}\n"
                response += f"   Area: {policy['area']}\n"
                response += f"   Year: {policy['year']}\n"
                response += f"   Status: {policy['status']}\n"
                description = policy['description'][:200] + "..." if len(policy['description']) > 200 else policy['description']
                response += f"   Description: {description}\n\n"

        response += "💡 Search Tips:\n"
        response += "• Type any country name to see all its AI policies\n"
        response += "• Search by policy area (e.g., \"AI Safety\", \"Digital Education\")\n"
        response += "• Type \"countries\" to see all available countries\n"
        response += "• Type \"areas\" to see all policy areas"

        return response

    def get_help_response(self) -> str:
        """Generate help response with Ithra-inspired styling"""
        return """<div class="policy-response">
<div class="policy-header info">
    <span class="policy-icon">🤖</span>
    <span class="policy-title">AI Policy Database Assistant Help</span>
</div>
<div class="policy-content">
    <p>I can help you find AI policies from our database! Here's what I can do:</p>
    
    <div class="help-section">
        <h4>🔍 Search Commands:</h4>
        <ul>
            <li><strong>Country Search:</strong> Type any country name (e.g., "United States", "Germany", "Japan")</li>
            <li><strong>Policy Name Search:</strong> Type part of a policy name (e.g., "AI Act", "Strategy")</li>
            <li><strong>Policy Area Search:</strong> Type policy areas (e.g., "AI Safety", "Digital Education")</li>
        </ul>
    </div>
    
    <div class="help-section">
        <h4>📊 List Commands:</h4>
        <ul>
            <li><strong>"countries"</strong> - See all countries with policies in our database</li>
            <li><strong>"areas"</strong> - See all policy areas available</li>
            <li><strong>"help"</strong> - Show this help message</li>
        </ul>
    </div>
    
    <div class="help-section">
        <h4>💡 Example Searches:</h4>
        <ul>
            <li>"United States" → Find all US AI policies</li>
            <li>"AI Safety" → Find all AI safety policies</li>
            <li>"GDPR" → Find GDPR-related policies</li>
            <li>"Digital Education" → Find digital education policies</li>
        </ul>
    </div>
    
    <div class="important-note">
        <h4>⚠️ Important Limitations:</h4>
        <ul>
            <li>I ONLY provide information from our AI policy database</li>
            <li>I cannot answer questions about weather, temperature, current events, news, or other non-policy topics</li>
            <li>If information isn't in our AI policy database, I'll let you know</li>
            <li>All policy information is sourced from official government submissions</li>
        </ul>
    </div>
    
    <p class="help-footer">Just type your search term and I'll find relevant AI policies for you! 🚀</p>
</div>
</div>"""

    def get_simple_greeting_response(self) -> str:
        """Generate simple greeting response without HTML"""
        return """Welcome to the AI Policy Database Assistant!

I'm here to help you explore AI policies from around the world. I have access to a comprehensive database of AI governance frameworks, regulations, and policy initiatives.

What would you like to search for?
• Type a country name to see all its AI policies
• Type a policy name to find specific policies  
• Type a policy area like "AI Safety" or "Digital Education"
• Type "help" for detailed search options
• Type "countries" to see all available countries

Example searches:
• European Union
• AI Safety policies
• Digital Education
• National AI Strategy

Important: I only provide information from our AI policy database. I cannot help with weather, current events, or other non-policy topics.

What AI policies would you like to explore?"""

    def get_simple_help_response(self) -> str:
        """Generate simple help response without HTML"""
        return """AI Policy Database Assistant Help

I can help you find AI policies from our database! Here's what I can do:

Search Commands:
• Country Search: Type any country name (e.g., "United States", "Germany", "Japan")
• Policy Name Search: Type part of a policy name (e.g., "AI Act", "Strategy")
• Policy Area Search: Type policy areas (e.g., "AI Safety", "Digital Education")

List Commands:
• "countries" - See all countries with policies in our database
• "areas" - See all policy areas available
• "help" - Show this help message

Example Searches:
• "United States" → Find all US AI policies
• "AI Safety" → Find all AI safety policies
• "GDPR" → Find GDPR-related policies
• "Digital Education" → Find digital education policies

Important Limitations:
• I ONLY provide information from our AI policy database
• I cannot answer questions about weather, temperature, current events, news, or other non-policy topics
• If information isn't in our AI policy database, I'll let you know
• All policy information is sourced from official government submissions

Just type your search term and I'll find relevant AI policies for you!"""

    def get_help_response(self) -> str:
        """Generate help response with Ithra-inspired styling"""
        return """<div class="policy-response">
<div class="policy-header info">
    <span class="policy-icon">🤖</span>
    <span class="policy-title">AI Policy Database Assistant Help</span>
</div>
<div class="policy-content">
    <p>I can help you find AI policies from our database! Here's what I can do:</p>
    
    <div class="help-section">
        <h4>🔍 Search Commands:</h4>
        <ul>
            <li><strong>Country Search:</strong> Type any country name (e.g., "United States", "Germany", "Japan")</li>
            <li><strong>Policy Name Search:</strong> Type part of a policy name (e.g., "AI Act", "Strategy")</li>
            <li><strong>Policy Area Search:</strong> Type policy areas (e.g., "AI Safety", "Digital Education")</li>
        </ul>
    </div>
    
    <div class="help-section">
        <h4>📊 List Commands:</h4>
        <ul>
            <li><strong>"countries"</strong> - See all countries with policies in our database</li>
            <li><strong>"areas"</strong> - See all policy areas available</li>
            <li><strong>"help"</strong> - Show this help message</li>
        </ul>
    </div>
    
    <div class="help-section">
        <h4>💡 Example Searches:</h4>
        <ul>
            <li>"United States" → Find all US AI policies</li>
            <li>"AI Safety" → Find all AI safety policies</li>
            <li>"GDPR" → Find GDPR-related policies</li>
            <li>"Digital Education" → Find digital education policies</li>
        </ul>
    </div>
    
    <div class="important-note">
        <h4>⚠️ Important Limitations:</h4>
        <ul>
            <li>I ONLY provide information from our AI policy database</li>
            <li>I cannot answer questions about weather, temperature, current events, news, or other non-policy topics</li>
            <li>If information isn't in our AI policy database, I'll let you know</li>
            <li>All policy information is sourced from official government submissions</li>
        </ul>
    </div>
    
    <p class="help-footer">Just type your search term and I'll find relevant AI policies for you! 🚀</p>
</div>
</div>"""

    def get_simple_non_database_response(self) -> str:
        """Simple response for non-database queries without HTML"""
        return """Sorry, I can only help with AI policy information.

I'm specifically designed to assist with AI policy information from our database.

I can help with:
• AI Policies by Country (e.g., "United States AI policies")
• Policy Areas (e.g., "AI Safety", "Digital Education")
• Specific Policies (e.g., "AI Act", "National AI Strategy")
• Countries with AI Policies (type "countries")

I cannot help with:
• Weather, temperature, or climate information
• Current news or events
• Location or geographic details
• Sports, entertainment, or general knowledge
• Any topics not related to AI policies

Try asking about AI policies instead:
• "What AI policies does Bangladesh have?"
• "Show me AI Safety policies"
• "List all countries with AI policies"
• Type "help" for more options

What AI policies would you like to learn about?"""

    async def process_query(self, message: str) -> str:
        """Process user query and return database-based response with AI analysis"""
        message_lower = message.lower().strip()
        
        # Check if this is a non-database query first
        if self.is_non_database_query(message):
            return self.get_simple_non_database_response()
        
        # Handle greetings
        if any(greeting in message_lower for greeting in self.greeting_responses):
            return self.get_simple_greeting_response()
        
        # Handle help requests
        if any(help_word in message_lower for help_word in self.help_keywords):
            return self.get_simple_help_response()
        
        # Handle list commands
        if message_lower in ["countries", "list countries", "show countries"]:
            countries = await self.get_countries_list()
            if countries:
                response = f"Countries with AI policies in our database ({len(countries)} total):\n\n"
                
                # Group countries by first letter
                countries_by_letter = {}
                for country in countries:
                    first_letter = country[0].upper()
                    if first_letter not in countries_by_letter:
                        countries_by_letter[first_letter] = []
                    countries_by_letter[first_letter].append(country)
                
                for letter in sorted(countries_by_letter.keys()):
                    response += f"{letter}:\n"
                    for country in countries_by_letter[letter]:
                        response += f"- {country}\n"
                    response += "\n"
                
                response += "Type any country name to see its AI policies!"
                return response
            else:
                return "Sorry, no countries found in our database."
        
        if message_lower in ["areas", "policy areas", "list areas", "show areas"]:
            areas = await self.get_policy_areas_list()
            if areas:
                response = f"Policy areas in our database ({len(areas)} total):\n\n"
                
                for i, area in enumerate(areas, 1):
                    response += f"{i}. {area}\n"
                
                response += "\nType any policy area to see related policies!"
                return response
            else:
                return "Sorry, no policy areas found in our database."
        
        # Search for policies with improved matching
        countries = await self.get_countries_list()
        areas = await self.get_policy_areas_list()
        
        policies_found = []
        search_type = ""
        search_term = ""
        
        # Enhanced country search with fuzzy matching
        matched_country = self.find_closest_country_match(message, countries)
        if matched_country:
            policies_found = await self.search_policies_by_country(matched_country)
            search_type = "for country"
            search_term = matched_country
        
        # Enhanced area search with fuzzy matching (if no country match)
        if not policies_found:
            matched_area = self.find_closest_area_match(message, areas)
            if matched_area:
                policies_found = await self.search_policies_by_area(matched_area)
                search_type = "in area"
                search_term = matched_area
        
        # Try policy name search (if no area match)
        if not policies_found:
            policies_found = await self.search_policies_by_name(message)
            search_type = "matching"
            search_term = message
        
        # If we found specific policies, return structured database response only
        if policies_found:
            return await self.format_policies_response(policies_found, search_type, search_term)
        
        # For queries with no specific matches, try AI analysis with general context
        if self.groq_api_key:
            try:
                # Get general policy context
                all_policies = []
                async for policy in self.master_policies_collection.find({"master_status": "active"}).limit(30):
                    all_policies.append({
                        "policyName": policy.get("policyName", ""),
                        "country": policy.get("country", ""),
                        "policyArea": policy.get("policyArea", ""),
                        "policyDescription": policy.get("policyDescription", "")[:200] + "..." if len(policy.get("policyDescription", "")) > 200 else policy.get("policyDescription", "")
                    })
                
                if all_policies:
                    ai_response = await self.get_simple_ai_response(message, all_policies)
                    if ai_response:
                        return ai_response
            except Exception as e:
                print(f"Error in AI analysis: {e}")
        
        # If nothing found, provide helpful response
        return f"""I couldn't find any AI policies matching "{message}" in our database.

You can try searching for country names like United States, Germany, or Japan to see their AI policies. You can also search by policy areas such as AI Safety, Digital Education, or Cybersafety, or look for specific policy names like AI Act or National AI Strategy.

If you want to browse what's available, you can type "countries" to see all countries with policies in our database, or "areas" to see all policy areas. You can also type "help" for more detailed search options.

Some example searches that work well include "United States" (I can handle typos too!), "AI Safety", "Digital Education policies", or "European Union".

Keep in mind that I only provide information from our AI policy database and can't help with weather, current events, or other non-policy topics.

What AI policies would you like to explore?"""

    async def get_conversation(self, conversation_id: str) -> Optional[ChatConversation]:
        """Retrieve a conversation from the database"""
        try:
            doc = await self.conversations_collection.find_one({"conversation_id": conversation_id})
            if doc:
                return ChatConversation(**convert_objectid(doc))
            return None
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return None

    async def save_conversation(self, conversation: ChatConversation):
        """Save or update a conversation in the database"""
        try:
            await self.conversations_collection.replace_one(
                {"conversation_id": conversation.conversation_id},
                conversation.dict(),
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

    def is_ai_enabled(self) -> bool:
        """Check if AI analysis is enabled"""
        return bool(self.groq_api_key)
    
    async def get_ai_enhanced_response(self, query: str, context_data: List[Dict] = None) -> Optional[str]:
        """Get AI-enhanced response for complex queries"""
        if not self.is_ai_enabled():
            return None
            
        try:
            if context_data is None:
                # Get general policy context
                context_data = []
                async for policy in self.master_policies_collection.find({"master_status": "active"}).limit(20):
                    context_data.append({
                        "policyName": policy.get("policyName", ""),
                        "country": policy.get("country", ""),
                        "policyArea": policy.get("policyArea", ""),
                        "policyDescription": policy.get("policyDescription", "")[:150] + "..." if len(policy.get("policyDescription", "")) > 150 else policy.get("policyDescription", "")
                    })
            
            return await self.analyze_query_with_ai(query, context_data)
        except Exception as e:
            print(f"Error getting AI enhanced response: {e}")
            return None

    async def analyze_query_with_ai(self, user_query: str, policies_data: List[Dict]) -> str:
        """Analyze user query using AI with structured prompt format"""
        try:
            # Create structured prompt similar to digital wellbeing format
            prompt = self.create_structured_prompt(user_query, policies_data)
            
            # Call AI API
            ai_response = await self._call_groq_api(prompt)
            
            # Parse AI response
            parsed_response = self._parse_ai_response(ai_response)
            
            # Format the response for the UI
            return self._format_ai_response(parsed_response)
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            # Fallback to existing logic
            return None

    def create_structured_prompt(self, user_query: str, data_context) -> str:
        """Create structured prompt similar to digital wellbeing format"""
        
        # Handle both list and dict formats
        if isinstance(data_context, list):
            context_json = json.dumps(data_context, indent=2) if data_context else "No specific policies found, but provide guidance on available data in our AI policy database."
            context_note = ""
        else:
            context_json = json.dumps(data_context, indent=2) if data_context else "No specific policies found, but provide guidance on available data in our AI policy database."
            context_note = "Note: This is a sample of policies from a larger dataset. Mention the total number found if relevant to the query."
        
        return f"""
You are an AI policy database analyst. Answer the user's question about AI policies using the provided dataset in a natural, conversational way like ChatGPT or Claude.

User Query: "{user_query}"

Available Policy Data Context:
{context_json}

{context_note}

Guidelines:
1. Answer in a natural, conversational tone like a knowledgeable assistant
2. Provide specific policy names, countries, policy areas, and comparisons when relevant
3. If the question cannot be answered with the available data, explain what data would be needed
4. Be conversational and friendly while being precise with policy information
5. Include relevant insights about AI governance and policy trends naturally in the conversation
6. Focus only on AI policy-related information from our database
7. Write like you're having a conversation with a colleague, not like a formal report
8. Use natural language flow, not bullet points or structured lists in the main answer
9. If showing a sample of policies from a larger set, mention the total number naturally in your response

Respond in JSON format:
{{
    "answer": "natural conversational response as if you're ChatGPT or Claude explaining the policies (plain text, no HTML, no bullet points in main answer - write naturally)",
    "relevant_policies": {{"key policies and data points that support the answer"}},
    "additional_insights": ["insight1 about AI policy trends", "insight2 about governance patterns"],
    "suggestions": ["suggestion for further policy exploration", "related policy areas to explore"]
}}
"""

    async def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API for AI analysis"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama3-70b-8192",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            }
            
            response = requests.post(
                self.groq_api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"Error calling Groq API: {str(e)}")
            raise

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response JSON"""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            
            # Find JSON content between curly braces
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No valid JSON found in AI response")
            
            json_content = response[start_idx:end_idx]
            parsed_data = json.loads(json_content)
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from AI response: {str(e)}")
            raise ValueError(f"Invalid JSON in AI response: {str(e)}")

    def _format_ai_response(self, ai_data: Dict[str, Any]) -> str:
        """Format AI response into plain text"""
        try:
            answer = ai_data.get("answer", "")
            relevant_policies = ai_data.get("relevant_policies", {})
            insights = ai_data.get("additional_insights", [])
            suggestions = ai_data.get("suggestions", [])
            
            # Build formatted response as plain text
            response = answer
            
            if relevant_policies:
                response += "\n\nRelevant Policy Data:\n"
                for key, value in relevant_policies.items():
                    response += f"• {key}: {value}\n"
            
            if insights:
                response += "\nAdditional Insights:\n"
                for insight in insights:
                    response += f"• {insight}\n"
            
            if suggestions:
                response += "\nExplore Further:\n"
                for suggestion in suggestions:
                    response += f"• {suggestion}\n"
            
            return response.strip()
            
        except Exception as e:
            print(f"Error formatting AI response: {e}")
            return ai_data.get("answer", "Error formatting response")

    async def get_simple_ai_response(self, user_query: str, policies_data) -> Optional[str]:
        """Get simple AI response without extra formatting"""
        try:
            # Handle both old format (list) and new format (summary object)
            if isinstance(policies_data, dict) and "policies" in policies_data:
                # New format with summary info
                actual_policies = policies_data["policies"]
                total_count = policies_data.get("total_policies_found", len(actual_policies))
                search_info = f" (showing {len(actual_policies)} of {total_count} total policies found)"
            else:
                # Old format (direct list)
                actual_policies = policies_data if isinstance(policies_data, list) else []
                search_info = ""
            
            # Create structured prompt
            prompt = self.create_structured_prompt(user_query + search_info, actual_policies)
            
            # Call AI API
            ai_response = await self._call_groq_api(prompt)
            
            # Parse AI response
            parsed_response = self._parse_ai_response(ai_response)
            
            # Return just the answer without extra formatting
            answer = parsed_response.get("answer", "I couldn't generate a proper response.")
            return answer
            
        except Exception as e:
            print(f"Error in simple AI response: {e}")
            return None

# Create singleton instance
chatbot_service = ChatbotService()

# Initialize function (if needed by main.py)
def init_chatbot(database_client):
    """Initialize chatbot with database client"""
    pass  # We're using the global database instance