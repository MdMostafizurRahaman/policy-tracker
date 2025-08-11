"""
Quick test for Bangladesh education policy
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

async def test_bd_education():
    """Test Bangladesh education policy query"""
    try:
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        from models.chat import ChatRequest
        
        # Test the exact query the user asked
        test_request = ChatRequest(
            message="what is the education policy of bd",
            conversation_id=None,
            user_id="test_user"
        )
        
        print("🔍 Testing: 'what is the education policy of bd'")
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
    asyncio.run(test_bd_education())
