"""
Enhanced Chatbot Service with GPT API for human-like responses
Covers 10 policy domains: AI Safety, CyberSafety, Digital Education, Digital Inclusion, 
Digital Leisure, (Dis)Information, Digital Work, Mental Health, Physical Health, and Social Media/Gaming Regulation
Only responds with database information, redirects non-policy queries to registration
"""
import os
import json
import httpx
import asyncio
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from models.chat import ChatMessage, ChatRequest, ChatResponse, ChatConversation
from config.dynamodb import get_dynamodb
from utils.helpers import convert_objectid

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)


class EnhancedChatbotService:
    def __init__(self):
        self._db = None
        
        # GPT API configuration (using OpenAI) - Primary and only AI model
        self.openai_api_key = os.getenv('OPENAI_API_KEY')  # Your GPT API key
        self.openai_api_url = "https://api.openai.com/v1/chat/completions"
        
        # GROQ configuration - COMMENTED OUT (Using ChatGPT only)
        # self.groq_api_key = os.getenv('GROQ_API_KEY')
        # self.groq_api_url = os.getenv('GROQ_API_URL', "https://api.groq.com/openai/v1/chat/completions")
        
        # Policy data cache for faster responses
        self.policy_cache = None
        self.countries_cache = None
        self.areas_cache = None
        self.last_cache_update = None
        self.cache_duration = 3600  # 1 hour
        
        # Greeting responses
        self.greeting_keywords = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy', 'hola', 'thanks', 'thank you', 'thank', 'appreciate', 'goodbye', 'bye', 'see you', 'farewell', 'have a nice day', 'take care']
        
        # Simple acknowledgment keywords (conversational responses)
        self.acknowledgment_keywords = ['ok', 'okay', 'alright', 'sure', 'right', 'got it', 'understood', 'i see', 'makes sense', 'cool', 'fine', 'no problem', 'no worries', 'all good', 'nice', 'great', 'awesome', 'perfect', 'excellent', 'wonderful']
        
        # Apologetic/polite phrases that should get gentle responses
        self.apologetic_keywords = ['sorry', 'apologize', 'my bad', 'oops', 'excuse me']
        
        # Help keywords
        self.help_keywords = ['help', 'what can you do', 'assist', 'guide', 'support', 'how to use']
        
        # Country comparison keywords
        self.comparison_keywords = ['compare', 'difference', 'vs', 'versus', 'between', 'different', 'contrast']
        
        # Out of scope topics (non-policy related) - expanded to exclude general topics
        self.non_policy_topics = [
            'weather', 'sports', 'entertainment news', 'movies', 'music', 'food', 'recipes',
            'fashion', 'travel', 'jokes', 'memes', 'dating', 'relationships',
            'stocks', 'cryptocurrency', 'bitcoin', 'shopping', 'celebrity news',
            'programming tutorials', 'coding help', 'software development', 'math homework', 
            'physics', 'chemistry', 'biology', 'science facts', 'personal advice',
            'general knowledge', 'trivia', 'history facts', 'geography', 'animals', 'plants',
            'space', 'astronomy', 'literature', 'books', 'cooking', 'personal finance',
            'car maintenance', 'home improvement', 'gardening', 'pets', 'hobbies'
        ]
        
        # Spelling correction mappings for common typos
        self.spelling_corrections = {
            # Common greeting/thank you typos
            'thnks': 'thanks',
            'thanx': 'thanks', 
            'thx': 'thanks',
            'thnak': 'thank',
            'thnk': 'thank',
            'thankyou': 'thank you',
            'helo': 'hello',
            'hllo': 'hello',
            'hi': 'hi',  # Keep as is
            'hy': 'hi',
            'hii': 'hi',
            'heelo': 'hello',
            'hellow': 'hello',
            'helo': 'hello',
            'helllo': 'hello',
            'hi there': 'hi there',  # Keep as is
            
            # Common acknowledgment typos
            'ok': 'ok',  # Keep as is
            'okey': 'okay',
            'okk': 'ok',
            'okya': 'okay',
            'oky': 'okay',
            'alrigt': 'alright',
            'alrite': 'alright',
            'alrigth': 'alright',
            'alrigh': 'alright',
            'sure': 'sure',  # Keep as is
            'sur': 'sure',
            'shure': 'sure',
            'rigt': 'right',
            'rigth': 'right',
            'rite': 'right',
            'riht': 'right',
            
            # Common apologetic typos
            'sory': 'sorry',
            'sorri': 'sorry',
            'sori': 'sorry',
            'sorr': 'sorry',
            'soory': 'sorry',
            'apologise': 'apologize',
            'appologize': 'apologize',
            'apoligize': 'apologize',
            
            # Common goodbye typos
            'by': 'bye',
            'bai': 'bye',
            'bey': 'bye',
            'byee': 'bye',
            'goodby': 'goodbye',
            'gooodbye': 'goodbye',
            'good bye': 'goodbye',
            
            # Policy-related typos
            'polcy': 'policy',
            'poicy': 'policy',
            'polici': 'policy',
            'policys': 'policies',
            'polcies': 'policies',
            'poicies': 'policies',
            'comparision': 'comparison',
            'comparision': 'comparison',
            'diference': 'difference',
            'diferent': 'different',
            'diferrence': 'difference',
            'betwen': 'between',
            'betwenn': 'between',
            'beetween': 'between',
            'contries': 'countries',
            'coutries': 'countries',
            'countires': 'countries',
            
            # AI and tech-related typos
            'artifical': 'artificial',
            'artifical intelligence': 'artificial intelligence',
            'ai safety': 'ai safety',  # Keep as is
            'cyber security': 'cybersecurity',
            'cyber-security': 'cybersecurity',
            'saftey': 'safety',
            'safty': 'safety',
            'secuirty': 'security',
            'securty': 'security',
            'secrity': 'security',
            
            # Common word typos
            'adn': 'and',
            'an': 'and',  # Context dependent, but often a typo
            'teh': 'the',
            'te': 'the',
            'thhe': 'the',
            'tehre': 'there',
            'ther': 'there',
            'thier': 'their',
            'theri': 'their',
            'form': 'from',  # Context dependent
            'fomr': 'from',
            'wit': 'with',
            'wiht': 'with',
            'wih': 'with',
            'whit': 'with',
            'wnat': 'want',
            'waht': 'what',
            'wnat': 'want',
            'whta': 'what',
            'hwat': 'what',
            'hwo': 'how',
            'how': 'how',  # Keep as is
            'cna': 'can',
            'acn': 'can',
            'yuor': 'your',
            'yoru': 'your',
            'oyu': 'you',
            'yuo': 'you',
            'u': 'you',
            'ur': 'your',
            'pls': 'please',
            'plz': 'please',
            'plase': 'please',
            'pleae': 'please',
            'plese': 'please'
        }

    async def get_db(self):
        """Get DynamoDB connection"""
        if not self._db:
            self._db = await get_dynamodb()
        return self._db

    async def _update_cache(self):
        """Update policy cache with latest data"""
        try:
            current_time = datetime.utcnow().timestamp()
            
            # Check if cache needs update
            if (self.last_cache_update and 
                current_time - self.last_cache_update < self.cache_duration and 
                self.policy_cache):
                return
            
            db = await self.get_db()
            
            # Get all approved policies
            all_policies = await db.scan_table('policies')
            
            # Process and cache policy data
            self.policy_cache = []
            countries_set = set()
            areas_set = set()
            
            for policy in all_policies:
                if policy.get('status') in ['approved', 'master']:
                    country = policy.get('country', '').strip()
                    if country:
                        countries_set.add(country)
                    
                    policy_areas = policy.get('policy_areas', [])
                    for area in policy_areas:
                        area_name = area.get('area_name', '').strip()
                        if area_name:
                            areas_set.add(area_name)
                        
                        for p in area.get('policies', []):
                            if p.get('status') == 'approved' or policy.get('status') == 'master':
                                policy_data = {
                                    'country': country,
                                    'area_name': area_name,
                                    'policy_name': p.get('policyName', ''),
                                    'policy_description': p.get('policyDescription', ''),
                                    'implementation': p.get('implementation', ''),
                                    'evaluation': p.get('evaluation', ''),
                                    'participation': p.get('participation', ''),
                                    'policy_id': policy.get('policy_id'),
                                    'created_at': policy.get('created_at'),
                                    'approved_at': p.get('approved_at')
                                }
                                self.policy_cache.append(policy_data)
            
            self.countries_cache = sorted(list(countries_set))
            self.areas_cache = sorted(list(areas_set))
            self.last_cache_update = current_time
            
            print(f"Cache updated: {len(self.policy_cache)} policies, {len(self.countries_cache)} countries, {len(self.areas_cache)} areas")
            
        except Exception as e:
            print(f"Error updating cache: {e}")

    def _correct_spelling_mistakes(self, message: str) -> tuple[str, bool]:
        """
        Detect and correct common spelling mistakes in user messages.
        Returns (corrected_message, was_corrected)
        """
        try:
            original_message = message
            corrected_message = message.lower()
            corrections_made = []
            
            # Split message into words for word-level corrections
            words = corrected_message.split()
            corrected_words = []
            
            for word in words:
                # Remove punctuation for matching but keep it for reconstruction
                clean_word = re.sub(r'[^\w]', '', word)
                punctuation = re.sub(r'[\w]', '', word)
                
                # Check if the clean word needs correction
                if clean_word in self.spelling_corrections:
                    corrected_word = self.spelling_corrections[clean_word]
                    corrected_words.append(corrected_word + punctuation)
                    corrections_made.append(f"'{clean_word}' → '{corrected_word}'")
                else:
                    corrected_words.append(word)
            
            corrected_message = ' '.join(corrected_words)
            
            # Additional phrase-level corrections for multi-word expressions
            phrase_corrections = {
                'thank u': 'thank you',
                'thnk u': 'thank you', 
                'thnk you': 'thank you',
                'thanx u': 'thank you',
                'good mornig': 'good morning',
                'good evning': 'good evening',
                'good afernoon': 'good afternoon',
                'good afteroon': 'good afternoon',
                'artifical intelligence': 'artificial intelligence',
                'cyber saftey': 'cybersafety',
                'cyber safty': 'cybersafety',
                'ai safty': 'ai safety',
                'ai saftey': 'ai safety',
                'comparision between': 'comparison between',
                'diference between': 'difference between',
                'beetween countries': 'between countries'
            }
            
            for incorrect_phrase, correct_phrase in phrase_corrections.items():
                if incorrect_phrase in corrected_message:
                    corrected_message = corrected_message.replace(incorrect_phrase, correct_phrase)
                    corrections_made.append(f"'{incorrect_phrase}' → '{correct_phrase}'")
            
            # Check if any corrections were made
            was_corrected = len(corrections_made) > 0
            
            if was_corrected:
                print(f"Spelling corrections made: {', '.join(corrections_made)}")
                # Preserve original capitalization pattern as much as possible
                corrected_message = self._preserve_capitalization(original_message, corrected_message)
            
            return corrected_message if was_corrected else original_message, was_corrected
            
        except Exception as e:
            print(f"Error in spelling correction: {e}")
            return message, False

    def _preserve_capitalization(self, original: str, corrected: str) -> str:
        """
        Attempt to preserve the original capitalization pattern in the corrected message
        """
        try:
            # Simple approach: if original was all caps, return all caps
            if original.isupper():
                return corrected.upper()
            
            # If original started with capital letter, capitalize the corrected message
            if original and original[0].isupper():
                return corrected.capitalize()
            
            # Otherwise return as is
            return corrected
            
        except Exception as e:
            print(f"Error preserving capitalization: {e}")
            return corrected

    def _calculate_similarity(self, word1: str, word2: str) -> float:
        """
        Calculate similarity between two words using simple edit distance
        Returns a score between 0 and 1 (1 = identical)
        """
        try:
            if word1 == word2:
                return 1.0
            
            # Simple Levenshtein distance calculation
            len1, len2 = len(word1), len(word2)
            if len1 == 0:
                return 0.0 if len2 > 0 else 1.0
            if len2 == 0:
                return 0.0
            
            # Create a matrix for dynamic programming
            matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
            
            # Initialize first row and column
            for i in range(len1 + 1):
                matrix[i][0] = i
            for j in range(len2 + 1):
                matrix[0][j] = j
            
            # Fill the matrix
            for i in range(1, len1 + 1):
                for j in range(1, len2 + 1):
                    cost = 0 if word1[i-1] == word2[j-1] else 1
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,      # deletion
                        matrix[i][j-1] + 1,      # insertion
                        matrix[i-1][j-1] + cost  # substitution
                    )
            
            # Calculate similarity score
            max_len = max(len1, len2)
            distance = matrix[len1][len2]
            similarity = (max_len - distance) / max_len
            
            return similarity
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def _smart_spell_check(self, message: str) -> tuple[str, bool, list]:
        """
        Intelligent spell checking that suggests corrections for unknown words
        Returns (corrected_message, was_corrected, suggestions)
        """
        try:
            # First apply direct corrections
            corrected_message, was_directly_corrected = self._correct_spelling_mistakes(message)
            
            if was_directly_corrected:
                return corrected_message, True, []
            
            # If no direct corrections, try fuzzy matching for potential typos
            words = message.lower().split()
            suggestions = []
            
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)
                if len(clean_word) > 2:  # Only check words longer than 2 characters
                    
                    # Check against greeting keywords
                    best_match = None
                    best_score = 0.0
                    
                    # Check all keyword categories for fuzzy matches
                    all_keywords = (self.greeting_keywords + 
                                  self.acknowledgment_keywords + 
                                  self.apologetic_keywords + 
                                  self.help_keywords)
                    
                    for keyword in all_keywords:
                        for keyword_word in keyword.split():
                            similarity = self._calculate_similarity(clean_word, keyword_word)
                            if similarity > best_score and similarity > 0.7:  # 70% similarity threshold
                                best_score = similarity
                                best_match = keyword_word
                    
                    if best_match and best_score > 0.7:
                        suggestions.append({
                            'original': clean_word,
                            'suggestion': best_match,
                            'confidence': best_score
                        })
            
            return message, False, suggestions
            
        except Exception as e:
            print(f"Error in smart spell check: {e}")
            return message, False, []

    def _is_simple_conversational(self, message_lower: str) -> bool:
        """Check if message is a simple conversational phrase that should get acknowledgment response"""
        # Patterns for simple conversational phrases
        simple_patterns = [
            # Apologetic phrases
            "oh ok, sorry",
            "sorry for asking",
            "my bad",
            "oops",
            # Simple expressions  
            "nice",
            "cool",
            "great",
            "awesome",
            "perfect",
            "excellent",
            "wonderful",
            "interesting",
            # Combination phrases
            "oh ok",
            "oh alright", 
            "oh sure",
            "ah ok",
            "ah i see",
            # Short responses
            "i see",
            "makes sense",
            "got it"
        ]
        
        # Check if the message is short and matches conversational patterns
        if len(message_lower.split()) <= 5:  # 5 words or less
            for pattern in simple_patterns:
                if pattern in message_lower:
                    return True
                    
            # Check for single word acknowledgments
            single_words = ['nice', 'cool', 'great', 'awesome', 'perfect', 'excellent', 'wonderful', 'interesting']
            if message_lower.strip() in single_words:
                return True
        
        return False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat endpoint with intelligent spelling correction"""
        try:
            # Update cache first
            await self._update_cache()
            
            # Apply intelligent spelling correction to user message
            original_message = request.message
            corrected_message, was_corrected = self._correct_spelling_mistakes(original_message)
            
            # Use corrected message for processing
            processed_message = corrected_message
            
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                request.conversation_id, 
                request.user_id
            )
            
            # Create user message (store original message but process corrected one)
            user_message = ChatMessage(
                role="user",
                content=original_message,  # Store original for conversation history
                timestamp=datetime.utcnow()
            )
            
            # Extract conversation context from history
            context = self._extract_conversation_context(conversation.messages, processed_message)
            
            # Check for greetings first (priority handling) - using corrected message
            message_lower = processed_message.lower().strip()
            if any(keyword in message_lower for keyword in self.greeting_keywords):
                ai_response = await self._get_greeting_response(processed_message, conversation.messages, was_corrected, original_message)
            # Check for simple acknowledgments or apologetic phrases
            elif (any(keyword == message_lower for keyword in self.acknowledgment_keywords) or 
                  any(keyword in message_lower for keyword in self.apologetic_keywords) or
                  self._is_simple_conversational(message_lower)):
                ai_response = await self._get_acknowledgment_response(processed_message, conversation.messages, was_corrected, original_message)
            # Check for help requests
            elif any(keyword in message_lower for keyword in self.help_keywords):
                ai_response = await self._get_help_response(processed_message, conversation.messages)
            else:
                # Check if this is a policy-related query with context
                is_policy_query = await self._is_policy_related_query(processed_message, context)
                
                # Generate AI response based on whether it's policy-related
                if is_policy_query:
                    # Check if it's a comparison query
                    if self._is_comparison_query(processed_message):
                        ai_response = await self._handle_country_comparison(processed_message, conversation.messages, context)
                    else:
                        # Find relevant policies with context
                        policies = await self._find_relevant_policies_with_context(processed_message, context)
                        if policies:
                            ai_response = await self._get_policy_response(processed_message, policies, conversation.messages)
                        else:
                            ai_response = await self._get_no_data_response(processed_message)
                else:
                    # Non-policy response
                    ai_response = await self._get_non_policy_response(processed_message)
            
            # Create AI message
            ai_message = ChatMessage(
                role="assistant",
                content=ai_response,
                timestamp=datetime.utcnow()
            )
            
            # Add messages to conversation
            conversation.messages.extend([user_message, ai_message])
            conversation.updated_at = datetime.utcnow()
            
            # Save conversation
            await self._save_conversation(conversation)
            
            return ChatResponse(
                response=ai_response,
                conversation_id=conversation.conversation_id
            )
            
        except Exception as e:
            print(f"Chat error: {e}")
            return ChatResponse(
                response="I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                conversation_id=request.conversation_id or "new"
            )

    async def _get_or_create_conversation(self, conversation_id: Optional[str], user_id: Optional[str]) -> ChatConversation:
        """Get existing conversation or create new one"""
        try:
            if conversation_id:
                db = await self.get_db()
                conversation_data = await db.get_item('chat_sessions', {'session_id': conversation_id})
                
                if conversation_data:
                    messages = []
                    for msg_data in conversation_data.get('messages', []):
                        message = ChatMessage(
                            role=msg_data.get('role'),
                            content=msg_data.get('content'),
                            timestamp=datetime.fromisoformat(msg_data.get('timestamp'))
                        )
                        messages.append(message)
                    
                    return ChatConversation(
                        conversation_id=conversation_id,
                        messages=messages,
                        created_at=datetime.fromisoformat(conversation_data.get('created_at')),
                        updated_at=datetime.fromisoformat(conversation_data.get('updated_at', conversation_data.get('created_at')))
                    )
            
            # Create new conversation
            conversation_id = f"conv_{datetime.utcnow().timestamp()}"
            new_conversation = ChatConversation(
                conversation_id=conversation_id,
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return new_conversation
            
        except Exception as e:
            print(f"Error getting/creating conversation: {e}")
            conversation_id = f"conv_{datetime.utcnow().timestamp()}"
            return ChatConversation(
                conversation_id=conversation_id,
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

    async def _save_conversation(self, conversation: ChatConversation):
        """Save conversation to database"""
        try:
            db = await self.get_db()
            
            conversation_data = {
                'session_id': conversation.conversation_id,
                'messages': [
                    {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat()
                    }
                    for msg in conversation.messages
                ],
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
            
            await db.insert_item('chat_sessions', conversation_data)
            
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def _is_policy_related_query(self, message: str) -> bool:
        """Check if the message is related to any policy area or governance"""
        message_lower = message.lower()
        
        # Policy-related keywords (expanded for all 10 policy areas)
        policy_keywords = [
            'policy', 'policies', 'governance', 'regulation', 'law', 'legislation',
            'government', 'framework', 'strategy', 'implementation', 'evaluation', 
            'compliance', 'standard', 'guideline', 'principle',
            # AI Safety
            'ai', 'artificial intelligence', 'ai safety', 'machine learning', 'automation',
            # CyberSafety
            'cyber', 'cybersecurity', 'digital security', 'data protection', 'privacy',
            # Digital Education
            'digital education', 'online learning', 'educational technology', 'e-learning',
            # Digital Inclusion
            'digital divide', 'digital inclusion', 'accessibility', 'internet access',
            # Digital Leisure
            'gaming', 'digital leisure', 'entertainment', 'online gaming', 'digital recreation',
            # Disinformation
            'misinformation', 'disinformation', 'fake news', 'information', 'media literacy',
            # Digital Work
            'digital work', 'remote work', 'gig economy', 'digital employment', 'future of work',
            # Mental Health
            'mental health', 'digital wellness', 'screen time', 'digital wellbeing',
            # Physical Health
            'physical health', 'healthcare technology', 'telemedicine', 'health tech',
            # Social Media/Gaming Regulation
            'social media', 'platform regulation', 'content moderation', 'gaming regulation'
        ]
        
        # Check if message contains any policy keywords
        for keyword in policy_keywords:
            if keyword in message_lower:
                return True
        
        # Check if message mentions any country from our database
        if self.countries_cache:
            for country in self.countries_cache:
                if country and country.lower() in message_lower:
                    return True
        
        # Check if message mentions any policy area from our database
        if self.areas_cache:
            for area in self.areas_cache:
                if area and area.lower() in message_lower:
                    return True
        
        return False

    def _extract_conversation_context(self, conversation_history: List[ChatMessage], current_message: str) -> Dict[str, Any]:
        """Extract relevant context from recent conversation history"""
        context = {
            'mentioned_countries': set(),
            'mentioned_areas': set(),
            'recent_queries': [],
            'last_topic': None
        }
        
        # Analyze last 10 messages (5 exchanges) for context
        recent_messages = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        
        for message in recent_messages:
            # Check if message has role or message_type attribute
            message_role = getattr(message, 'role', None) or getattr(message, 'message_type', None)
            if message_role == "user":
                content_lower = message.content.lower()
                context['recent_queries'].append(content_lower)
                
                # Extract countries mentioned in recent conversation
                if self.countries_cache:
                    for country in self.countries_cache:
                        if country:
                            country_lower = country.lower()
                            if (country_lower in content_lower or
                                (country_lower == "united states" and any(term in content_lower for term in ["usa", "us ", " us", "america", "american"])) or
                                (country_lower == "united kingdom" and any(term in content_lower for term in ["uk ", " uk", "britain", "british"]))):
                                context['mentioned_countries'].add(country)
                
                # Extract policy areas mentioned
                if self.areas_cache:
                    for area in self.areas_cache:
                        if area and area.lower() in content_lower:
                            context['mentioned_areas'].add(area)
                        elif area == "AI Safety" and any(term in content_lower for term in ["ai", "artificial intelligence", "ai policy"]):
                            context['mentioned_areas'].add(area)
                
                # Identify the topic of the last substantial query
                if any(keyword in content_lower for keyword in ['policy', 'policies', 'ai', 'cyber', 'digital', 'governance']):
                    context['last_topic'] = content_lower
        
        return context

    def _is_comparison_query(self, message: str) -> bool:
        """Check if the message is asking for a comparison between countries/policies"""
        message_lower = message.lower()
        comparison_patterns = [
            'difference between',
            'compare',
            'vs',
            'versus',
            'different from',
            'contrast',
            'how does',
            'what\'s the difference',
            'whats the difference'
        ]
        
        return any(pattern in message_lower for pattern in comparison_patterns)

    async def _is_policy_related_query(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Enhanced policy-related query detection with conversation context"""
        message_lower = message.lower()
        
        # If context suggests we're already discussing policies, be more lenient
        if context and (context.get('mentioned_countries') or context.get('mentioned_areas') or 
                       any('policy' in query for query in context.get('recent_queries', []))):
            # Allow follow-up questions that might not explicitly mention policy keywords
            comparison_words = ['difference', 'compare', 'vs', 'versus', 'between', 'different', 'contrast', 'how does']
            if any(word in message_lower for word in comparison_words):
                return True
        
        # Original policy detection logic
        policy_keywords = [
            'policy', 'policies', 'governance', 'regulation', 'law', 'legislation',
            'government', 'framework', 'strategy', 'implementation', 'evaluation', 
            'compliance', 'standard', 'guideline', 'principle',
            # AI Safety
            'ai', 'artificial intelligence', 'ai safety', 'machine learning', 'automation',
            # CyberSafety
            'cyber', 'cybersecurity', 'digital security', 'data protection', 'privacy',
            # Digital Education
            'digital education', 'online learning', 'educational technology', 'e-learning',
            # Digital Inclusion
            'digital divide', 'digital inclusion', 'accessibility', 'internet access',
            # Digital Leisure
            'gaming', 'digital leisure', 'entertainment', 'online gaming', 'digital recreation',
            # Disinformation
            'misinformation', 'disinformation', 'fake news', 'information', 'media literacy',
            # Digital Work
            'digital work', 'remote work', 'gig economy', 'digital employment', 'future of work',
            # Mental Health
            'mental health', 'digital wellness', 'screen time', 'digital wellbeing',
            # Physical Health
            'physical health', 'healthcare technology', 'telemedicine', 'health tech',
            # Social Media/Gaming Regulation
            'social media', 'platform regulation', 'content moderation', 'gaming regulation'
        ]
        
        # Check if message contains any policy keywords
        for keyword in policy_keywords:
            if keyword in message_lower:
                return True
        
        # Check if message mentions any country from our database
        if self.countries_cache:
            for country in self.countries_cache:
                if country and country.lower() in message_lower:
                    return True
        
        # Check if message mentions any policy area from our database
        if self.areas_cache:
            for area in self.areas_cache:
                if area and area.lower() in message_lower:
                    return True

    async def _generate_ai_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate AI response based on message and context with conversation memory"""
        # Ensure message is a string
        if not isinstance(message, str):
            message = str(message)
            
        message_lower = message.lower().strip()
        
        # Extract conversation context from recent messages (last 5 exchanges)
        recent_context = self._extract_conversation_context(conversation_history, message)
        
        # Check for greetings
        if any(keyword in message_lower for keyword in self.greeting_keywords):
            return await self._get_greeting_response(message, conversation_history)
        
        # Check for help requests
        if any(keyword in message_lower for keyword in self.help_keywords):
            return await self._get_help_response(message, conversation_history)
        
        # Check for explicit non-policy topics first
        if any(topic in message_lower for topic in self.non_policy_topics):
            return await self._get_non_policy_response(message)
        
        # Check if the query is actually policy-related (enhanced with context)
        if not await self._is_policy_related_query(message, recent_context):
            return await self._get_non_policy_response(message)
        
        # Enhanced comparison detection with context awareness
        if any(keyword in message_lower for keyword in self.comparison_keywords):
            return await self._handle_country_comparison_with_context(message, recent_context)
        
        # Search for relevant policies (enhanced with context)
        relevant_policies = await self._find_relevant_policies_with_context(message, recent_context)
        
        if relevant_policies:
            return await self._get_policy_response(message, relevant_policies, conversation_history)
        else:
            # No relevant policies found - suggest submission
            return await self._get_no_data_response(message)

    async def _find_relevant_policies(self, query: str) -> List[Dict]:
        """Find policies relevant to the query - strict matching for precise results"""
        if not self.policy_cache:
            return []
        
        query_lower = query.lower()
        relevant_policies = []
        
        # Extract specific country and area mentions for strict filtering
        mentioned_countries = []
        mentioned_areas = []
        
        # Find mentioned countries (support common variations and typos)
        if self.countries_cache:
            for country in self.countries_cache:
                if country and (country.lower() in query_lower or 
                               # Handle common variations and typos
                               (country.lower() == "united states" and any(term in query_lower for term in ["usa", "us ", " us", "america", "american", "use "])) or  # "use" might be typo for "us"
                               (country.lower() == "united kingdom" and any(term in query_lower for term in ["uk ", " uk", "britain", "british"]))):
                    mentioned_countries.append(country.lower())
        
        # Find mentioned areas
        if self.areas_cache:
            for area in self.areas_cache:
                if area and area.lower() in query_lower:
                    mentioned_areas.append(area.lower())
        
        # Score policies based on relevance with strict filtering
        for policy in self.policy_cache:
            score = 0
            country = policy.get('country', '').lower()
            area = policy.get('area_name', '').lower()
            
            # If user mentioned specific countries, only show those countries
            if mentioned_countries and country not in mentioned_countries:
                continue
                
            # If user mentioned specific areas, only show those areas
            if mentioned_areas and area not in mentioned_areas:
                continue
            
            # Score based on matches (be more flexible with country matching)
            if (country in query_lower or 
                # Handle common country name variations and typos
                (country == "united states" and any(term in query_lower for term in ["usa", "us ", " us", "america", "american", "use "])) or  # "use" might be typo for "us"
                (country == "united kingdom" and any(term in query_lower for term in ["uk ", " uk", "britain", "british"]))):
                score += 10
            
            # Enhanced area matching - be more flexible with AI Safety terms
            area_match_score = 0
            if area in query_lower:
                area_match_score = 8
            elif area == "ai safety" and any(term in query_lower for term in ["ai", "artificial intelligence", "ai policy", "ai governance"]):
                area_match_score = 6
            elif area == "cybersafety" and any(term in query_lower for term in ["cyber", "cybersecurity", "digital security"]):
                area_match_score = 6
            
            score += area_match_score
            
            # Check policy name match
            if policy.get('policy_name') and policy['policy_name'].lower() in query_lower:
                score += 15
            
            # Check description match (only if no specific country/area mentioned or if they match)
            if policy.get('policy_description'):
                description_words = policy['policy_description'].lower().split()
                query_words = query_lower.split()
                common_words = set(description_words) & set(query_words)
                if common_words:
                    score += len(common_words) * 2
            
            # Check implementation, evaluation, participation
            for field in ['implementation', 'evaluation', 'participation']:
                field_value = policy.get(field)
                if field_value and isinstance(field_value, str):
                    query_words = query_lower.split()
                    if any(word in field_value.lower() for word in query_words):
                        score += 3
            
            if score > 0:
                policy['relevance_score'] = score
                relevant_policies.append(policy)
        
        # Sort by relevance and return top results
        relevant_policies.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_policies[:10]  # Return top 10 relevant policies

    async def _find_relevant_policies_with_context(self, query: str, context: Dict[str, Any]) -> List[Dict]:
        """Find relevant policies with conversation context"""
        # Start with the base query
        policies = await self._find_relevant_policies(query)
        
        # If no policies found but we have context, try expanding the search
        if not policies and context:
            expanded_queries = []
            
            # Add context from mentioned countries
            for country in context.get('mentioned_countries', []):
                expanded_queries.append(f"{query} {country}")
            
            # Add context from mentioned areas
            for area in context.get('mentioned_areas', []):
                expanded_queries.append(f"{query} {area}")
            
            # Try the last topic if available
            if context.get('last_topic'):
                expanded_queries.append(f"{query} {context['last_topic']}")
            
            # Search with expanded queries
            for expanded_query in expanded_queries:
                expanded_policies = await self._find_relevant_policies(expanded_query)
                if expanded_policies:
                    policies.extend(expanded_policies)
            
            # Remove duplicates based on policy_id
            seen_ids = set()
            unique_policies = []
            for policy in policies:
                policy_id = policy.get('policy_id') or policy.get('id')
                if policy_id and policy_id not in seen_ids:
                    seen_ids.add(policy_id)
                    unique_policies.append(policy)
            
            policies = unique_policies
        
        return policies

    async def _get_greeting_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate human-friendly greeting response"""
        try:
            message_lower = message.lower().strip()
            
            # Check if this is a thank you/appreciation after conversation (context-aware)
            is_thank_you = any(word in message_lower for word in ['thank', 'appreciate'])
            is_goodbye = any(word in message_lower for word in ['goodbye', 'bye', 'see you', 'farewell', 'have a nice day', 'take care'])
            has_conversation_history = len(conversation_history) > 2  # More than just this exchange
            
            # If it's a thank you or goodbye after conversation, give a simple, natural response
            if (is_thank_you or is_goodbye) and has_conversation_history:
                if is_goodbye:
                    farewell_responses = [
                        "Goodbye! Feel free to come back anytime you have policy questions.",
                        "Take care! I'm always here when you need policy insights.",
                        "See you later! Don't hesitate to ask if you need help with policies.",
                        "Have a great day! Come back whenever you need policy information.",
                        "Farewell! I'll be here whenever you want to explore policy topics.",
                        "Bye! Always happy to help with policy questions."
                    ]
                    import random
                    return random.choice(farewell_responses)
                else:  # is_thank_you
                    thank_responses = [
                        "You're very welcome! I'm glad I could help.",
                        "Happy to assist! That's what I'm here for.",
                        "You're welcome! Feel free to ask anytime.",
                        "My pleasure! Always happy to help with policy insights.",
                        "Glad I could help! Don't hesitate to reach out if you need anything else.",
                        "You're most welcome! Have a great day!",
                        "Anytime! Feel free to come back whenever you have policy questions."
                    ]
                    import random
                    return random.choice(thank_responses)
            
            # Detect greeting type for appropriate response (initial greetings)
            if is_thank_you:
                greeting_responses = [
                    "You're very welcome! I'm glad I could help.",
                    "Happy to assist! That's what I'm here for.",
                    "You're welcome! Feel free to ask anytime.",
                    "My pleasure! Always happy to help with policy insights."
                ]
            elif is_goodbye:
                greeting_responses = [
                    "Goodbye! Feel free to come back anytime.",
                    "Take care! I'm always here when you need help.",
                    "See you later! Don't hesitate to ask if you need assistance.",
                    "Have a great day! Come back whenever you need information."
                ]
            elif any(word in message_lower for word in ['good morning', 'morning']):
                greeting_responses = [
                    "Good morning! Hope you're having a great day.",
                    "Morning! Ready to explore some policy insights?",
                    "Good morning! What policy area interests you today?"
                ]
            elif any(word in message_lower for word in ['good afternoon', 'afternoon']):
                greeting_responses = [
                    "Good afternoon! How can I help you today?",
                    "Afternoon! What policy questions do you have?",
                    "Good afternoon! Ready to dive into some policy analysis?"
                ]
            elif any(word in message_lower for word in ['good evening', 'evening']):
                greeting_responses = [
                    "Good evening! What brings you here today?",
                    "Evening! Looking for some policy insights?",
                    "Good evening! How can I assist you tonight?"
                ]
            else:
                greeting_responses = [
                    "Hello there! Great to meet you.",
                    "Hi! Welcome, I'm excited to help you today.",
                    "Hey! Nice to see you here.",
                    "Hello! Wonderful to connect with you."
                ]
            
            # Pick a friendly greeting
            import random
            friendly_greeting = random.choice(greeting_responses)
            
            # Add the helpful information only for initial greetings (not for thank you/goodbye responses)
            if not (is_thank_you or is_goodbye):
                helpful_info = f"""\n\nI'd be happy to answer questions about:
• Policies from {len(self.countries_cache)} countries across 10 policy areas
• AI Safety, CyberSafety, Digital Education, Digital Inclusion
• Digital Leisure, (Dis)Information, Digital Work  
• Mental Health, Physical Health, Social Media/Gaming Regulation
• Policy comparisons between nations
• Specific governance frameworks and implementations

If you're an expert in any policy areas, we'd love for you to contribute your knowledge to expand our database! Just use our form submission option to submit your expertise."""
                return friendly_greeting + helpful_info
            else:
                # For thank you and goodbye, just return the friendly response
                return friendly_greeting
            
        except Exception as e:
            print(f"Error generating greeting: {e}")
            return "Hello! Great to meet you. I'm your Policy Expert Assistant with deep knowledge of policies from around the world across 10 key domains. I'd be happy to answer questions about policies from multiple countries, help with comparisons, and provide detailed insights. What would you like to explore today?"

    async def _get_acknowledgment_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate natural response to simple acknowledgments"""
        try:
            message_lower = message.lower().strip()
            
            # Check if it's an apologetic message
            is_apologetic = any(keyword in message_lower for keyword in self.apologetic_keywords)
            
            if is_apologetic:
                # Gentle responses to apologies
                apologetic_responses = [
                    "No need to apologize! I'm here to help with any policy questions you might have.",
                    "Don't worry about it! Feel free to ask me anything about policies.",
                    "No problem at all! I'm always happy to help with policy-related questions.",
                    "That's perfectly fine! Ask me anything about policies whenever you're ready.",
                    "No worries! I'm here whenever you need policy information.",
                    "Don't apologize! I'm here to assist with any policy questions."
                ]
                import random
                return random.choice(apologetic_responses)
            
            # Natural responses to acknowledgments
            acknowledgment_responses = [
                "Great! Is there anything else you'd like to know about policies?",
                "Perfect! Feel free to ask if you have any other policy questions.",
                "Sounds good! What else can I help you with?",
                "Excellent! Let me know if you need any other policy insights.",
                "Wonderful! I'm here if you have more questions.",
                "Nice! Anything else about policies you'd like to explore?",
                "Got it! Feel free to ask about any policy area that interests you.",
                "Awesome! I'm ready to help with any other policy queries."
            ]
            
            # If there's conversation history, be more contextual
            if len(conversation_history) > 2:
                contextual_responses = [
                    "Got it! Let me know if you have any other questions.",
                    "Perfect! I'm here if you need anything else.",
                    "Sounds good! Feel free to ask if something else comes to mind.",
                    "Understood! I'm ready to help with anything else you need.",
                    "Great! Don't hesitate to reach out if you have more questions."
                ]
                import random
                return random.choice(contextual_responses)
            else:
                # For initial acknowledgments, be more welcoming
                import random
                return random.choice(acknowledgment_responses)
            
        except Exception as e:
            print(f"Error generating acknowledgment response: {e}")
            return "Great! Let me know if you have any other policy questions I can help with."

    async def _get_help_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate friendly help response"""
        try:
            available_countries = ', '.join(self.countries_cache[:10]) + ('...' if len(self.countries_cache) > 10 else '')
            
            friendly_help = f"""I'm here to help you explore global policy insights! Here's what I can do for you:

🔍 **Find Policies**: Ask about specific countries or policy areas
   Example: "What are the AI policies in the United States?" or "Tell me about Canada's cybersecurity policies"

🌍 **Compare Countries**: See how different nations approach similar challenges  
   Example: "Compare AI safety policies between US and EU" or "How do Canada and Australia handle digital education?"

📊 **Explore Areas**: Dive deep into any of our 10 policy domains:
   AI Safety, CyberSafety, Digital Education, Digital Inclusion, Digital Leisure, (Dis)Information, Digital Work, Mental Health, Physical Health, Social Media/Gaming Regulation

📈 **Get Details**: Learn about implementation, evaluation, and participation frameworks

**Available Data**: {len(self.policy_cache)} policies from {len(self.countries_cache)} countries including {available_countries}

Try asking something like "What digital education policies does Germany have?" or "Compare mental health policies between Nordic countries" - I'm here to help! 🚀"""
            
            return friendly_help
            
        except Exception as e:
            print(f"Error generating help: {e}")
            return f"I can help you explore policies across 10 key domains from {len(self.countries_cache)} countries! Try asking me about specific countries, policy areas like AI Safety or CyberSafety, or compare policies between countries. What would you like to explore?"

    async def _get_policy_response(self, query: str, policies: List[Dict], conversation_history: List[ChatMessage]) -> str:
        """Generate AI response about policies using ONLY database information"""
        try:
            prompt = f"""
            User Query: "{query}"
            
            You are responding based EXCLUSIVELY on the specific policies in your database. Do not make assumptions or add information not present in the data.
            
            Available policies for this query: {len(policies)} relevant entries from your database.
            
            Instructions:
            1. Answer the user's question using ONLY the specific policy data provided
            2. If the data is insufficient for a complete answer, say so clearly
            3. Cite specific policy names, countries, and details from your actual database
            4. Do not supplement with general knowledge or assumptions
            5. Be conversational but accurate to your database
            6. If comparisons are possible with your data, provide them
            7. Focus on implementation details, evaluation methods, and participation frameworks from your database
            
            Be helpful and informative, but stay strictly within your database boundaries.
            """
            
            return await self._call_ai_api(prompt, policies)
            
        except Exception as e:
            print(f"Error generating policy response: {e}")
            return self._format_fallback_policy_response(policies)

    async def _handle_country_comparison(self, message: str, conversation_history: List[ChatMessage] = None, context: Dict[str, Any] = None) -> str:
        """Handle country comparison requests with enhanced country detection and conversation context"""
        try:
            message_lower = message.lower()
            mentioned_countries = []
            
            # Start with countries from conversation context if available
            if context and context.get('mentioned_countries'):
                for country in context['mentioned_countries']:
                    if country not in mentioned_countries:
                        mentioned_countries.append(country)
            
            # Enhanced country detection with common variations
            for country in self.countries_cache:
                if country:
                    country_lower = country.lower()
                    # Direct match
                    if country_lower in message_lower:
                        if country not in mentioned_countries:
                            mentioned_countries.append(country)
                    # Handle common variations
                    elif country_lower == "united states" and any(term in message_lower for term in ["usa", "us ", " us", "america", "american"]):
                        if country not in mentioned_countries:
                            mentioned_countries.append(country)
                    elif country_lower == "united kingdom" and any(term in message_lower for term in ["uk ", " uk", "britain", "british"]):
                        if country not in mentioned_countries:
                            mentioned_countries.append(country)
                    elif country_lower == "russia" and any(term in message_lower for term in ["russian"]):
                        if country not in mentioned_countries:
                            mentioned_countries.append(country)
                    elif country_lower == "china" and any(term in message_lower for term in ["chinese"]):
                        if country not in mentioned_countries:
                            mentioned_countries.append(country)
            
            # Remove duplicates while preserving order
            mentioned_countries = list(dict.fromkeys(mentioned_countries))
            
            if len(mentioned_countries) < 2:
                # Enhanced fallback - try to extract from comparison keywords context
                comparison_phrases = [
                    "difference between", "compare", "vs", "versus", "between", 
                    "and", "differ", "contrast"
                ]
                
                # Look for patterns like "USA and Russia", "difference between X and Y"
                for phrase in comparison_phrases:
                    if phrase in message_lower:
                        # Extract text around comparison phrases
                        parts = message_lower.split(phrase)
                        if len(parts) >= 2:
                            # Look for country names in both parts
                            for country in self.countries_cache:
                                country_variations = [country.lower()]
                                if country.lower() == "united states":
                                    country_variations.extend(["usa", "us", "america", "american"])
                                elif country.lower() == "united kingdom":
                                    country_variations.extend(["uk", "britain", "british"])
                                elif country.lower() == "russia":
                                    country_variations.extend(["russian"])
                                elif country.lower() == "china":
                                    country_variations.extend(["chinese"])
                                
                                for variation in country_variations:
                                    if any(variation in part for part in parts) and country not in mentioned_countries:
                                        mentioned_countries.append(country)
                                        break
                        break
            
            if len(mentioned_countries) < 2:
                # Still no luck - provide helpful guidance
                countries_list = ', '.join(self.countries_cache[:8])
                return f"I can help you compare policies across 10 key domains between countries! Please specify which countries you'd like to compare. We have data for: {countries_list}. For example, you could ask 'Compare AI policies between United States and Russia' or 'What's the difference between Canada and Australia cybersafety policies?'"
            
            # Get policies for mentioned countries
            comparison_data = {}
            for country in mentioned_countries[:3]:  # Limit to 3 countries
                country_policies = [p for p in self.policy_cache 
                                  if p.get('country') and p['country'].lower() == country.lower()]
                
                # If we have context about specific policy areas, filter further
                if context and context.get('mentioned_areas'):
                    area_filtered_policies = []
                    for policy in country_policies:
                        policy_area = policy.get('policy_area', '').lower()
                        policy_name = policy.get('policy_name', '').lower()
                        policy_desc = policy.get('policy_description', '').lower()
                        
                        # Check if policy matches any mentioned areas
                        for mentioned_area in context['mentioned_areas']:
                            mentioned_area_lower = mentioned_area.lower()
                            if (mentioned_area_lower in policy_area or
                                mentioned_area_lower in policy_name or
                                mentioned_area_lower in policy_desc or
                                # Special handling for AI Safety
                                (mentioned_area == "AI Safety" and any(term in policy_name or term in policy_desc 
                                    for term in ["ai", "artificial intelligence", "machine learning", "automation"]))):
                                area_filtered_policies.append(policy)
                                break
                    
                    if area_filtered_policies:
                        country_policies = area_filtered_policies
                
                comparison_data[country] = country_policies
            
            if not any(comparison_data.values()):
                return f"I don't have policy data for {' and '.join(mentioned_countries)}. Available countries: {', '.join(self.countries_cache[:10])}"
            
            return await self._generate_country_comparison(mentioned_countries, comparison_data, message)
            
        except Exception as e:
            print(f"Error handling comparison: {e}")
            return "I can help you compare policies between countries across 10 key policy domains. Please specify which countries you'd like to compare from our available data."

    async def _generate_country_comparison(self, countries: List[str], data: Dict[str, List], original_query: str) -> str:
        """Generate AI-powered country comparison using ONLY your database data"""
        try:
            # Collect all relevant policies for training context
            all_comparison_policies = []
            for country_policies in data.values():
                all_comparison_policies.extend(country_policies[:5])  # Top 5 per country
            
            # Check if we have sufficient data for comparison
            countries_with_data = [country for country, policies in data.items() if policies]
            countries_without_data = [country for country, policies in data.items() if not policies]
            
            if len(countries_with_data) < 2:
                # Not enough data for comparison
                missing_countries = ', '.join(countries_without_data)
                available_countries = ', '.join(countries_with_data) if countries_with_data else "none of the requested countries"
                
                return f"I don't have sufficient policy data to compare {', '.join(countries)}. I have data for {available_countries} but not for {missing_countries}. Would you like me to share information about policies from {available_countries[0] if countries_with_data else 'countries where I do have data'}?"
            
            prompt = f"""
            User Query: "{original_query}"
            Countries to Compare: {', '.join(countries_with_data)}
            
            You are comparing policies using ONLY the data from your specific database. Do not add external knowledge.
            
            Available data:
            - Countries with data: {', '.join(countries_with_data)}
            - Countries without data: {', '.join(countries_without_data) if countries_without_data else 'None'}
            
            Instructions:
            1. Compare ONLY the countries for which you have actual database entries
            2. If some requested countries lack data, mention this clearly
            3. Use specific policy names, implementation details, and frameworks from your database
            4. Highlight actual differences and similarities based on your data
            5. Do not speculate or add information not in your database
            6. Be clear about the scope and limitations of your comparison
            
            Structure your response professionally but stay strictly within your database boundaries.
            """
            
            return await self._call_ai_api(prompt, all_comparison_policies)
            
        except Exception as e:
            print(f"Error generating comparison: {e}")
            return self._format_fallback_comparison(countries, data)

    async def _get_non_policy_response(self, message: str) -> str:
        """Response for non-policy related queries"""
        # Check if it's a very short message that might be conversational
        message_lower = message.lower().strip()
        
        # Handle apologetic phrases gently
        if any(word in message_lower for word in ['sorry', 'apologize', 'my bad', 'oops']):
            return "No need to apologize! I'm here to help with any policy questions you might have."
        
        # Handle simple conversational words
        short_conversational = ['ok', 'okay', 'alright', 'sure', 'right', 'cool', 'fine', 'hmm', 'oh', 'ah', 'yes', 'no', 'yeah', 'yep', 'nope', 'nice', 'great', 'awesome', 'perfect', 'excellent', 'wonderful']
        
        if message_lower in short_conversational:
            return "I understand! Is there anything specific about policies you'd like to know?"
        
        # Handle short conversational phrases
        if len(message_lower.split()) <= 3 and any(word in message_lower for word in short_conversational):
            return "I understand! Is there anything specific about policies you'd like to know?"
        
        return f"""I'm sorry, but as a Policy Expert Assistant, I specialize exclusively in policy areas and governance frameworks across 10 key domains. I can't help with general questions like "{message}".

However, I'd be happy to answer questions about:
• Policies from {len(self.countries_cache)} countries across 10 policy areas
• AI Safety, CyberSafety, Digital Education, Digital Inclusion
• Digital Leisure, (Dis)Information, Digital Work
• Mental Health, Physical Health, Social Media/Gaming Regulation
• Policy comparisons between nations  
• Specific governance frameworks and implementations

If you're an expert in any policy areas, we'd love for you to contribute your knowledge to expand our database!"""

    async def _get_no_data_response(self, message: str) -> str:
        """Response when no relevant policies found - handles intelligently based on query specificity"""
        try:
            # Extract specific country and policy area from the message
            mentioned_country = None
            mentioned_area = None
            
            # Check for specific country mention
            if self.countries_cache:
                for country in self.countries_cache:
                    if country and country.lower() in message.lower():
                        mentioned_country = country
                        break
            
            # Check for specific policy area mention
            if self.areas_cache:
                for area in self.areas_cache:
                    if area and area.lower() in message.lower():
                        mentioned_area = area
                        break
            
            # Generate intelligent response based on query specificity
            if mentioned_country and mentioned_area:
                # Very specific query - user wants specific country + area
                response = f"I don't have {mentioned_area} policy data for {mentioned_country} in our database. This could be a valuable addition to our collection!"
                
            elif mentioned_country:
                # Country-specific query - check if we actually have any policies for this country first
                country_policies = []
                if self.policy_cache:
                    for policy in self.policy_cache:
                        if policy.get('country', '').lower() == mentioned_country.lower():
                            country_policies.append(policy)
                
                if country_policies:
                    # We have policies for this country but not the specific area requested
                    available_areas = list(set([p.get('area_name', '') for p in country_policies if p.get('area_name')]))
                    response = f"I don't have the specific policy information you're looking for about {mentioned_country}. However, I do have {mentioned_country} policies in: {', '.join(available_areas[:5])}{'...' if len(available_areas) > 5 else ''}. Would you like information about these areas instead?"
                else:
                    # We truly don't have data for this country
                    response = f"I don't have policy data for {mentioned_country} in our database yet. We're always looking to expand our coverage to include more countries."
                
            elif mentioned_area:
                # Area-specific query - only suggest alternatives if explicitly no data exists
                area_countries = []
                if self.policy_cache:
                    for policy in self.policy_cache:
                        if policy.get('area_name', '').lower() == mentioned_area.lower():
                            country = policy.get('country', '')
                            if country and country not in area_countries:
                                area_countries.append(country)
                
                if area_countries:
                    # Don't automatically suggest other countries - just acknowledge we have that area
                    response = f"I don't have the specific {mentioned_area} data you're looking for. I do have {mentioned_area} policies from other countries in our database if you'd like to explore that area generally."
                else:
                    response = f"I don't have {mentioned_area} policy data in our database yet."
            else:
                # General query
                response = f"I don't have specific information about that in our current database."
            
            # Add contribution encouragement
            response += f"\n\n🌟 **Know about this policy area?** Help us expand our database by contributing your expertise!"
            
            return response
            
        except Exception as e:
            print(f"Error generating no-data response: {e}")
            return f"I don't have specific information about that in our current database. If you're a policy expert, consider contributing your knowledge to help expand our coverage!"

    async def _create_enhanced_system_prompt(self, context_policies: List[Dict] = None) -> str:
        """Create enhanced system prompt using your policy database for training context"""
        
        # Base system prompt
        base_prompt = """You are an Expert Policy Assistant with deep knowledge of global governance frameworks across 10 key policy domains. You have been trained on a comprehensive database of policies from around the world covering:

1. **AI Safety** - AI systems safety and governance
2. **CyberSafety** - Cybersecurity and digital safety  
3. **Digital Education** - Educational technology policies
4. **Digital Inclusion** - Bridging digital divides
5. **Digital Leisure** - Gaming and entertainment policies
6. **(Dis)Information** - Combating misinformation
7. **Digital Work** - Future of work policies
8. **Mental Health** - Digital wellness policies
9. **Physical Health** - Healthcare technology policies
10. **Social Media/Gaming Regulation** - Platform regulation

**YOUR EXPERTISE COVERS:**"""
        
        # Add your actual data statistics
        if self.countries_cache and self.areas_cache and self.policy_cache:
            base_prompt += f"""
- {len(self.countries_cache)} Countries: {', '.join(self.countries_cache[:15])}{'...' if len(self.countries_cache) > 15 else ''}
- {len(self.areas_cache)} Policy Areas: {', '.join(self.areas_cache)}
- {len(self.policy_cache)} Individual Policies with detailed implementation data

**YOUR KNOWLEDGE BASE INCLUDES:**"""
            
            # Add specific examples from your database
            country_examples = {}
            for policy in self.policy_cache[:20]:  # Sample policies for training context
                country = policy.get('country', '')
                if country and country not in country_examples:
                    country_examples[country] = []
                if country and len(country_examples[country]) < 3:
                    country_examples[country].append({
                        'area': policy.get('area_name', ''),
                        'policy': policy.get('policy_name', ''),
                        'description': policy.get('policy_description', '')[:200]
                    })
            
            for country, policies in list(country_examples.items())[:8]:
                base_prompt += f"\n\n**{country}:**"
                for p in policies:
                    base_prompt += f"\n- {p['area']}: {p['policy']} - {p['description']}..."
        
        # Add specific context policies if provided
        if context_policies:
            base_prompt += "\n\n**SPECIFIC CONTEXT FOR THIS QUERY:**"
            for i, policy in enumerate(context_policies[:5]):
                base_prompt += f"""
{i+1}. **{policy.get('policy_name', 'Unknown Policy')}** ({policy.get('country', 'Unknown')} - {policy.get('area_name', 'Unknown Area')})
   Description: {policy.get('policy_description', 'No description available')}
   Implementation: {policy.get('implementation', 'Not specified')}
   Evaluation: {policy.get('evaluation', 'Not specified')}
   Participation: {policy.get('participation', 'Not specified')}"""
        
        base_prompt += """

**YOUR RESPONSE STYLE:**
- Act as a specialized policy expert who ONLY knows about policies in your specific database
- NEVER make up or assume policy information that's not in your database
- If asked about specific countries/areas not in your data, clearly state you don't have that information
- Only suggest alternatives when explicitly asked or when it would be genuinely helpful
- Provide specific, detailed responses citing exact policy names, countries, and implementation details from your database
- Compare and contrast different approaches when relevant, but only using your actual data
- Use professional yet conversational tone
- If asked about areas outside these 10 policy domains, politely redirect while acknowledging their expertise needs
- When you don't have specific data, encourage contribution rather than providing irrelevant alternatives

**CRITICAL RULES:**
1. ONLY use information from your actual policy database
2. If specific country/area data doesn't exist, say so clearly and don't substitute with other data unless explicitly asked
3. Be helpful but precise - don't overwhelm users with irrelevant information when they ask for specific country/area combinations
4. When user asks for specific country policies (like "USA", "America", "US"), focus ONLY on that country's data
5. Encourage data contribution when gaps are identified
6. If user asks about "AI policy in [country]" or "[country] AI policies", show ONLY that country's AI-related policies

**REMEMBER:** You have intimate knowledge of each policy's nuances, implementation challenges, and real-world impacts across AI Safety, CyberSafety, Digital Education, Digital Inclusion, Digital Leisure, (Dis)Information, Digital Work, Mental Health, Physical Health, and Social Media/Gaming Regulation. Use this expertise to provide exceptional insights, but ONLY from your actual database."""
        
        return base_prompt

    async def _call_ai_api(self, prompt: str, context_policies: List[Dict] = None) -> str:
        """Call AI API (ChatGPT Only - GROQ functionality commented out)"""
        try:
            # Use ChatGPT as the primary and only AI model
            if self.openai_api_key:
                response = await self._call_openai_api(prompt, context_policies)
                if response:
                    return response
                else:
                    return "I apologize, but I'm having trouble connecting to ChatGPT right now. Please check your API key and try again."
            else:
                return "ChatGPT API key is not configured. Please set your OPENAI_API_KEY environment variable."
            
            # GROQ Fallback - COMMENTED OUT (Using ChatGPT only)
            # if self.groq_api_key:
            #     response = await self._call_groq_api(prompt)
            #     if response:
            #         return response
            
        except Exception as e:
            print(f"Error calling ChatGPT API: {e}")
            return "I apologize, but I'm experiencing technical difficulties with ChatGPT. Please try again in a moment."

    async def _call_openai_api(self, prompt: str, context_policies: List[Dict] = None) -> Optional[str]:
        """Call ChatGPT (OpenAI GPT-4) API with enhanced context from your policy database"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            # Create comprehensive system message using your policy data
            system_content = await self._create_enhanced_system_prompt(context_policies)
            
            payload = {
                "model": "gpt-4",  # Using ChatGPT-4 as the primary and only AI model
                "messages": [
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.7,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.1
            }
            
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self.openai_api_url, headers=headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
                
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            return None

    # GROQ API Method - COMMENTED OUT (Using ChatGPT only)
    # async def _call_groq_api(self, prompt: str) -> Optional[str]:
    #     """Call GROQ API as fallback - DISABLED"""
    #     try:
    #         headers = {
    #             "Authorization": f"Bearer {self.groq_api_key}",
    #             "Content-Type": "application/json"
    #         }
    #         
    #         payload = {
    #             "model": "llama3-8b-8192",
    #             "messages": [
    #                 {
    #                     "role": "system",
    #                     "content": "You are a professional Policy Expert Assistant covering 10 key policy domains: AI Safety, CyberSafety, Digital Education, Digital Inclusion, Digital Leisure, (Dis)Information, Digital Work, Mental Health, Physical Health, and Social Media/Gaming Regulation. Provide helpful, accurate, and conversational responses about policies across these domains."
    #                 },
    #                 {
    #                     "role": "user",
    #                     "content": prompt
    #                 }
    #             ],
    #             "max_tokens": 500,
    #             "temperature": 0.7
    #         }
    #         
    #         async with httpx.AsyncClient(timeout=30.0) as client:
    #             response = await client.post(self.groq_api_url, headers=headers, json=payload)
    #             response.raise_for_status()
    #             
    #             data = response.json()
    #             return data['choices'][0]['message']['content'].strip()
    #             
    #     except Exception as e:
    #         print(f"GROQ API error: {e}")
    #         return None

    def _format_fallback_policy_response(self, policies: List[Dict]) -> str:
        """Fallback policy response if AI fails"""
        if not policies:
            return "I couldn't find relevant policies for your query."
        
        response = f"I found {len(policies)} relevant policies:\n\n"
        for i, policy in enumerate(policies[:3]):
            response += f"**{i+1}. {policy['policy_name']}** ({policy['country']} - {policy['area_name']})\n"
            response += f"{policy['policy_description'][:150]}{'...' if len(policy['policy_description']) > 150 else ''}\n\n"
        
        return response.strip()

    def _format_fallback_comparison(self, countries: List[str], data: Dict[str, List]) -> str:
        """Fallback comparison response if AI fails"""
        response = f"**Policy Comparison: {' vs '.join(countries)}**\n\n"
        
        for country, policies in data.items():
            response += f"**{country}:**\n"
            if policies:
                areas = list(set([p['area_name'] for p in policies]))
                response += f"- Policy Areas: {', '.join(areas)}\n"
                response += f"- Total Policies: {len(policies)}\n"
                response += f"- Key Policy: {policies[0]['policy_name']}\n\n"
            else:
                response += "- No policies found\n\n"
        
        return response.strip()

    # Additional methods for conversation management
    async def get_conversation_history(self, conversation_id: str) -> List[ChatMessage]:
        """Get conversation history"""
        try:
            db = await self.get_db()
            conversation_data = await db.get_item('chat_sessions', {'session_id': conversation_id})
            
            if conversation_data:
                messages = []
                for msg_data in conversation_data.get('messages', []):
                    message = ChatMessage(
                        role=msg_data.get('role'),
                        content=msg_data.get('content'),
                        timestamp=datetime.fromisoformat(msg_data.get('timestamp'))
                    )
                    messages.append(message)
                return messages
            
            return []
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def get_user_conversations(self, limit: int = 20, user_id: Optional[str] = None) -> List[Dict]:
        """Get user conversations"""
        try:
            db = await self.get_db()
            sessions = await db.scan_table('chat_sessions')
            
            # Filter by user if specified
            if user_id:
                sessions = [s for s in sessions if s.get('user_id') == user_id]
            
            # Sort by updated_at descending
            sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
            # Limit results
            sessions = sessions[:limit]
            
            # Format for frontend
            conversations = []
            for session in sessions:
                last_message = ""
                messages = session.get('messages', [])
                if messages:
                    last_message = messages[-1].get('content', '')[:100]
                
                conversation = {
                    'conversation_id': session.get('session_id'),
                    'last_message': last_message,
                    'updated_at': session.get('updated_at'),
                    'created_at': session.get('created_at'),
                    'message_count': len(messages)
                }
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            print(f"Error getting user conversations: {e}")
            return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        try:
            db = await self.get_db()
            return await db.delete_item('chat_sessions', {'session_id': conversation_id})
            
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    async def generate_training_data(self) -> List[Dict]:
        """Generate training examples from your policy database for model fine-tuning"""
        await self._update_cache()
        
        training_examples = []
        
        # Generate different types of training examples
        for policy in self.policy_cache[:50]:  # Use top 50 policies for training
            country = policy.get('country', '')
            area = policy.get('area_name', '')
            name = policy.get('policy_name', '')
            description = policy.get('policy_description', '')
            
            if country and area and name and description:
                # Example 1: Direct policy question
                training_examples.append({
                    "messages": [
                        {
                            "role": "system",
                            "content": await self._create_enhanced_system_prompt([policy])
                        },
                        {
                            "role": "user", 
                            "content": f"What {area} policies does {country} have?"
                        },
                        {
                            "role": "assistant",
                            "content": f"In {area}, {country} has implemented '{name}'. {description[:300]}... This policy demonstrates {country}'s approach to {area.lower()} governance, focusing on {policy.get('implementation', 'comprehensive implementation strategies')}."
                        }
                    ]
                })
                
                # Example 2: Policy details question
                training_examples.append({
                    "messages": [
                        {
                            "role": "system",
                            "content": await self._create_enhanced_system_prompt([policy])
                        },
                        {
                            "role": "user",
                            "content": f"Tell me about {name} in {country}"
                        },
                        {
                            "role": "assistant", 
                            "content": f"'{name}' is {country}'s {area} policy that {description[:200]}... The implementation approach involves {policy.get('implementation', 'structured regulatory frameworks')} with evaluation mechanisms focusing on {policy.get('evaluation', 'ongoing assessment and adaptation')}."
                        }
                    ]
                })
        
        # Generate country comparison examples
        for i, country1 in enumerate(self.countries_cache[:5]):
            for country2 in self.countries_cache[i+1:6]:
                policies1 = [p for p in self.policy_cache if p.get('country') == country1][:3]
                policies2 = [p for p in self.policy_cache if p.get('country') == country2][:3]
                
                if policies1 and policies2:
                    training_examples.append({
                        "messages": [
                            {
                                "role": "system",
                                "content": await self._create_enhanced_system_prompt(policies1 + policies2)
                            },
                            {
                                "role": "user",
                                "content": f"Compare policies between {country1} and {country2}"
                            },
                            {
                                "role": "assistant",
                                "content": f"Comparing {country1} and {country2}'s policy approaches reveals distinct strategic differences. {country1} focuses on {policies1[0].get('area_name', 'comprehensive governance')} with policies like '{policies1[0].get('policy_name', '')}', while {country2} emphasizes {policies2[0].get('area_name', 'targeted regulation')} through initiatives such as '{policies2[0].get('policy_name', '')}'. The implementation strategies differ significantly, with {country1} adopting {policies1[0].get('implementation', 'systematic approaches')} versus {country2}'s {policies2[0].get('implementation', 'adaptive frameworks')}."
                            }
                        ]
                    })
        
        return training_examples[:100]  # Return top 100 training examples

    async def export_training_data_for_finetuning(self, output_file: str = "policy_training_data.jsonl"):
        """Export training data in format suitable for OpenAI fine-tuning"""
        training_data = await self.generate_training_data()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in training_data:
                    f.write(json.dumps(example) + '\n')
            
            print(f"Exported {len(training_data)} training examples to {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error exporting training data: {e}")
            return None

    async def search_policies(self, query: str) -> List[Dict]:
        """Search policies"""
        await self._update_cache()
        return await self._find_relevant_policies(query)
    
    async def get_available_data_summary(self) -> Dict[str, Any]:
        """Get summary of available data in the database for debugging/info"""
        await self._update_cache()
        
        # Group policies by country and area
        country_data = {}
        for policy in self.policy_cache:
            country = policy.get('country', 'Unknown')
            area = policy.get('area_name', 'Unknown')
            
            if country not in country_data:
                country_data[country] = {}
            if area not in country_data[country]:
                country_data[country][area] = 0
            country_data[country][area] += 1
        
        return {
            'total_policies': len(self.policy_cache),
            'total_countries': len(self.countries_cache),
            'total_areas': len(self.areas_cache),
            'countries': self.countries_cache,
            'areas': self.areas_cache,
            'country_area_breakdown': country_data
        }
    
    def check_specific_data(self, country: str = None, area: str = None) -> Dict[str, Any]:
        """Check if specific country/area data exists in cache"""
        if not self.policy_cache:
            return {'status': 'cache_empty', 'message': 'Policy cache not loaded'}
        
        matching_policies = []
        
        for policy in self.policy_cache:
            match = True
            policy_country = policy.get('country', '').strip()
            policy_area = policy.get('area_name', '').strip()
            
            if country:
                # Handle common country name variations
                country_matches = (
                    policy_country.lower() == country.lower() or
                    (country.lower() in ["usa", "us", "america", "american"] and policy_country.lower() == "united states") or
                    (country.lower() in ["uk", "britain", "british"] and policy_country.lower() == "united kingdom")
                )
                if not country_matches:
                    match = False
                    
            if area and policy_area.lower() != area.lower():
                match = False
            
            if match:
                matching_policies.append({
                    'country': policy_country,
                    'area': policy_area,
                    'policy_name': policy.get('policy_name'),
                    'has_description': bool(policy.get('policy_description'))
                })
        
        return {
            'query': {'country': country, 'area': area},
            'found': len(matching_policies),
            'policies': matching_policies[:5],  # First 5 for preview
            'total_available': len(matching_policies),
            'all_countries_in_cache': sorted(list(set([p.get('country', '') for p in self.policy_cache if p.get('country')]))),
            'all_areas_in_cache': sorted(list(set([p.get('area_name', '') for p in self.policy_cache if p.get('area_name')])))
        }


# Global instance
enhanced_chatbot_service = EnhancedChatbotService()
