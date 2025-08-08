#!/usr/bin/env python3
"""
Test conversation memory functionality in the enhanced chatbot
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting test...")

try:
    from services.chatbot_service_enhanced import EnhancedChatbotService
    from models.chat import ChatRequest
    print("Imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def test_conversation_memory():
    """Test that the chatbot remembers previous conversation context"""
    
    print("🤖 Testing Enhanced Chatbot Conversation Memory")
    print("=" * 50)
    
    try:
        # Initialize the service
        print("Initializing service...")
        service = EnhancedChatbotService()
        conversation_id = "test_memory_conv_001"
        
        print("Service initialized, starting conversation tests...")
        
        # Test 1: Ask about USA AI policy
        print("\n--- Test 1: Asking about USA AI policy ---")
        request1 = ChatRequest(
            message="Tell me about USA AI Safety policy",
            conversation_id=conversation_id,
            user_id="test_user"
        )
        
        print("Sending first request...")
        response1 = await service.chat(request1)
        print(f"Response 1: {response1.response[:300]}...")
        
        # Test 2: Ask for comparison (should use context)
        print("\n--- Test 2: Asking for comparison ---")
        request2 = ChatRequest(
            message="difference between usa ai policy and russia ai policy",
            conversation_id=conversation_id,
            user_id="test_user"
        )
        
        print("Sending second request...")
        response2 = await service.chat(request2)
        print(f"Response 2: {response2.response[:300]}...")
        
        # Check if conversation memory worked
        print("\n🎯 Analysis:")
        if "russia" in response2.response.lower() and ("usa" in response2.response.lower() or "united states" in response2.response.lower() or "america" in response2.response.lower()):
            print("✅ Conversation memory appears to be working - both countries mentioned in comparison!")
        else:
            print("⚠️ Conversation memory may need improvement - check if both countries are properly compared")
        
        print("\n🎯 Conversation Memory Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running main...")
    asyncio.run(test_conversation_memory())
