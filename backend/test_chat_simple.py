"""
Test the conversational RAG system locally
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_chat_endpoint():
    """Test the chat endpoint locally"""
    print("🧪 Testing conversational RAG system...")
    
    try:
        from models.chat import ChatRequest
        from services.conversational_rag_service import conversational_rag_service
        
        # Test message 1
        print("\n📱 Testing first message...")
        request1 = ChatRequest(
            message="Hello, I'm interested in AI policy in the USA",
            conversation_id=None,
            user_id="test_user_123"
        )
        
        response1 = await conversational_rag_service.chat_with_memory(request1)
        print(f"✅ Response 1: {response1.response[:100]}...")
        print(f"🆔 Conversation ID: {response1.conversation_id}")
        
        # Test message 2 - should remember context
        print("\n📱 Testing second message with context...")
        request2 = ChatRequest(
            message="What are the main challenges with AI safety in that country?",
            conversation_id=response1.conversation_id,
            user_id="test_user_123"
        )
        
        response2 = await conversational_rag_service.chat_with_memory(request2)
        print(f"✅ Response 2: {response2.response[:100]}...")
        print(f"🔍 Context used: {response2.metadata.get('conversation_context_used', False)}")
        print(f"📊 Context messages: {response2.metadata.get('context_messages_count', 0)}")
        
        # Test message 3 - more context
        print("\n📱 Testing third message with more context...")
        request3 = ChatRequest(
            message="Can you summarize what we discussed about AI policy?",
            conversation_id=response1.conversation_id,
            user_id="test_user_123"
        )
        
        response3 = await conversational_rag_service.chat_with_memory(request3)
        print(f"✅ Response 3: {response3.response[:100]}...")
        print(f"🔍 Context used: {response3.metadata.get('conversation_context_used', False)}")
        print(f"📊 Context messages: {response3.metadata.get('context_messages_count', 0)}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_endpoint())
