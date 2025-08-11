"""
Test GROQ API backup functionality
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

async def test_groq_backup():
    """Test GROQ backup when OpenAI fails"""
    try:
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        from models.chat import ChatRequest
        
        print("🔍 Testing GROQ Backup System")
        print("=" * 50)
        
        # Check API keys
        print(f"OpenAI Key: {'✅ Found' if enhanced_chatbot_service.openai_api_key else '❌ Missing'}")
        print(f"GROQ Key: {'✅ Found' if enhanced_chatbot_service.groq_api_key else '❌ Missing'}")
        
        # Test the education policy query
        test_request = ChatRequest(
            message="what is the education policy of bangladesh",
            conversation_id=None,
            user_id="test_user"
        )
        
        print(f"\n🔍 Testing: '{test_request.message}'")
        print("=" * 50)
        
        response = await enhanced_chatbot_service.chat(test_request)
        
        print("✅ RESPONSE:")
        print(response.response)
        print("\n" + "=" * 50)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_groq_backup())
