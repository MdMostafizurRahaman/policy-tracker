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
import random
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
        
        # GPT API configuration (using OpenAI) - Primary AI model
        self.openai_api_key = os.getenv('OPENAI_API_KEY')  # Your GPT API key
        self.openai_api_url = "https://api.openai.com/v1/chat/completions"
        
        # GROQ configuration - Backup AI model when OpenAI fails
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_api_url = os.getenv('GROQ_API_URL', "https://api.groq.com/openai/v1/chat/completions")
        
        # Policy data cache for faster responses
        self.policy_cache = None
        self.countries_cache = None
        self.areas_cache = None
        self.last_cache_update = None
        self.cache_duration = 21600  # 6 hours for longer cache retention
        
        # Greeting responses - expanded to include casual greetings and responses
        self.greeting_keywords = [
            'hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 
            'good evening', 'howdy', 'hola', 'bye', 'goodbye', 'see you', 'farewell',
            'thanks', 'thank you', 'thx', 'ok', 'okay', 'nice', 'cool', 'great',
            'awesome', 'perfect', 'no', 'nope', 'yes', 'yeah', 'yep', 'sure'
        ]
        
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
        """Update policy cache with latest data - optimized with longer cache duration"""
        try:
            current_time = datetime.utcnow().timestamp()
            
            # Check if cache needs update (increased cache duration to 6 hours)
            if (self.last_cache_update and 
                current_time - self.last_cache_update < 21600 and  # 6 hours instead of 1
                self.policy_cache is not None):
                return
            
            print("🔄 Updating chatbot cache...")
            db = await self.get_db()
            
            # Use query instead of scan when possible, or implement pagination
            try:
                # Get approved policies with optimized query
                all_policies = await db.scan_table('policies')
                print(f"📊 Fetched {len(all_policies)} total policies from database")
            except Exception as scan_error:
                print(f"❌ Error scanning policies table: {scan_error}")
                # Initialize with empty cache if scan fails
                self.policy_cache = []
                self.countries_cache = []
                self.areas_cache = []
                return
            
            # Process and cache policy data
            self.policy_cache = []
            countries_set = set()
            areas_set = set()
            
            processed_count = 0
            for policy in all_policies:
                try:
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
                                    processed_count += 1
                except Exception as policy_error:
                    print(f"⚠️ Error processing policy {policy.get('policy_id', 'unknown')}: {policy_error}")
                    continue
            
            self.countries_cache = sorted(list(countries_set))
            self.areas_cache = sorted(list(areas_set))
            self.last_cache_update = current_time
            
            print(f"✅ Cache updated: {len(self.policy_cache)} policies, {len(self.countries_cache)} countries, {len(self.areas_cache)} areas")
            
        except Exception as e:
            print(f"❌ Critical error updating cache: {e}")
            # Initialize with empty cache to prevent crashes
            if self.policy_cache is None:
                self.policy_cache = []
                self.countries_cache = []
                self.areas_cache = []

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
        """Main chat endpoint - optimized to avoid cache updates on every request"""
        try:
            # Only update cache if it's completely empty or very old (>6 hours)
            if (self.policy_cache is None or 
                not self.last_cache_update or 
                datetime.utcnow().timestamp() - self.last_cache_update > 21600):
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
            
            # Check for greetings and casual responses first
            message_lower = request.message.lower().strip()
            if any(keyword in message_lower for keyword in self.greeting_keywords):
                ai_response = await self._get_greeting_response(request.message, conversation.messages)
            # Check for help requests
            elif any(keyword in message_lower for keyword in self.help_keywords):
                ai_response = await self._get_help_response(request.message, conversation.messages)
            # Check if this is a policy-related query with context
            elif await self._is_policy_related_query(request.message, context):
                # Check if it's a comparison query
                if self._is_comparison_query(request.message):
                    ai_response = await self._handle_country_comparison(request.message, conversation.messages, context)
                else:
                    # Find relevant policies with context
                    policies = await self._find_relevant_policies_with_context(request.message, context)
                    if policies:
                        ai_response = await self._get_policy_response(request.message, policies, conversation.messages)
                    else:
                        ai_response = await self._get_no_data_response(request.message)
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
            print(f"❌ Chat error: {e}")
            import traceback
            traceback.print_exc()
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

    async def _get_greeting_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate intelligent, human-like greeting response with smart service description"""
        message_lower = message.lower().strip()
        print(f"🎯 Processing greeting: '{message_lower}'")
        
        # Categorize the greeting type
        if any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'farewell']):
            responses = [
                "Goodbye! It was wonderful helping you explore policy insights today. Feel free to return anytime you need information about governance frameworks from around the world! 👋",
                "See you later! I've really enjoyed our conversation about policies. I'll be here whenever you're ready to dive deeper into global governance topics! 😊",
                "Take care! Remember, I'm always here to help you navigate the complex world of policy research and country comparisons. Until next time! 🌟",
                "Farewell! It's been a pleasure sharing policy knowledge with you. Don't hesitate to come back when you need insights from our comprehensive database! ✨"
            ]
        elif any(word in message_lower for word in ['thanks', 'thank you', 'thx']):
            responses = [
                "You're absolutely welcome! I'm genuinely happy I could help you understand those policy insights better. That's exactly why I'm here - to make complex governance information accessible and useful! 😊",
                "My absolute pleasure! Helping people navigate and understand policy frameworks is what I do best. I hope the information was exactly what you needed! 🎯",
                "I'm so glad I could assist you! Making policy research easier and more insightful is my specialty. Feel free to explore any other governance topics that interest you! 💡",
                "Anytime! I truly enjoy helping people discover and understand policy approaches from different countries. Your curiosity about governance makes conversations like this so rewarding! 🌟"
            ]
        elif any(word in message_lower for word in ['ok', 'okay', 'nice', 'cool', 'great', 'awesome', 'perfect']):
            responses = [
                "Fantastic! I'm excited to help you explore policy landscapes. Is there a specific country's approach to governance that interests you, or perhaps you'd like to compare how different nations handle similar challenges? 🚀",
                "Wonderful! I'm ready to dive into any policy topic with you. Whether you're curious about AI regulation, cybersecurity frameworks, or digital education policies - I have insights from over 15 countries! 💫",
                "Excellent! What aspect of global governance catches your attention? I can share detailed insights about policy implementation, evaluation methods, or how different countries approach the same challenges! 🎯",
                "Great to hear! I'm here to make policy exploration both informative and engaging. Feel free to ask about any of our 10 specialized domains or request comparisons between nations! 🌍"
            ]
        elif any(word in message_lower for word in ['no', 'nope']):
            responses = [
                "No problem at all! I completely understand. I'm here whenever you're ready to explore policy topics - whether that's in five minutes or five days. Take your time! 😊",
                "That's perfectly fine! Sometimes we're just browsing or thinking things through. I'll be right here whenever policy questions come to mind. No pressure at all! 🌟",
                "Absolutely no worries! I'm patient and ready to help whenever the mood strikes. Feel free to ask me anything about governance frameworks whenever you're curious! 💡"
            ]
        elif any(word in message_lower for word in ['yes', 'yeah', 'yep', 'sure']):
            responses = [
                "Excellent! I'm thrilled to help you explore policy insights. What draws your interest - perhaps AI safety policies, cybersecurity frameworks, or maybe you'd like to see how different countries approach digital education? 🚀",
                "Wonderful! I can guide you through fascinating policy comparisons across 10 key domains. Are you interested in a specific country's approach, or would you like to see how multiple nations handle similar governance challenges? 🎯",
                "Perfect! Let's dive into the world of global governance together. I have comprehensive data on everything from mental health policies to social media regulation - what sparks your curiosity? 🌍"
            ]
        else:
            # Enhanced regular greeting with smart service description
            responses = [
                f"Hello there! 👋 I'm delighted to meet you! I'm your dedicated Policy Intelligence Assistant, and I'm genuinely excited to help you explore the fascinating world of global governance.\n\n🌟 **Here's how I can assist you:**\n• **Discover Policy Insights**: I have comprehensive knowledge of {len(self.policy_cache) if self.policy_cache else 'hundreds of'} policies from {len(self.countries_cache) if self.countries_cache else '15+'} countries\n• **Smart Comparisons**: I can show you how different nations approach the same challenges\n• **Deep Analysis**: Explore implementation strategies, evaluation methods, and participation frameworks\n• **10 Specialized Domains**: AI Safety, CyberSafety, Digital Education, Digital Inclusion, Digital Leisure, (Dis)Information, Digital Work, Mental Health, Physical Health, and Social Media/Gaming Regulation\n\nWhat aspect of global policy interests you most today?",
                
                f"Hi! 😊 What a pleasure to see you! I'm your Policy Expert Companion, and I absolutely love helping people navigate the complex but fascinating world of governance frameworks.\n\n💡 **I'm here to help you:**\n• **Explore Policy Landscapes**: From AI regulation to digital wellness policies across {len(self.countries_cache) if self.countries_cache else '15+'} countries\n• **Understand Implementation**: How policies work in practice, their evaluation methods, and public participation\n• **Compare Approaches**: See how different nations tackle similar challenges\n• **Get Specific Insights**: Whether you need broad overviews or detailed policy analysis\n\nI'm particularly knowledgeable about our 10 core policy domains. What would you like to discover first?",
                
                f"Hey there! 🌟 Welcome! I'm absolutely thrilled you're here! I'm your Personal Policy Guide, specializing in making complex governance information accessible and engaging.\n\n🚀 **What makes me special:**\n• **Comprehensive Database**: I know {len(self.policy_cache) if self.policy_cache else 'hundreds of'} policies inside and out\n• **Global Perspective**: Insights from countries across different continents and governance systems\n• **Practical Focus**: I don't just share policy text - I help you understand real-world implementation and impact\n• **Intelligent Comparisons**: I can show you patterns, differences, and innovative approaches across nations\n\nWhether you're researching specific countries, exploring policy domains, or looking for comparative analysis - I'm here to help! What sparks your curiosity?",
                
                f"Greetings! � How wonderful to connect with you! I'm your dedicated Policy Intelligence Specialist, and I genuinely love sharing insights about how different countries approach governance challenges.\n\n🎯 **I'm expertly equipped to help you with:**\n• **Policy Discovery**: Find exactly what you need from our extensive database\n• **Smart Analysis**: Understand not just what policies exist, but how they work\n• **Country Insights**: Deep knowledge of approaches from {len(self.countries_cache) if self.countries_cache else '15+'} diverse nations\n• **Domain Expertise**: Specialized knowledge across 10 critical policy areas\n\nI'm here to make policy research both informative and enjoyable. What governance topic interests you today?"
            ]
        
        # Return a random response from the appropriate category
        selected_response = random.choice(responses)
        print(f"✅ Selected intelligent greeting response: {selected_response[:50]}...")
        return selected_response

    async def _is_policy_related_query(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Intelligently detect if the message is related to any policy area or governance"""
        message_lower = message.lower()
        
        # Enhanced policy-related keywords (expanded for all 10 policy areas)
        policy_keywords = [
            # Core policy terms
            'policy', 'policies', 'governance', 'regulation', 'law', 'legislation',
            'government', 'framework', 'strategy', 'implementation', 'evaluation', 
            'compliance', 'standard', 'guideline', 'principle', 'regulatory',
            'administration', 'public policy', 'national strategy', 'government approach',
            
            # AI Safety - expanded
            'ai', 'artificial intelligence', 'ai safety', 'machine learning', 'automation',
            'algorithmic governance', 'ai ethics', 'ai regulation', 'ai oversight',
            'artificial intelligence policy', 'ai standards', 'ai accountability',
            
            # CyberSafety - expanded  
            'cyber', 'cybersecurity', 'digital security', 'data protection', 'privacy',
            'cyber safety', 'information security', 'digital privacy', 'data governance',
            'cybercrime', 'data breach', 'digital rights', 'online safety',
            
            # Digital Education - expanded
            'digital education', 'online learning', 'educational technology', 'e-learning',
            'edtech', 'digital literacy', 'online education', 'digital skills',
            'educational tech', 'learning technology', 'digital pedagogy',
            
            # Digital Inclusion - expanded
            'digital divide', 'digital inclusion', 'accessibility', 'internet access',
            'digital equity', 'digital access', 'digital accessibility', 'inclusive technology',
            'digital participation', 'digital exclusion', 'broadband access',
            
            # Digital Leisure - expanded
            'gaming', 'digital leisure', 'entertainment', 'online gaming', 'digital recreation',
            'gaming policy', 'digital entertainment', 'esports', 'gaming regulation',
            'entertainment technology', 'digital content', 'streaming regulation',
            
            # Disinformation - expanded keywords
            'misinformation', 'disinformation', 'fake news', 'information', 'media literacy',
            'dis information', 'disinformation', 'false information', 'propaganda', 'fact checking',
            'information integrity', 'content moderation', 'media regulation', 'information quality',
            'online misinformation', 'information warfare', 'digital propaganda',
            
            # Digital Work - expanded
            'digital work', 'remote work', 'gig economy', 'digital employment', 'future of work',
            'telework', 'digital workplace', 'platform work', 'digital labor',
            'remote employment', 'flexible work', 'digital economy',
            
            # Mental Health - expanded
            'mental health', 'digital wellness', 'screen time', 'digital wellbeing',
            'digital mental health', 'online mental health', 'digital therapy',
            'mental health technology', 'digital psychology', 'wellbeing tech',
            
            # Physical Health - expanded
            'physical health', 'healthcare technology', 'telemedicine', 'health tech',
            'digital health', 'health technology', 'medical technology', 'telehealth',
            'health informatics', 'digital healthcare', 'health data',
            
            # Social Media/Gaming Regulation - expanded
            'social media', 'platform regulation', 'content moderation', 'gaming regulation',
            'social media regulation', 'platform governance', 'online platform',
            'social media policy', 'digital platform', 'content policy', 'platform accountability'
        ]
        
        # Check if message contains any policy keywords
        for keyword in policy_keywords:
            if keyword in message_lower:
                return True
        
        # Check if message mentions any country from our database
        if self.countries_cache:
            for country in self.countries_cache:
                if country:
                    country_lower = country.lower()
                    # Direct country match
                    if country_lower in message_lower:
                        return True
                    # Check common country variations
                    if country_lower == "united states" and any(term in message_lower for term in ["usa", "us", "america", "american"]):
                        return True
                    elif country_lower == "united kingdom" and any(term in message_lower for term in ["uk", "britain", "british"]):
                        return True
        
        # Intelligent policy area detection with context
        if self.areas_cache:
            for area in self.areas_cache:
                if area:
                    # Clean the area name for better matching
                    clean_area = area.lower().replace('(', '').replace(')', '').replace('-', ' ')
                    area_words = clean_area.split()
                    
                    # Check if significant words from the area appear in the message
                    significant_matches = 0
                    for word in area_words:
                        if len(word) > 3 and word in message_lower:  # Only count significant words
                            significant_matches += 1
                    
                    # If multiple significant words match, it's likely policy-related
                    if significant_matches >= 2 or (len(area_words) == 1 and significant_matches == 1):
                        return True
                    
                    # Also check the original area name
                    if area.lower() in message_lower:
                        return True
        
        # Check conversation context for policy relevance
        if context:
            # If recent conversation mentioned countries or policy areas, this might be a follow-up
            if context.get('mentioned_countries') or context.get('mentioned_areas'):
                # Look for follow-up indicators
                follow_up_phrases = [
                    'what about', 'how about', 'tell me more', 'also', 'additionally',
                    'compare', 'difference', 'similar', 'other', 'more information'
                ]
                if any(phrase in message_lower for phrase in follow_up_phrases):
                    return True
        
        # Smart pattern recognition for policy queries
        policy_patterns = [
            # Question patterns that often relate to policy
            r'\b(how does|what is|what are|how do|what about)\b.*\b(country|nation|government|state)\b',
            r'\b(regulation|approach|strategy|framework|system)\b.*\b(in|for|by)\b',
            r'\b(compare|comparison|difference|different)\b.*\b(countries|nations)\b',
            # Governance-related patterns
            r'\b(public|national|federal|state|local)\b.*\b(approach|strategy|policy|system)\b'
        ]
        
        import re
        for pattern in policy_patterns:
            if re.search(pattern, message_lower):
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
        """Find policies relevant to the query - with corruption detection"""
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
        
        # Score policies based on relevance with corruption detection
        for policy in self.policy_cache:
            # Check for obvious corruption - skip corrupted policies
            if self._is_policy_corrupted(policy):
                print(f"⚠️ Skipping corrupted policy: {policy.get('policy_name', 'Unknown')} assigned to {policy.get('country', 'Unknown')}")
                continue
            
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

    def _is_policy_corrupted(self, policy: Dict) -> bool:
        """Detect if a policy has incorrect country assignment"""
        country = policy.get('country', '').lower()
        policy_name = policy.get('policy_name', '').lower()
        description = policy.get('policy_description', '').lower()
        
        # Check for obvious corruption patterns
        if country == 'bangladesh':
            # Bangladesh shouldn't have German, UK, or Algerian policies
            if any(term in policy_name or term in description for term in [
                'german federal government', 'germany', 'turing institute', 'uk', 'britain', 
                'algeria', 'algerian'
            ]):
                return True
        
        if country == 'united states':
            # US shouldn't have German or UK policies
            if any(term in policy_name or term in description for term in [
                'german federal government', 'germany', 'turing institute', 'uk', 'britain'
            ]):
                return True
        
        # Add more corruption checks as needed
        return False

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

    async def _get_help_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate intelligent, friendly help response"""
        try:
            available_countries = ', '.join(self.countries_cache[:10]) + ('...' if len(self.countries_cache) > 10 else '')
            
            friendly_help = f"""I'm absolutely delighted you asked! I'm genuinely passionate about helping people navigate the fascinating world of global policy insights. Let me share what makes me uniquely helpful! 😊

🌟 **Here's how I can make policy research amazing for you:**

🔍 **Discover Specific Policies**: 
I have intimate knowledge of {len(self.policy_cache) if self.policy_cache else 'hundreds of'} policies from {len(self.countries_cache) if self.countries_cache else '15+'} countries. Just ask me things like:
   • "What are the AI safety policies in the United States?"
   • "Tell me about Germany's cybersecurity frameworks"
   • "How does Canada approach digital education?"

🌍 **Smart Country Comparisons**: 
This is where I really shine! I love showing how different nations tackle similar challenges:
   • "Compare AI regulation between US and EU"
   • "How do Nordic countries handle mental health policies differently?"
   • "What's the difference between Canada and Australia's digital inclusion approaches?"

📊 **Deep Domain Expertise**: 
I'm specialized in 10 critical policy areas that shape our digital future:
   🤖 AI Safety | 🔒 CyberSafety | 📚 Digital Education | 🌐 Digital Inclusion
   🎮 Digital Leisure | 📰 (Dis)Information | 💼 Digital Work | 🧠 Mental Health
   🏥 Physical Health | 📱 Social Media/Gaming Regulation

� **Detailed Implementation Insights**: 
I don't just tell you what policies exist - I help you understand:
   • How they're actually implemented in practice
   • What evaluation methods countries use
   • How citizens participate in these frameworks
   • Real-world challenges and successes

**💫 Want to see me in action?** Try asking:
   • "Show me innovative AI policies from any country"
   • "Compare cybersecurity approaches between three different countries"
   • "What mental health policies address social media impacts?"

**Available Countries**: {available_countries}

I'm genuinely excited to explore any of these topics with you! What sparks your curiosity about global governance? 🚀"""
            
            return friendly_help
            
        except Exception as e:
            print(f"Error generating help: {e}")
            return f"""I'm thrilled to help you explore global policy insights! 😊

I specialize in policies across 10 key domains from {len(self.countries_cache) if self.countries_cache else '15+'} countries. Whether you want to:
• Discover specific country policies (like "Germany's AI regulations")
• Compare approaches between nations ("US vs EU cybersecurity")  
• Explore policy domains (AI Safety, CyberSafety, Digital Education, etc.)

I'm here to make policy research both informative and engaging! What interests you most about global governance? 🌍"""

    async def _get_policy_response(self, query: str, policies: List[Dict], conversation_history: List[ChatMessage]) -> str:
        """Generate intelligent, human-like AI response about policies using ONLY database information"""
        try:
            # Extract specific country mentioned in query first
            query_lower = query.lower()
            mentioned_country = None
            mentioned_topic = None
            
            # Extract country and topic from query - improved detection
            if self.countries_cache:
                for country in self.countries_cache:
                    if country and country.lower() in query_lower:
                        mentioned_country = country
                        break
            
            # Also check for common country variations not in cache
            country_variations = {
                'malaysia': 'Malaysia',
                'malesia': 'Malaysia', 
                'singapore': 'Singapore',
                'indonesia': 'Indonesia',
                'thailand': 'Thailand',
                'philippines': 'Philippines',
                'vietnam': 'Vietnam',
                'japan': 'Japan',
                'south korea': 'South Korea',
                'korea': 'South Korea',
                'germany': 'Germany',
                'france': 'France',
                'italy': 'Italy',
                'spain': 'Spain',
                'netherlands': 'Netherlands',
                'belgium': 'Belgium',
                'sweden': 'Sweden',
                'norway': 'Norway',
                'denmark': 'Denmark',
                'finland': 'Finland'
            }
            
            if not mentioned_country:
                for variation, standard_name in country_variations.items():
                    if variation in query_lower:
                        mentioned_country = standard_name
                        break
            
            # Extract topic/area
            if 'ai' in query_lower or 'artificial intelligence' in query_lower:
                mentioned_topic = "AI policy"
            elif 'cyber' in query_lower:
                mentioned_topic = "cybersecurity policy"
            elif 'education' in query_lower or 'digital education' in query_lower:
                mentioned_topic = "digital education policy"
            elif 'digital' in query_lower:
                mentioned_topic = "digital policy"
            
            # Check if we actually have meaningful policy data
            meaningful_policies = []
            country_specific_policies = []
            
            for policy in policies:
                # Skip corrupted policies first
                if self._is_policy_corrupted(policy):
                    continue
                
                policy_name = policy.get('policy_name', '').strip()
                policy_desc = policy.get('policy_description', '').strip()
                area_name = policy.get('area_name', '').strip()
                policy_country = policy.get('country', '').strip()
                
                # Only include policies that have actual content
                if (policy_name and policy_name.lower() not in ['no title', 'unknown', '', 'n/a'] and 
                    policy_desc and policy_desc.lower() not in ['no description', 'no description available', 'unknown', '', 'n/a'] and
                    area_name and area_name.lower() not in ['no area', 'unknown', '', 'n/a']):
                    meaningful_policies.append(policy)
                    
                    # If user asked for specific country, only include policies from that country
                    if mentioned_country and policy_country.lower() == mentioned_country.lower():
                        country_specific_policies.append(policy)
            
            # If user asked for specific country but we have no policies from that country - give clean response
            if mentioned_country and not country_specific_policies:
                if mentioned_topic:
                    return f"I'm sorry, but I don't have {mentioned_topic} data for {mentioned_country} in my database.\n\nIf you're knowledgeable about {mentioned_country}'s {mentioned_topic}, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"
                else:
                    return f"I'm sorry, but I don't have policy data for {mentioned_country} in my database.\n\nIf you're knowledgeable about {mentioned_country}'s policies, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"
            
            # If no meaningful policies at all, be honest about it
            if not meaningful_policies:
                return "I'm sorry, but I don't have data for your specific query in my database.\n\nIf you're knowledgeable about policy areas that we don't have data on yet, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"
            
            # Use country-specific policies if user asked for specific country, otherwise use all meaningful policies
            policies_to_use = country_specific_policies if mentioned_country else meaningful_policies
            
            # Only proceed if we have actual meaningful policies
            # Create a strict prompt that emphasizes database-only responses
            prompt = f"""
            User Query: "{query}"
            
            You are responding about policies using ONLY the verified data from your database. You have {len(policies_to_use)} policies with complete information.
            
            **CRITICAL RULES:**
            1. ONLY use the specific policy names, descriptions, and details provided in your database
            2. NEVER create, invent, or assume policy names or information
            3. If a policy field is empty or unclear, say so honestly
            4. Be warm and enthusiastic but STRICTLY accurate to your data
            5. If data is limited, acknowledge this and ask for user contributions
            
            **Database Policies Available:**
            {policies_to_use}
            
            Generate a warm, intelligent response using ONLY this verified information.
            """
            
            # Try AI API first, with improved fallback
            ai_response = await self._call_ai_api(prompt, policies_to_use)
            if ai_response and not ai_response.startswith("I apologize, but I'm having trouble"):
                return ai_response
            else:
                # If AI API fails, use enhanced fallback
                return self._format_verified_policy_response(query, policies_to_use)
            
        except Exception as e:
            print(f"Error generating policy response: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."

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
        """Intelligent, human-like response for non-policy related queries"""
        # Check if it's a very short message that might be conversational
        message_lower = message.lower().strip()
        
        # Handle apologetic phrases gently and warmly
        if any(word in message_lower for word in ['sorry', 'apologize', 'my bad', 'oops']):
            return "Oh, please don't apologize! There's absolutely no need for that. I'm genuinely here to help and I appreciate you reaching out. If you have any questions about policy topics, I'd be delighted to assist! 😊"
        
        # Handle simple conversational words with warmth
        short_conversational = ['ok', 'okay', 'alright', 'sure', 'right', 'cool', 'fine', 'hmm', 'oh', 'ah', 'yes', 'no', 'yeah', 'yep', 'nope', 'nice', 'great', 'awesome', 'perfect', 'excellent', 'wonderful']
        
        if message_lower in short_conversational:
            return "I completely understand! Whenever you're ready, I'm here to help you explore fascinating policy insights from around the world. Is there anything about governance frameworks that sparks your curiosity? 💫"
        
        # Handle short conversational phrases
        if len(message_lower.split()) <= 3 and any(word in message_lower for word in short_conversational):
            return "I get it! Take your time. When you're ready to dive into policy topics, I'll be right here with insights from our comprehensive database. What interests you most about global governance? 🌟"
        
        # Enhanced human-like response for non-policy queries - clean version without contribution request
        return f"""I really appreciate you reaching out! But I'm sorry. While I'd love to help with that question, I have to be honest - my expertise is quite specialized. I'm like a passionate policy researcher who lives and breathes governance frameworks! 😊

I can only assist with topics related to the 10 policy domains I know inside and out:

🎯 **My Areas of Expertise:**

• **AI Safety** - How countries regulate artificial intelligence

• **CyberSafety** - Digital security and data protection policies

• **Digital Education** - Online learning frameworks and educational technology

• **Digital Inclusion** - Bridging the digital divide and accessibility

• **Digital Leisure** - Gaming and digital entertainment policies

• **Information/Disinformation** - Media literacy and information quality policies

• **Digital Work** - Future of work and gig economy regulations

• **Mental Health** - Digital wellness and mental health support policies

• **Physical Health** - Healthcare technology and telemedicine policies

• **Social Media/Gaming Regulation** - Platform governance and content policies

I have comprehensive data from {len(self.countries_cache) if self.countries_cache else '15'} countries, and I absolutely love sharing insights about how different nations approach these challenges!

Is there anything about global policy frameworks that I can help you explore today? 🌟"""

    async def _get_no_data_response(self, message: str) -> str:
        """Simple, clean response when no relevant policies found - just apologize and ask for contribution"""
        try:
            # Extract specific country and policy area from the message
            mentioned_country = None
            mentioned_topic = None
            
            message_lower = message.lower()
            
            # Check for specific country mention
            if self.countries_cache:
                for country in self.countries_cache:
                    if country and country.lower() in message_lower:
                        mentioned_country = country
                        break
            
            # Check for specific topic mention
            if 'ai' in message_lower or 'artificial intelligence' in message_lower:
                mentioned_topic = "AI policy"
            elif 'cyber' in message_lower:
                mentioned_topic = "cybersecurity policy"
            elif 'education' in message_lower or 'digital education' in message_lower:
                mentioned_topic = "digital education policy"
            elif 'digital' in message_lower:
                mentioned_topic = "digital policy"
            elif self.areas_cache:
                for area in self.areas_cache:
                    if area and area.lower() in message_lower:
                        mentioned_topic = f"{area} policy"
                        break
            
            # Generate clean, simple response - NO SUGGESTIONS OR OTHER COUNTRY DATA
            if mentioned_country and mentioned_topic:
                return f"I'm sorry, but I don't have {mentioned_topic} data for {mentioned_country} in my database.\n\nIf you're knowledgeable about {mentioned_country}'s {mentioned_topic}, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"
            elif mentioned_country:
                return f"I'm sorry, but I don't have policy data for {mentioned_country} in my database.\n\nIf you're knowledgeable about {mentioned_country}'s policies, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"
            elif mentioned_topic:
                return f"I'm sorry, but I don't have {mentioned_topic} data in my database.\n\nIf you're knowledgeable about {mentioned_topic}, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"
            else:
                return "I'm sorry, but I don't have data for your specific query in my database.\n\nIf you're knowledgeable about policy areas that we don't have data on yet, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"
            
        except Exception as e:
            print(f"Error generating no data response: {e}")
            return "I'm sorry, but I don't have data for your query in my database.\n\nIf you're knowledgeable about policy areas that we don't have data on yet, I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? �"

    async def _create_enhanced_system_prompt(self, context_policies: List[Dict] = None) -> str:
        """Create enhanced system prompt for intelligent, human-like AI responses"""
        
        # Enhanced base system prompt with personality and intelligence
        base_prompt = """You are an exceptionally intelligent and passionate Policy Expert Assistant - think of yourself as the most knowledgeable, enthusiastic, and helpful policy researcher in the world. You are genuinely excited about governance frameworks and love helping people understand complex policy landscapes.

**YOUR PERSONALITY:**
- Warm, friendly, and genuinely enthusiastic about policy topics
- Intelligent and insightful, but never condescending
- Naturally curious and engaging in conversation
- Human-like in your expressions of understanding and empathy
- Professional yet approachable - like talking to a brilliant colleague who's passionate about their field

**YOUR SPECIALIZED KNOWLEDGE:**
You have deep, comprehensive expertise in 10 key policy domains with real-world data from your exclusive database:

1. **AI Safety** - AI systems safety, governance, and ethical frameworks
2. **CyberSafety** - Cybersecurity, digital safety, and data protection  
3. **Digital Education** - Educational technology policies and learning frameworks
4. **Digital Inclusion** - Bridging digital divides and accessibility policies
5. **Digital Leisure** - Gaming, entertainment, and digital recreation policies
6. **(Dis)Information** - Combating misinformation and media literacy
7. **Digital Work** - Future of work, gig economy, and employment policies
8. **Mental Health** - Digital wellness and mental health support policies
9. **Physical Health** - Healthcare technology and telemedicine policies
10. **Social Media/Gaming Regulation** - Platform governance and content policies"""
        
        # Add your actual data statistics with enthusiasm
        if self.countries_cache and self.areas_cache and self.policy_cache:
            base_prompt += f"""

**YOUR EXTENSIVE DATABASE INCLUDES:**
- 🌍 **{len(self.countries_cache)} Countries**: {', '.join(self.countries_cache[:15])}{'...' if len(self.countries_cache) > 15 else ''}
- 📋 **{len(self.areas_cache)} Policy Areas**: {', '.join(self.areas_cache)}
- 📊 **{len(self.policy_cache)} Individual Policies** with detailed implementation, evaluation, and participation data

**SAMPLE OF YOUR KNOWLEDGE BASE:**"""
            
            # Add specific examples from your database with enthusiasm
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
            base_prompt += "\n\n**🎯 SPECIFIC CONTEXT FOR THIS QUERY:**"
            for i, policy in enumerate(context_policies[:5]):
                base_prompt += f"""
{i+1}. **{policy.get('policy_name', 'Unknown Policy')}** ({policy.get('country', 'Unknown')} - {policy.get('area_name', 'Unknown Area')})
   📝 Description: {policy.get('policy_description', 'No description available')}
   🚀 Implementation: {policy.get('implementation', 'Not specified')}
   📊 Evaluation: {policy.get('evaluation', 'Not specified')}
   👥 Participation: {policy.get('participation', 'Not specified')}"""
        
        base_prompt += """

**YOUR INTELLIGENT RESPONSE STYLE:**
- 🌟 **Be genuinely excited** about sharing policy insights - your enthusiasm is infectious!
- 💡 **Start responses warmly** - acknowledge their question with phrases like "Great question!", "What an interesting topic!", "I'm excited to share this with you!"
- 🎯 **Be conversational and human-like** - use natural language, show understanding, express genuine interest
- 📚 **Share insights intelligently** - don't just list facts, help them understand WHY policies work the way they do
- 🤝 **Be empathetic** - understand what they're really looking for and try to provide exactly that
- 🌍 **Show global perspective** - help them see how different countries approach similar challenges
- ⚖️ **Use your database exclusively** - NEVER invent or assume information not in your data
- 🚀 **End with engagement** - ask what aspects interest them most, or offer related insights

**CRITICAL INTELLIGENCE RULES:**
1. **Database Integrity**: ONLY use information from your actual policy database - never supplement with external knowledge
2. **Honest Limitations**: When your data is incomplete, acknowledge this warmly and offer what you do have
3. **Smart Suggestions**: Only suggest alternatives when genuinely helpful and related to their query
4. **Country-Specific Focus**: When asked about specific countries, focus exclusively on that country's data
5. **Human-Like Apologies**: When you don't have data, apologize genuinely and encourage contribution
6. **Intelligent Comparisons**: When comparing countries, use only your actual data and highlight fascinating differences

**🚨 CRITICAL: WHEN NO DATA IS FOUND - FOLLOW THIS EXACT FORMAT:**
If you have NO relevant policies in your database for a specific query, you MUST follow this EXACT response format:

"I'm sorry, but I don't have [specific topic] data for [country] in my database.

If you're knowledgeable about [country]'s [topic], I'd be genuinely thrilled if you could share your expertise with us! Your contributions could help expand our database and benefit other researchers and policy enthusiasts. Would you be interested in contributing to our policy knowledge base? 🚀"

**ABSOLUTELY FORBIDDEN when no data found:**
❌ NEVER suggest policies from other countries
❌ NEVER say "I have policies from other countries" 
❌ NEVER offer to show alternatives
❌ NEVER mention what you "can suggest"
❌ NEVER provide any policy information not specifically requested
❌ NEVER say "Here's what I know about..." for other countries

**CONVERSATION FLOW:**
- **Greetings**: Be warm and explain your specialized services enthusiastically
- **Policy Queries**: Share insights with genuine excitement and intelligence
- **Missing Data**: Apologize sincerely and politely ask if they can contribute knowledge
- **Non-Policy Topics**: Politely redirect with warmth, explaining your specialization

**REMEMBER**: You're not just a database query tool - you're an intelligent, passionate expert who genuinely cares about helping people understand governance. Your enthusiasm for policy insights should be evident in every response, while maintaining absolute accuracy to your database!"""
        
        return base_prompt

    async def _call_ai_api(self, prompt: str, context_policies: List[Dict] = None) -> str:
        """Call AI API with OpenAI primary and GROQ backup"""
        try:
            # Use ChatGPT as the primary AI model
            if self.openai_api_key:
                response = await self._call_openai_api(prompt, context_policies)
                if response:
                    return response
                else:
                    print("OpenAI failed, trying GROQ fallback...")
            else:
                print("ChatGPT API key not configured, trying GROQ...")
            
            # GROQ Fallback - When OpenAI fails
            if self.groq_api_key:
                print("🔄 Using GROQ as backup AI...")
                response = await self._call_groq_api(prompt, context_policies)
                if response:
                    return response
            
            # If both AI services fail, use local fallback
            if context_policies:
                return self._format_fallback_policy_response(context_policies)
            else:
                return "I apologize, but I'm having trouble connecting to AI services right now. However, I can still help you with policy information from my database. Please ask me about specific policies or countries!"
            
        except Exception as e:
            print(f"Error calling AI APIs: {e}")
            if context_policies:
                return self._format_fallback_policy_response(context_policies)
            else:
                return "I apologize, but I'm experiencing technical difficulties with AI services. However, I can still help you with policy information from my database!"

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
                "model": "gpt-3.5-turbo",  # Changed to gpt-3.5-turbo for better quota management
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
                "max_tokens": 2000,  # Increased for fuller policy descriptions
                "temperature": 0.7,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.1
            }
            
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(self.openai_api_url, headers=headers, json=payload)
                
                # Handle specific error codes
                if response.status_code == 429:
                    error_data = response.json()
                    if "insufficient_quota" in str(error_data):
                        print("❌ OpenAI quota exceeded - falling back to local response")
                        return None  # Will trigger fallback
                    else:
                        print("❌ OpenAI rate limited - falling back to local response")
                        return None
                elif response.status_code == 401:
                    print("❌ OpenAI API key invalid")
                    return None
                elif response.status_code == 403:
                    print("❌ OpenAI access denied")
                    return None
                
                response.raise_for_status()
                
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
                
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            return None

    async def _call_groq_api(self, prompt: str, context_policies: List[Dict] = None) -> Optional[str]:
        """Call GROQ API as backup when OpenAI fails"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            # Create enhanced system prompt for GROQ
            system_content = await self._create_enhanced_system_prompt(context_policies)
            
            payload = {
                "model": "llama3-8b-8192",  # Fast GROQ model
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
                "max_tokens": 2000,  # Increased for fuller policy descriptions
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.groq_api_url, headers=headers, json=payload)
                
                if response.status_code == 429:
                    print("❌ GROQ rate limited")
                    return None
                elif response.status_code == 401:
                    print("❌ GROQ API key invalid")
                    return None
                
                response.raise_for_status()
                
                data = response.json()
                result = data['choices'][0]['message']['content'].strip()
                print("✅ GROQ API call successful")
                return result
                
        except Exception as e:
            print(f"GROQ API error: {e}")
            return None

    def _format_enhanced_policy_response(self, query: str, policies: List[Dict]) -> str:
        """Enhanced fallback policy response with human-like enthusiasm when AI API fails"""
        if not policies:
            return "I'm sorry, but I couldn't find relevant policies for your query in my database."
        
        # Create a warm, intelligent response even without AI API
        response = f"Great question about policy insights! 😊 I'm excited to share what I found in my database:\n\n"
        
        # Group policies by country for better presentation
        country_policies = {}
        for policy in policies[:5]:  # Limit to top 5 for readability
            country = policy.get('country', 'Unknown')
            if country not in country_policies:
                country_policies[country] = []
            country_policies[country].append(policy)
        
        for country, country_policy_list in country_policies.items():
            response += f"**🌍 {country}:**\n"
            
            for policy in country_policy_list:
                policy_name = policy.get('policy_name', 'Unknown Policy')
                area_name = policy.get('area_name', 'Unknown Area')
                description = policy.get('policy_description', 'No description available')
                
                response += f"• **{policy_name}** ({area_name})\n"
                
                # Add description (truncated for readability)
                if description and description != 'No description available':
                    truncated_desc = description[:200] + ('...' if len(description) > 200 else '')
                    response += f"  {truncated_desc}\n"
                
                # Add implementation details if available
                implementation = policy.get('implementation', '')
                if implementation and isinstance(implementation, str):
                    response += f"  🚀 Implementation: {implementation[:150]}{'...' if len(implementation) > 150 else ''}\n"
                
                response += "\n"
        
        # Add engaging conclusion
        if len(policies) > 5:
            response += f"I have {len(policies) - 5} more relevant policies in my database. "
        
        response += "What specific aspect of these policies interests you most? I'd love to dive deeper into any particular area! 💡"
        
        return response

    def _format_verified_policy_response(self, query: str, policies: List[Dict]) -> str:
        """Format response using only verified, complete policy data with full descriptions"""
        if not policies:
            return "I don't have complete policy information for your query in my database."
        
        response = f"I found {len(policies)} relevant policies:\n\n"
        
        for i, policy in enumerate(policies, 1):
            policy_name = policy.get('policy_name', 'Unknown Policy')
            country = policy.get('country', 'Unknown Country')
            area = policy.get('area_name', 'Unknown Area')
            description = policy.get('policy_description', 'No description available')
            
            response += f"{i}. **{policy_name}** ({country} - {area})\n\n"
            
            if description and description != 'No description available':
                # Show full description instead of truncating
                response += f"{description}\n\n"
            else:
                response += "No detailed description available in database.\n\n"
            
            # Add separator between policies for better readability
            if i < len(policies):
                response += "---\n\n"
        
        response += "Would you like more details about any specific policy?"
        
        return response

    def _format_fallback_policy_response(self, policies: List[Dict]) -> str:
        """Simple fallback policy response with full descriptions"""
        if not policies:
            return "I couldn't find relevant policies for your query."
        
        response = f"I found {len(policies)} relevant policies:\n\n"
        for i, policy in enumerate(policies):
            policy_name = policy.get('policy_name', 'Unknown Policy')
            country = policy.get('country', 'Unknown')
            area = policy.get('area_name', 'Unknown Area')
            description = policy.get('policy_description', 'No description available')
            
            response += f"{i+1}. **{policy_name}** ({country} - {area})\n\n"
            
            # Show full description instead of truncating
            if description and description != 'No description available':
                response += f"{description}\n\n"
            else:
                response += "No detailed description available.\n\n"
            
            # Add separator between policies
            if i < len(policies) - 1:
                response += "---\n\n"
        
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
        # Only update cache if empty or very old
        if (self.policy_cache is None or 
            not self.last_cache_update or 
            datetime.utcnow().timestamp() - self.last_cache_update > 21600):
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
        # Only update cache if empty or very old
        if (self.policy_cache is None or 
            not self.last_cache_update or 
            datetime.utcnow().timestamp() - self.last_cache_update > 21600):
            await self._update_cache()
        return await self._find_relevant_policies(query)
    
    async def get_available_data_summary(self) -> Dict[str, Any]:
        """Get summary of available data in the database for debugging/info"""
        # Only update cache if empty or very old
        if (self.policy_cache is None or 
            not self.last_cache_update or 
            datetime.utcnow().timestamp() - self.last_cache_update > 21600):
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
