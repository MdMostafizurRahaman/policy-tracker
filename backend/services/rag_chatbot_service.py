"""
RAG (Retrieval-Augmented Generation) Service
============================================

This service implements a comprehensive RAG system that:
1. Generates embeddings for conversations
2. Stores conversation data with semantic search capabilities
3. Retrieves relevant context using hybrid search (keyword + semantic)
4. Enhances responses with retrieved context

Key Features:
- OpenAI embeddings for semantic search
- FAISS vector store for fast similarity search
- DynamoDB for persistent storage
- Hybrid retrieval (keyword + semantic)
- Context-aware response generation
"""

import asyncio
import json
import numpy as np
import faiss
import openai
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import os
import pickle
from dataclasses import dataclass
from config.dynamodb import get_dynamodb, DynamoDBClient

@dataclass
class ConversationEntry:
    """Represents a conversation entry with embeddings"""
    conversation_id: str
    user_message: str
    bot_response: str
    timestamp: datetime
    embedding: Optional[np.ndarray] = None
    keywords: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class RetrievalResult:
    """Represents a retrieval result with relevance score"""
    conversation_entry: ConversationEntry
    similarity_score: float
    keyword_matches: int
    relevance_score: float

class RAGChatbotService:
    """
    Production-ready RAG chatbot service for AWS deployment
    """
    
    def __init__(self):
        # Database connection
        self.db = None  # Will be initialized in ensure_db_connection()
        
        # OpenAI API setup
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # GROQ backup
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_api_url = os.getenv('GROQ_API_URL', "https://api.groq.com/openai/v1/chat/completions")
        
        # Vector store configuration
        self.embedding_dimension = 1536  # OpenAI ada-002 dimension
        self.faiss_index = None
        self.conversation_cache = []
        self.index_file_path = "/tmp/faiss_index.pkl"
        self.cache_file_path = "/tmp/conversation_cache.pkl"
        
        # Retrieval parameters
        self.max_retrieved_conversations = 5
        self.similarity_threshold = 0.7
        self.keyword_weight = 0.3
        self.semantic_weight = 0.7
    
    async def ensure_db_connection(self):
        """Ensure database connection is established"""
        if self.db is None:
            self.db = await get_dynamodb()
        
        # Initialize FAISS index
        self._initialize_faiss_index()
    
    def _initialize_faiss_index(self):
        """Initialize FAISS index for vector similarity search"""
        try:
            # Try to load existing index
            if os.path.exists(self.index_file_path) and os.path.exists(self.cache_file_path):
                with open(self.index_file_path, 'rb') as f:
                    index_data = pickle.load(f)
                    self.faiss_index = index_data['index']
                
                with open(self.cache_file_path, 'rb') as f:
                    self.conversation_cache = pickle.load(f)
                
                print(f"✅ Loaded FAISS index with {len(self.conversation_cache)} conversations")
            else:
                # Create new index
                self.faiss_index = faiss.IndexFlatIP(self.embedding_dimension)  # Inner product for cosine similarity
                print("🔧 Created new FAISS index")
                
        except Exception as e:
            print(f"⚠️ Error loading FAISS index, creating new one: {e}")
            self.faiss_index = faiss.IndexFlatIP(self.embedding_dimension)
            self.conversation_cache = []
    
    async def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text using OpenAI API"""
        try:
            # Clean and prepare text
            clean_text = text.strip().replace('\n', ' ')[:8000]  # Limit text length
            
            if not clean_text:
                return None
            
            # Use OpenAI embeddings API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: openai.embeddings.create(
                    input=clean_text,
                    model="text-embedding-ada-002"
                )
            )
            
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        import re
        
        # Clean text and extract words
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Filter out common stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    async def store_conversation(self, user_message: str, bot_response: str, 
                               conversation_id: str, user_id: str = None) -> bool:
        """Store conversation with embeddings in database and vector store"""
        try:
            # Generate embedding for the conversation context
            conversation_text = f"User: {user_message}\nBot: {bot_response}"
            embedding = await self.generate_embedding(conversation_text)
            
            # Extract keywords
            keywords = self.extract_keywords(user_message + " " + bot_response)
            
            # Create conversation entry
            entry = ConversationEntry(
                conversation_id=conversation_id,
                user_message=user_message,
                bot_response=bot_response,
                timestamp=datetime.utcnow(),
                embedding=embedding,
                keywords=keywords,
                metadata={
                    'user_id': user_id,
                    'message_length': len(user_message),
                    'response_length': len(bot_response)
                }
            )
            
            # Store in DynamoDB
            conversation_data = {
                'conversation_id': conversation_id,
                'user_id': user_id or 'anonymous',
                'user_message': user_message,
                'bot_response': bot_response,
                'timestamp': entry.timestamp.isoformat(),
                'keywords': keywords,
                'embedding': embedding.tolist() if embedding is not None else None,
                'metadata': entry.metadata
            }
            
            await self.db.put_item('conversation_embeddings', conversation_data)
            
            # Add to FAISS index if embedding exists
            if embedding is not None:
                self.conversation_cache.append(entry)
                self.faiss_index.add(embedding.reshape(1, -1))
                
                # Save index periodically
                if len(self.conversation_cache) % 10 == 0:
                    self._save_index()
            
            print(f"✅ Stored conversation: {conversation_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error storing conversation: {e}")
            return False
    
    def _save_index(self):
        """Save FAISS index and cache to disk"""
        try:
            # Save FAISS index
            with open(self.index_file_path, 'wb') as f:
                pickle.dump({'index': self.faiss_index}, f)
            
            # Save conversation cache
            with open(self.cache_file_path, 'wb') as f:
                pickle.dump(self.conversation_cache, f)
            
            print(f"💾 Saved FAISS index with {len(self.conversation_cache)} conversations")
            
        except Exception as e:
            print(f"⚠️ Error saving index: {e}")
    
    async def retrieve_relevant_conversations(self, query: str, user_id: str = None) -> List[RetrievalResult]:
        """Retrieve relevant conversations using hybrid search"""
        try:
            # Generate embedding for query
            query_embedding = await self.generate_embedding(query)
            query_keywords = self.extract_keywords(query)
            
            results = []
            
            # 1. Semantic similarity search using FAISS
            semantic_results = []
            if query_embedding is not None and self.faiss_index.ntotal > 0:
                # Search for similar conversations
                similarities, indices = self.faiss_index.search(
                    query_embedding.reshape(1, -1), 
                    min(self.max_retrieved_conversations * 2, self.faiss_index.ntotal)
                )
                
                for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                    if idx < len(self.conversation_cache) and similarity > self.similarity_threshold:
                        entry = self.conversation_cache[idx]
                        semantic_results.append((entry, similarity))
            
            # 2. Keyword-based search from database
            keyword_results = await self._keyword_search(query_keywords, user_id)
            
            # 3. Combine and rank results
            all_results = {}
            
            # Add semantic results
            for entry, similarity in semantic_results:
                key = entry.conversation_id
                if key not in all_results:
                    all_results[key] = {
                        'entry': entry,
                        'semantic_score': similarity,
                        'keyword_matches': 0
                    }
            
            # Add keyword results
            for entry, keyword_matches in keyword_results:
                key = entry.conversation_id
                if key in all_results:
                    all_results[key]['keyword_matches'] = keyword_matches
                else:
                    all_results[key] = {
                        'entry': entry,
                        'semantic_score': 0.0,
                        'keyword_matches': keyword_matches
                    }
            
            # 4. Calculate final relevance scores
            for key, data in all_results.items():
                # Normalize keyword matches (0-1 scale)
                max_keywords = len(query_keywords) if query_keywords else 1
                keyword_score = min(data['keyword_matches'] / max_keywords, 1.0)
                
                # Combined relevance score
                relevance_score = (
                    self.semantic_weight * data['semantic_score'] + 
                    self.keyword_weight * keyword_score
                )
                
                results.append(RetrievalResult(
                    conversation_entry=data['entry'],
                    similarity_score=data['semantic_score'],
                    keyword_matches=data['keyword_matches'],
                    relevance_score=relevance_score
                ))
            
            # Sort by relevance score and return top results
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:self.max_retrieved_conversations]
            
        except Exception as e:
            print(f"❌ Error retrieving conversations: {e}")
            return []
    
    async def _keyword_search(self, keywords: List[str], user_id: str = None) -> List[Tuple[ConversationEntry, int]]:
        """Search conversations by keywords in database"""
        try:
            # Query DynamoDB for conversations with matching keywords
            results = []
            
            # Scan conversations table (in production, use GSI for better performance)
            response = await self.db.scan_table('conversation_embeddings')
            
            for item in response:
                stored_keywords = item.get('keywords', [])
                
                # Count keyword matches
                matches = sum(1 for keyword in keywords if keyword in stored_keywords)
                
                if matches > 0:
                    # Reconstruct conversation entry
                    entry = ConversationEntry(
                        conversation_id=item['conversation_id'],
                        user_message=item['user_message'],
                        bot_response=item['bot_response'],
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        keywords=stored_keywords,
                        metadata=item.get('metadata', {})
                    )
                    
                    results.append((entry, matches))
            
            return results
            
        except Exception as e:
            print(f"❌ Error in keyword search: {e}")
            return []
    
    async def generate_rag_response(self, query: str, conversation_id: str, user_id: str = None) -> str:
        """Generate response using RAG (retrieval + generation)"""
        try:
            # 1. Retrieve relevant conversations
            relevant_conversations = await self.retrieve_relevant_conversations(query, user_id)
            
            # 2. Prepare context from retrieved conversations
            context_parts = []
            if relevant_conversations:
                context_parts.append("**Relevant Previous Conversations:**")
                for i, result in enumerate(relevant_conversations, 1):
                    entry = result.conversation_entry
                    context_parts.append(f"\n{i}. Previous Query: {entry.user_message}")
                    context_parts.append(f"   Previous Response: {entry.bot_response}")
                    context_parts.append(f"   (Relevance: {result.relevance_score:.2f})")
            
            context = "\n".join(context_parts)
            
            # 3. Generate enhanced prompt with context
            enhanced_prompt = f"""You are an intelligent assistant with access to previous conversation history. 
Use the context from previous conversations to provide more accurate and personalized responses.

{context}

**Current User Query:** {query}

**Instructions:**
1. Use relevant information from previous conversations to enhance your response
2. Be consistent with previous answers while providing new insights
3. If the current query relates to previous discussions, reference them appropriately
4. Provide a helpful, accurate, and contextually aware response

**Response:**"""
            
            # 4. Generate response using AI API
            response = await self._call_ai_api_with_context(enhanced_prompt)
            
            # 5. Store the new conversation
            await self.store_conversation(query, response, conversation_id, user_id)
            
            return response
            
        except Exception as e:
            print(f"❌ Error generating RAG response: {e}")
            # Fallback to simple response
            return "I apologize, but I'm experiencing technical difficulties. Please try again."
    
    async def _call_ai_api_with_context(self, prompt: str) -> str:
        """Call AI API with context-enhanced prompt"""
        try:
            import httpx
            
            # Try OpenAI first
            if self.openai_api_key:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that uses conversation history to provide better responses."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions", 
                        headers=headers, 
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data['choices'][0]['message']['content'].strip()
                    else:
                        print(f"OpenAI API error: {response.status_code}")
            
            # Fallback to GROQ
            if self.groq_api_key:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "llama3-8b-8192",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that uses conversation history to provide better responses."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(self.groq_api_url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data['choices'][0]['message']['content'].strip()
            
            return "I apologize, but I'm unable to process your request right now."
            
        except Exception as e:
            print(f"❌ Error calling AI API: {e}")
            return "I'm experiencing technical difficulties. Please try again later."
    
    async def initialize_from_existing_conversations(self):
        """Initialize RAG system from existing conversation data"""
        try:
            print("🔄 Initializing RAG system from existing conversations...")
            
            # Get existing conversations from chat_sessions table
            sessions = await self.db.scan_table('chat_sessions')
            
            processed = 0
            for session in sessions:
                messages = session.get('messages', [])
                conversation_id = session.get('session_id', '')
                user_id = session.get('user_id', 'anonymous')
                
                # Process message pairs (user + bot)
                for i in range(0, len(messages) - 1, 2):
                    if i + 1 < len(messages):
                        user_msg = messages[i]
                        bot_msg = messages[i + 1]
                        
                        if (user_msg.get('role') == 'user' and 
                            bot_msg.get('role') == 'assistant'):
                            
                            await self.store_conversation(
                                user_msg.get('content', ''),
                                bot_msg.get('content', ''),
                                f"{conversation_id}_{i}",
                                user_id
                            )
                            processed += 1
            
            # Save the index
            self._save_index()
            
            print(f"✅ Initialized RAG system with {processed} conversation pairs")
            
        except Exception as e:
            print(f"❌ Error initializing from existing conversations: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return {
            'total_conversations': len(self.conversation_cache),
            'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
            'embedding_dimension': self.embedding_dimension,
            'similarity_threshold': self.similarity_threshold,
            'max_retrieved_conversations': self.max_retrieved_conversations,
            'last_updated': datetime.utcnow().isoformat()
        }
