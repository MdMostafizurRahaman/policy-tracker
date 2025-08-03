"""
Enhanced Chatbot Service with GPT API for human-like responses
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
        
        # GPT API configuration (using OpenAI)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')  # Your GPT API key
        self.openai_api_url = "https://api.openai.com/v1/chat/completions"
        
        # Backup GROQ configuration
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_api_url = os.getenv('GROQ_API_URL', "https://api.groq.com/openai/v1/chat/completions")
        
        # Policy data cache for faster responses
        self.policy_cache = None
        self.countries_cache = None
        self.areas_cache = None
        self.last_cache_update = None
        self.cache_duration = 3600  # 1 hour
        
        # Registration and submission links
        self.registration_url = os.getenv('FRONTEND_URL', 'http://localhost:3000') + '/register'
        self.submission_url = os.getenv('FRONTEND_URL', 'http://localhost:3000') + '/submit-policy'
        
        # Greeting responses
        self.greeting_keywords = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy', 'hola']
        
        # Help keywords
        self.help_keywords = ['help', 'what can you do', 'assist', 'guide', 'support', 'how to use']
        
        # Country comparison keywords
        self.comparison_keywords = ['compare', 'difference', 'vs', 'versus', 'between', 'different', 'contrast']
        
        # Out of scope topics (non-policy related)
        self.non_policy_topics = [
            'weather', 'sports', 'entertainment', 'movies', 'music', 'food', 'recipes',
            'gaming', 'fashion', 'travel', 'jokes', 'memes', 'dating', 'relationships',
            'stocks', 'cryptocurrency', 'bitcoin', 'shopping', 'technology news',
            'programming', 'coding', 'software development', 'math', 'physics',
            'chemistry', 'biology', 'medicine', 'health tips', 'fitness', 'exercise',
            'color', 'colors', 'rainbow', 'art', 'painting', 'drawing', 'science facts',
            'general knowledge', 'trivia', 'history', 'geography', 'animals', 'plants',
            'space', 'astronomy', 'literature', 'books', 'cooking', 'recipes'
        ]

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

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Main chat endpoint"""
        try:
            # Update cache first
            await self._update_cache()
            
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                request.conversation_id, 
                request.user_id
            )
            
            # Create user message
            user_message = ChatMessage(
                role="user",
                content=request.message,
                timestamp=datetime.utcnow()
            )
            
            # Generate AI response
            ai_response = await self._generate_ai_response(
                request.message, 
                conversation.messages
            )
            
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
        """Check if the message is related to AI policy or governance"""
        message_lower = message.lower()
        
        # Policy-related keywords
        policy_keywords = [
            'policy', 'policies', 'governance', 'regulation', 'law', 'legislation',
            'government', 'ai', 'artificial intelligence', 'digital', 'technology',
            'ethics', 'safety', 'framework', 'strategy', 'implementation',
            'evaluation', 'compliance', 'standard', 'guideline', 'principle'
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

    async def _generate_ai_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate AI response based on message and context"""
        # Ensure message is a string
        if not isinstance(message, str):
            message = str(message)
            
        message_lower = message.lower().strip()
        
        # Check for greetings
        if any(keyword in message_lower for keyword in self.greeting_keywords):
            return await self._get_ai_greeting_response(message, conversation_history)
        
        # Check for help requests
        if any(keyword in message_lower for keyword in self.help_keywords):
            return await self._get_ai_help_response(message, conversation_history)
        
        # Check for explicit non-policy topics first
        if any(topic in message_lower for topic in self.non_policy_topics):
            return await self._get_non_policy_response(message)
        
        # Check if the query is actually policy-related
        if not await self._is_policy_related_query(message):
            return await self._get_non_policy_response(message)
        
        # Check for country comparison requests
        if any(keyword in message_lower for keyword in self.comparison_keywords):
            return await self._handle_country_comparison(message)
        if any(keyword in message_lower for keyword in self.comparison_keywords):
            return await self._handle_country_comparison(message)
        
        # Search for relevant policies
        relevant_policies = await self._find_relevant_policies(message)
        
        if relevant_policies:
            return await self._get_ai_policy_response(message, relevant_policies, conversation_history)
        else:
            # No relevant policies found - suggest submission
            return await self._get_no_data_response(message)

    async def _find_relevant_policies(self, query: str) -> List[Dict]:
        """Find policies relevant to the query"""
        if not self.policy_cache:
            return []
        
        query_lower = query.lower()
        relevant_policies = []
        
        # Score policies based on relevance
        for policy in self.policy_cache:
            score = 0
            
            # Check country match
            if policy.get('country') and policy['country'].lower() in query_lower:
                score += 10
            
            # Check area match
            if policy.get('area_name') and policy['area_name'].lower() in query_lower:
                score += 8
            
            # Check policy name match
            if policy.get('policy_name') and policy['policy_name'].lower() in query_lower:
                score += 15
            
            # Check description match
            if policy.get('policy_description'):
                description_words = policy['policy_description'].lower().split()
                query_words = query_lower.split()
                common_words = set(description_words) & set(query_words)
                score += len(common_words) * 2
            
            # Check implementation, evaluation, participation
            for field in ['implementation', 'evaluation', 'participation']:
                field_value = policy.get(field)
                if field_value and isinstance(field_value, str) and any(word in field_value.lower() for word in query_words):
                    score += 3
            
            if score > 0:
                policy['relevance_score'] = score
                relevant_policies.append(policy)
        
        # Sort by relevance and return top results
        relevant_policies.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_policies[:10]  # Return top 10 relevant policies

    async def _get_ai_greeting_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate AI greeting response with your policy data context"""
        try:
            # Get sample policies for context
            sample_policies = self.policy_cache[:5] if self.policy_cache else []
            
            prompt = f"""
            A user just greeted you with: "{message}"
            
            Respond as a world-class policy expert who has deep knowledge of the policies in your database.
            Reference specific countries and policy areas you know about.
            Make it warm, professional, and show your expertise.
            
            Keep it conversational and under 3 sentences.
            """
            
            return await self._call_ai_api(prompt, sample_policies)
            
        except Exception as e:
            print(f"Error generating greeting: {e}")
            return "Hello! I'm your AI Policy Expert Assistant with deep knowledge of AI policies from around the world. I can help you explore policies, compare different countries' approaches, and provide detailed insights. What would you like to know?"

    async def _get_ai_help_response(self, message: str, conversation_history: List[ChatMessage]) -> str:
        """Generate AI help response"""
        try:
            available_countries = ', '.join(self.countries_cache[:10]) + ('...' if len(self.countries_cache) > 10 else '')
            available_areas = ', '.join(self.areas_cache[:8]) + ('...' if len(self.areas_cache) > 8 else '')
            
            prompt = f"""
            You are a helpful AI Policy Expert Assistant. A user is asking for help: "{message}"
            
            Explain what you can help with in a friendly, conversational way:
            
            Available data:
            - Countries: {available_countries}
            - Policy Areas: {available_areas}
            - Total policies: {len(self.policy_cache)}
            
            You can help with:
            1. Finding policies by country or area
            2. Comparing policies between countries
            3. Explaining specific policy details
            4. Searching policy descriptions
            
            Give 2-3 example questions they could ask. Keep it friendly and under 4 sentences.
            """
            
            return await self._call_ai_api(prompt)
            
        except Exception as e:
            print(f"Error generating help: {e}")
            return f"I can help you explore AI policies from {len(self.countries_cache)} countries and {len(self.areas_cache)} policy areas. Try asking me about specific countries like '{self.countries_cache[0] if self.countries_cache else 'United States'}', policy areas like '{self.areas_cache[0] if self.areas_cache else 'AI Safety'}', or compare policies between countries. What would you like to explore?"

    async def _get_ai_policy_response(self, query: str, policies: List[Dict], conversation_history: List[ChatMessage]) -> str:
        """Generate AI response about policies using your data for training context"""
        try:
            prompt = f"""
            User Query: "{query}"
            
            Based on your extensive knowledge and the specific policies in your database, provide an expert analysis.
            Draw upon your training on these policies to give detailed, nuanced insights.
            
            Focus on:
            1. Directly answering the user's question with specific policy details
            2. Comparing different approaches where relevant
            3. Explaining implementation nuances you've learned
            4. Providing expert context about effectiveness and challenges
            5. Sound like a policy expert who has personally studied each policy
            
            Be conversational but authoritative. Use specific examples and comparisons.
            """
            
            return await self._call_ai_api(prompt, policies)
            
        except Exception as e:
            print(f"Error generating policy response: {e}")
            return self._format_fallback_policy_response(policies)

    async def _handle_country_comparison(self, message: str) -> str:
        """Handle country comparison requests"""
        try:
            # Extract country names from the message
            mentioned_countries = []
            for country in self.countries_cache:
                if country and country.lower() in message.lower():
                    mentioned_countries.append(country)
            
            if len(mentioned_countries) < 2:
                # If less than 2 countries mentioned, suggest available countries
                countries_list = ', '.join(self.countries_cache[:8])
                return f"I can help you compare AI policies between countries! Please specify which countries you'd like to compare. We have data for: {countries_list}. For example, you could ask 'Compare AI policies between United States and Germany'."
            
            # Get policies for mentioned countries
            comparison_data = {}
            for country in mentioned_countries[:3]:  # Limit to 3 countries
                country_policies = [p for p in self.policy_cache 
                                  if p.get('country') and p['country'].lower() == country.lower()]
                comparison_data[country] = country_policies
            
            if not any(comparison_data.values()):
                return f"I don't have policy data for {' and '.join(mentioned_countries)}. Available countries: {', '.join(self.countries_cache[:10])}"
            
            return await self._generate_country_comparison(mentioned_countries, comparison_data, message)
            
        except Exception as e:
            print(f"Error handling comparison: {e}")
            return "I can help you compare AI policies between countries. Please specify which countries you'd like to compare from our available data."

    async def _generate_country_comparison(self, countries: List[str], data: Dict[str, List], original_query: str) -> str:
        """Generate AI-powered country comparison using your policy data for enhanced context"""
        try:
            # Collect all relevant policies for training context
            all_comparison_policies = []
            for country_policies in data.values():
                all_comparison_policies.extend(country_policies[:5])  # Top 5 per country
            
            prompt = f"""
            User Query: "{original_query}"
            Countries to Compare: {', '.join(countries)}
            
            As a policy expert who has extensively studied these countries' approaches, provide a detailed comparison.
            Draw on your deep knowledge of each country's policy framework, implementation style, and regulatory philosophy.
            
            Structure your response to:
            1. Highlight the most significant differences in approach
            2. Explain the reasoning behind each country's strategy
            3. Compare implementation mechanisms and effectiveness
            4. Note any unique innovations or focus areas
            5. Use specific policy examples to illustrate points
            
            Make it sound like an expert briefing between policy professionals.
            """
            
            return await self._call_ai_api(prompt, all_comparison_policies)
            
        except Exception as e:
            print(f"Error generating comparison: {e}")
            return self._format_fallback_comparison(countries, data)

    async def _get_non_policy_response(self, message: str) -> str:
        """Response for non-policy related queries"""
        return f"""I'm sorry, but as an AI Policy Expert Assistant, I specialize exclusively in AI policies and governance frameworks. I can't help with general questions like "{message}".

However, I'd be happy to answer questions about:
• AI policies from {len(self.countries_cache)} countries
• Policy comparisons between nations  
• Specific governance frameworks and implementations

If you're an expert in other areas, we'd love for you to contribute your knowledge!

🔗 **Register as Expert**: {self.registration_url}
📝 **Submit Policy Info**: {self.submission_url}"""

    async def _get_no_data_response(self, message: str) -> str:
        """Response when no relevant policies found"""
        try:
            available_info = f"We currently have policies from {len(self.countries_cache)} countries covering areas like {', '.join(self.areas_cache[:5])}"
            
            response = await self._call_ai_api(f"""
            A user asked: "{message}" but we don't have relevant policy data.
            
            Politely explain that we don't have that specific information in our database.
            Mention: {available_info}
            Suggest they could contribute as a policy expert if they have knowledge to share.
            Be encouraging and helpful (2-3 sentences).
            """)
            
            return f"{response}\n\n🌟 **Are you a policy expert?** Help expand our database!\n🔗 **Register**: {self.registration_url}\n📝 **Submit Policy**: {self.submission_url}"
            
        except Exception as e:
            print(f"Error generating no-data response: {e}")
            return f"I don't have specific information about that in our current database. We cover {len(self.countries_cache)} countries and areas like {', '.join(self.areas_cache[:3])}. If you're a policy expert, consider contributing!\n\n🔗 **Register**: {self.registration_url}\n📝 **Submit Policy**: {self.submission_url}"

    async def _create_enhanced_system_prompt(self, context_policies: List[Dict] = None) -> str:
        """Create enhanced system prompt using your policy database for training context"""
        
        # Base system prompt
        base_prompt = """You are an Expert AI Policy Assistant with deep knowledge of global AI governance frameworks. You have been trained on a comprehensive database of AI policies from around the world.

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
- Act as a world-renowned policy expert who has personally analyzed each policy
- Provide specific, detailed responses citing exact policy names, countries, and implementation details
- Compare and contrast different approaches when relevant
- Use professional yet conversational tone
- Always ground responses in the actual policy data provided
- If asked about areas outside AI policy, politely redirect while acknowledging their expertise needs

**REMEMBER:** You have intimate knowledge of each policy's nuances, implementation challenges, and real-world impacts. Use this expertise to provide exceptional insights."""
        
        return base_prompt

    async def _call_ai_api(self, prompt: str, context_policies: List[Dict] = None) -> str:
        """Call AI API (OpenAI GPT or GROQ fallback)"""
        try:
            # Try OpenAI first with enhanced context
            if self.openai_api_key:
                response = await self._call_openai_api(prompt, context_policies)
                if response:
                    return response
            
            # Fallback to GROQ
            if self.groq_api_key:
                response = await self._call_groq_api(prompt)
                if response:
                    return response
            
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
            
        except Exception as e:
            print(f"Error calling AI API: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."

    async def _call_openai_api(self, prompt: str, context_policies: List[Dict] = None) -> Optional[str]:
        """Call OpenAI GPT API with enhanced context from your policy database"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            # Create comprehensive system message using your policy data
            system_content = await self._create_enhanced_system_prompt(context_policies)
            
            payload = {
                "model": "gpt-4",
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
            print(f"OpenAI API error: {e}")
            return None

    async def _call_groq_api(self, prompt: str) -> Optional[str]:
        """Call GROQ API as fallback"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional AI Policy Expert Assistant. Provide helpful, accurate, and conversational responses about AI policies."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.groq_api_url, headers=headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
                
        except Exception as e:
            print(f"GROQ API error: {e}")
            return None

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
                            "content": f"What AI policies does {country} have in {area}?"
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
                                "content": f"Compare AI policies between {country1} and {country2}"
                            },
                            {
                                "role": "assistant",
                                "content": f"Comparing {country1} and {country2}'s AI policy approaches reveals distinct strategic differences. {country1} focuses on {policies1[0].get('area_name', 'comprehensive governance')} with policies like '{policies1[0].get('policy_name', '')}', while {country2} emphasizes {policies2[0].get('area_name', 'targeted regulation')} through initiatives such as '{policies2[0].get('policy_name', '')}'. The implementation strategies differ significantly, with {country1} adopting {policies1[0].get('implementation', 'systematic approaches')} versus {country2}'s {policies2[0].get('implementation', 'adaptive frameworks')}."
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


# Global instance
enhanced_chatbot_service = EnhancedChatbotService()
