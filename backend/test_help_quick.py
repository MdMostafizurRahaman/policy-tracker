"""
Quick test for the help functionality
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_help_functionality():
    """Test the help functionality specifically"""
    
    print("🆘 Testing Help Functionality")
    print("=" * 50)
    
    help_queries = [
        "What can you help me with?",
        "help",
        "How can you assist me?",
        "What do you do?",
        "what can you do"
    ]
    
    for i, query in enumerate(help_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        print("-" * 30)
        
        try:
            request = ChatRequest(
                message=query,
                conversation_id=f"help_test_{i}",
                user_id="test_user"
            )
            
            response = await enhanced_chatbot_service.chat(request)
            print(f"Response: {response.response[:200]}...")
            
            # Check if it's using help response
            if "delighted" in response.response.lower() and "policy research" in response.response.lower():
                print("✅ PASS: Using help response")
            else:
                print("⚠️  REVIEW: May not be using help response")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_help_functionality())
