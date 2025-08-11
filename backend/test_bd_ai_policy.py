"""
Test Bangladesh AI policy query
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_bangladesh_ai_policy():
    """Test the specific Bangladesh AI policy query"""
    
    print("🇧🇩 Testing Bangladesh AI Policy Query")
    print("=" * 50)
    
    query = "ai policy of bd"
    print(f"Query: '{query}'")
    print("-" * 30)
    
    try:
        request = ChatRequest(
            message=query,
            conversation_id="bd_ai_test",
            user_id="test_user"
        )
        
        response = await enhanced_chatbot_service.chat(request)
        
        print("Response:")
        print(response.response)
        
        # Check if response is informative
        if "ChatGPT" in response.response and "trouble" in response.response:
            print("\n⚠️  API Issue detected - using fallback response")
        elif "Bangladesh" in response.response or "bd" in response.response.lower():
            print("\n✅ Contains Bangladesh-related information")
        elif "I don't have" in response.response or "sorry" in response.response:
            print("\n💡 No data available - appropriate response")
        else:
            print("\n📊 Response generated successfully")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bangladesh_ai_policy())
