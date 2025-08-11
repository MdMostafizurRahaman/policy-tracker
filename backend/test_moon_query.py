"""
Test the specific query: "tell me who went to the moon first"
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_moon_query():
    """Test the specific moon query to see current behavior"""
    
    print("🌙 Testing Moon Query Behavior")
    print("=" * 50)
    
    query = "tell me who went to the moon first"
    print(f"Query: '{query}'")
    print("-" * 30)
    
    try:
        request = ChatRequest(
            message=query,
            conversation_id="moon_test",
            user_id="test_user"
        )
        
        response = await enhanced_chatbot_service.chat(request)
        print("Current Response:")
        print(response.response)
        print("\n" + "=" * 50)
        
        # Check if it contains the required elements
        response_lower = response.response.lower()
        
        required_elements = [
            "i really appreciate you reaching out",
            "but i'm sorry",
            "my expertise is quite specialized",
            "passionate policy researcher",
            "10 policy domains",
            "ai safety",
            "cybersafety", 
            "digital education",
            "15 countries"
        ]
        
        print("Checking Required Elements:")
        for element in required_elements:
            if element in response_lower:
                print(f"✅ Contains: '{element}'")
            else:
                print(f"❌ Missing: '{element}'")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_moon_query())
