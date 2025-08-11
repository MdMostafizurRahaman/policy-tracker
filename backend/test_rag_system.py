"""
Test the complete RAG chatbot system functionality
"""

import asyncio
import os
import sys
import time
from typing import List, Dict, Any

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_chatbot_service import RAGChatbotService
from models.rag_models import RAGDatabaseManager

async def test_rag_system():
    """Test the complete RAG system functionality"""
    
    # Initialize services
    rag_service = RAGChatbotService()
    
    # Get database manager
    from config.dynamodb import get_dynamodb
    db_manager_instance = await get_dynamodb()
    db_manager = RAGDatabaseManager(db_manager_instance)
    
    print("🚀 Testing RAG Chatbot System\n")
    
    # Test 1: Initialize database tables
    print("1. Testing database initialization...")
    try:
        await db_manager.ensure_rag_tables()
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # Test 2: Test embedding generation
    print("\n2. Testing embedding generation...")
    try:
        test_message = "What are the education policies in Bangladesh?"
        embedding = await rag_service.generate_embedding(test_message)
        print(f"✅ Embedding generated successfully (dimension: {len(embedding)})")
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return
    
    # Test 3: Test conversation storage
    print("\n3. Testing conversation storage...")
    try:
        test_user_id = "test_user_123"
        test_conversations = [
            {
                "user_message": "What are Bangladesh education policies?",
                "ai_response": "Bangladesh has several education policies including free primary education and digital learning initiatives.",
                "policy_area": "education",
                "country": "bangladesh"
            },
            {
                "user_message": "Tell me about healthcare policies in India",
                "ai_response": "India has implemented various healthcare policies including Ayushman Bharat and telemedicine initiatives.",
                "policy_area": "healthcare", 
                "country": "india"
            },
            {
                "user_message": "What about technology policies in Malaysia?",
                "ai_response": "Malaysia focuses on digital transformation with policies for Industry 4.0 and smart city development.",
                "policy_area": "technology",
                "country": "malaysia"
            }
        ]
        
        for conv in test_conversations:
            await rag_service.store_conversation(
                user_id=test_user_id,
                user_message=conv["user_message"],
                ai_response=conv["ai_response"],
                policy_area=conv.get("policy_area"),
                country=conv.get("country")
            )
        
        print(f"✅ Stored {len(test_conversations)} test conversations")
    except Exception as e:
        print(f"❌ Conversation storage failed: {e}")
        return
    
    # Test 4: Test semantic search
    print("\n4. Testing semantic search...")
    try:
        search_queries = [
            "education policies",
            "healthcare in India", 
            "digital transformation Malaysia"
        ]
        
        for query in search_queries:
            results = await rag_service.retrieve_relevant_conversations(
                query=query,
                user_id=test_user_id,
                limit=2
            )
            print(f"   Query: '{query}' -> Found {len(results)} relevant conversations")
            
    except Exception as e:
        print(f"❌ Semantic search failed: {e}")
        return
    
    # Test 5: Test RAG response generation
    print("\n5. Testing RAG response generation...")
    try:
        test_query = "What education policies exist in South Asian countries?"
        test_conversation_id = f"test_conv_{int(time.time())}"
        response = await rag_service.generate_rag_response(
            query=test_query,
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        
        print(f"✅ RAG response generated successfully")
        print(f"   Query: {test_query}")
        print(f"   Response length: {len(response)} characters")
        print(f"   Response preview: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ RAG response generation failed: {e}")
        return
    
    # Test 6: Test keyword search
    print("\n6. Testing keyword search...")
    try:
        keyword_results = await db_manager.search_by_keywords(
            keywords=["education", "policy"],
            user_id=test_user_id,
            limit=3
        )
        print(f"✅ Keyword search found {len(keyword_results)} results")
        
    except Exception as e:
        print(f"❌ Keyword search failed: {e}")
    
    # Test 7: Test conversation history retrieval
    print("\n7. Testing conversation history...")
    try:
        history = await rag_service.get_conversation_context(
            user_id=test_user_id,
            limit=5
        )
        print(f"✅ Retrieved {len(history)} conversation entries from history")
        
    except Exception as e:
        print(f"❌ Conversation history retrieval failed: {e}")
    
    # Test 8: Test vector statistics
    print("\n8. Testing vector statistics...")
    try:
        stats = await rag_service.get_vector_stats()
        print("✅ Vector statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Vector statistics failed: {e}")
    
    print("\n🎉 RAG System Testing Complete!")
    print("\nNext steps:")
    print("1. Deploy to Render with updated requirements.txt")
    print("2. Set up environment variables (OpenAI API key, AWS credentials)")
    print("3. Run migration script in production")
    print("4. Test the API endpoints")
    print("5. Monitor performance and adjust as needed")

async def test_integration_with_existing_system():
    """Test integration with existing PolicyTracker system"""
    
    print("\n🔄 Testing Integration with Existing System\n")
    
    # Test that RAG system can handle policy-specific queries
    test_cases = [
        {
            "query": "What are the latest education policies in Bangladesh?",
            "expected_areas": ["education"],
            "expected_country": "bangladesh"
        },
        {
            "query": "Tell me about healthcare reforms",
            "expected_areas": ["healthcare"],
            "expected_country": None
        },
        {
            "query": "Technology and innovation policies in Southeast Asia",
            "expected_areas": ["technology", "innovation"],
            "expected_country": None
        }
    ]
    
    rag_service = RAGChatbotService()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Integration Test {i}: {test_case['query']}")
        
        try:
            # Test that the RAG system processes the query correctly
            test_conversation_id = f"integration_test_{i}_{int(time.time())}"
            response = await rag_service.generate_rag_response(
                query=test_case['query'],
                conversation_id=test_conversation_id,
                user_id="integration_test_user"
            )
            
            print(f"✅ Integration test {i} passed")
            print(f"   Response generated successfully")
            
        except Exception as e:
            print(f"❌ Integration test {i} failed: {e}")

if __name__ == "__main__":
    print("Starting RAG Chatbot System Tests...")
    
    # Run the tests
    asyncio.run(test_rag_system())
    asyncio.run(test_integration_with_existing_system())
    
    print("\nTo run this test:")
    print("1. Make sure your environment variables are set (OPENAI_API_KEY, AWS credentials)")
    print("2. Run: python test_rag_system.py")
    print("3. Check for any errors and fix them before deployment")
