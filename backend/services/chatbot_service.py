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
        """Format policies into a readable response with Ithra-inspired colors"""
        if not policies:
            return f"""<div class="policy-response">
<div class="policy-header error">
    <span class="policy-icon">❌</span>
    <span class="policy-title">No Policies Found</span>
</div>
<div class="policy-content">
    <p>Sorry, I couldn't find any policies {query_type} '<strong>{query}</strong>' in our AI policy database.</p>
    
    <div class="search-suggestions">
        <h4>🔍 Try searching for:</h4>
        <ul>
            <li><strong>Country names:</strong> United States, Germany, Japan, etc.</li>
            <li><strong>Policy areas:</strong> AI Safety, Digital Education, Cybersafety, etc.</li>
            <li><strong>Specific policy names:</strong> AI Act, National AI Strategy, etc.</li>
        </ul>
        
        <div class="quick-commands">
            <h4>📊 Quick commands:</h4>
            <ul>
                <li>Type <strong>"countries"</strong> to see all available countries</li>
                <li>Type <strong>"areas"</strong> to see all policy areas</li>
                <li>Type <strong>"help"</strong> for more search options</li>
            </ul>
        </div>
    </div>
</div>
</div>"""

        # Group policies by country for better organization
        policies_by_country = {}
        for policy in policies:
            country = policy["country"]
            if country not in policies_by_country:
                policies_by_country[country] = []
            policies_by_country[country].append(policy)

        # Build the response with Ithra-inspired styling
        response = f"""<div class="policy-response">
<div class="policy-header success">
    <span class="policy-icon">🌍</span>
    <span class="policy-title">Found {len(policies)} AI Policies {query_type} "{query}"</span>
</div>
<div class="policy-content">"""

        for country, country_policies in policies_by_country.items():
            response += f"""
    <div class="country-section">
        <div class="country-header">
            <span class="country-flag">🏛️</span>
            <span class="country-name">{country}</span>
            <span class="policy-count">({len(country_policies)} policies)</span>
        </div>
        <div class="policies-grid">"""
            
            for policy in country_policies:
                response += f"""
            <div class="policy-card">
                <div class="policy-card-header">
                    <span class="policy-area-icon">{policy['area_icon']}</span>
                    <div class="policy-meta">
                        <span class="policy-year">{policy['year']}</span>
                        <span class="policy-status">{policy['status']}</span>
                    </div>
                </div>
                <h4 class="policy-name">{policy['name']}</h4>
                <div class="policy-area">{policy['area']}</div>
                <p class="policy-description">{policy['description'][:200]}{'...' if len(policy['description']) > 200 else ''}</p>
            </div>"""
            
            response += "</div></div>"

        response += """
    <div class="search-tips">
        <h4>💡 Search Tips:</h4>
        <ul>
            <li>Type any country name to see all its AI policies</li>
            <li>Search by policy area (e.g., "AI Safety", "Digital Education")</li>
            <li>Type "countries" to see all available countries</li>
            <li>Type "areas" to see all policy areas</li>
        </ul>
    </div>
</div>
</div>"""

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

    def get_greeting_response(self) -> str:
        """Generate greeting response with Ithra-inspired styling"""
        return """<div class="policy-response">
<div class="policy-header welcome">
    <span class="policy-icon">👋</span>
    <span class="policy-title">Welcome to the AI Policy Database Assistant!</span>
</div>
<div class="policy-content">
    <p>I'm here to help you explore AI policies from around the world. I have access to a comprehensive database of AI governance frameworks, regulations, and policy initiatives.</p>
    
    <div class="search-options">
        <h4>🔍 What would you like to search for?</h4>
        <ul>
            <li>Type a <strong>country name</strong> to see all its AI policies</li>
            <li>Type a <strong>policy name</strong> to find specific policies</li>
            <li>Type a <strong>policy area</strong> like "AI Safety" or "Digital Education"</li>
            <li>Type <strong>"help"</strong> for detailed search options</li>
            <li>Type <strong>"countries"</strong> to see all available countries</li>
        </ul>
    </div>
    
    <div class="example-searches">
        <h4>💡 Example searches:</h4>
        <div class="examples-grid">
            <div class="example-item">European Union</div>
            <div class="example-item">AI Safety policies</div>
            <div class="example-item">Digital Education</div>
            <div class="example-item">National AI Strategy</div>
        </div>
    </div>
    
    <div class="important-note">
        <p><strong>⚠️ Important:</strong> I only provide information from our AI policy database. I cannot help with weather, current events, or other non-policy topics.</p>
    </div>
    
    <p class="welcome-footer">What AI policies would you like to explore? 🚀</p>
</div>
</div>"""

    def get_non_database_response(self) -> str:
        """Response for non-database queries with Ithra-inspired styling"""
        return """<div class="policy-response">
<div class="policy-header error">
    <span class="policy-icon">❌</span>
    <span class="policy-title">Sorry, I can only help with AI policy information</span>
</div>
<div class="policy-content">
    <p>I'm specifically designed to assist with AI policy information from our database.</p>
    
    <div class="can-help">
        <h4>🏛️ I can help with:</h4>
        <ul>
            <li><strong>AI Policies by Country</strong> (e.g., "United States AI policies")</li>
            <li><strong>Policy Areas</strong> (e.g., "AI Safety", "Digital Education")</li>
            <li><strong>Specific Policies</strong> (e.g., "AI Act", "National AI Strategy")</li>
            <li><strong>Countries with AI Policies</strong> (type "countries")</li>
        </ul>
    </div>
    
    <div class="cannot-help">
        <h4>⚠️ I cannot help with:</h4>
        <ul>
            <li>Weather, temperature, or climate information</li>
            <li>Current news or events</li>
            <li>Location or geographic details</li>
            <li>Sports, entertainment, or general knowledge</li>
            <li>Any topics not related to AI policies</li>
        </ul>
    </div>
    
    <div class="try-instead">
        <h4>🔍 Try asking about AI policies instead:</h4>
        <ul>
            <li>"What AI policies does Bangladesh have?"</li>
            <li>"Show me AI Safety policies"</li>
            <li>"List all countries with AI policies"</li>
            <li>Type "help" for more options</li>
        </ul>
    </div>
    
    <p class="help-footer">What AI policies would you like to learn about? 🚀</p>
</div>
</div>"""

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
        
        # Handle list commands
        if message_lower in ["countries", "list countries", "show countries"]:
            countries = await self.get_countries_list()
            if countries:
                response = f"""<div class="policy-response">
<div class="policy-header info">
    <span class="policy-icon">🌍</span>
    <span class="policy-title">Countries with AI policies in our database ({len(countries)} total)</span>
</div>
<div class="policy-content">
    <div class="countries-grid">"""
                
                # Group countries by first letter
                countries_by_letter = {}
                for country in countries:
                    first_letter = country[0].upper()
                    if first_letter not in countries_by_letter:
                        countries_by_letter[first_letter] = []
                    countries_by_letter[first_letter].append(country)
                
                for letter in sorted(countries_by_letter.keys()):
                    response += f"""
        <div class="country-group">
            <h4 class="letter-header">{letter}</h4>
            <div class="country-list">"""
                    for country in countries_by_letter[letter]:
                        response += f'<span class="country-item">{country}</span>'
                    response += "</div></div>"
                
                response += """
    </div>
    <p class="search-tip">💡 Type any country name to see its AI policies!</p>
</div>
</div>"""
                return response
            else:
                return "Sorry, no countries found in our database."
        
        if message_lower in ["areas", "policy areas", "list areas", "show areas"]:
            areas = await self.get_policy_areas_list()
            if areas:
                response = f"""<div class="policy-response">
<div class="policy-header info">
    <span class="policy-icon">📋</span>
    <span class="policy-title">Policy areas in our database ({len(areas)} total)</span>
</div>
<div class="policy-content">
    <div class="areas-grid">"""
                
                for i, area in enumerate(areas, 1):
                    response += f'<div class="area-item"><span class="area-number">{i}</span><span class="area-name">{area}</span></div>'
                
                response += """
    </div>
    <p class="search-tip">💡 Type any policy area to see related policies!</p>
</div>
</div>"""
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
        return f"""<div class="policy-response">
<div class="policy-header error">
    <span class="policy-icon">❌</span>
    <span class="policy-title">No AI policies found for "{message}"</span>
</div>
<div class="policy-content">
    <div class="search-suggestions">
        <h4>🔍 Try searching for:</h4>
        <ul>
            <li><strong>Country names:</strong> United States, Germany, Japan, etc.</li>
            <li><strong>Policy areas:</strong> AI Safety, Digital Education, Cybersafety, etc.</li>
            <li><strong>Specific policy names:</strong> AI Act, National AI Strategy, etc.</li>
        </ul>
    </div>
    
    <div class="quick-commands">
        <h4>📊 Quick commands:</h4>
        <ul>
            <li>Type <strong>"countries"</strong> to see all available countries</li>
            <li>Type <strong>"areas"</strong> to see all policy areas</li>
            <li>Type <strong>"help"</strong> for more search options</li>
        </ul>
    </div>
    
    <div class="example-searches">
        <h4>💡 Example searches that work:</h4>
        <ul>
            <li>"United States" (even if you type "United staes" - I'll fix typos!)</li>
            <li>"AI Safety"</li>
            <li>"Digital Education policies"</li>
            <li>"European Union"</li>
        </ul>
    </div>
    
    <div class="important-note">
        <p><strong>⚠️ Remember:</strong> I only provide information from our AI policy database. I cannot help with weather, current events, or other non-policy topics.</p>
    </div>
    
    <p class="help-footer">What AI policies would you like to explore? 🚀</p>
</div>
</div>"""

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


# Create singleton instance
chatbot_service = ChatbotService()

# Initialize function (if needed by main.py)
def init_chatbot(database_client):
    """Initialize chatbot with database client"""
    pass  # We're using the global database instance