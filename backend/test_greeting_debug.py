#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('.')

from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat import ChatRequest

async def test_greeting_system():
    """Test the greeting response system"""
    print("🧪 Testing Greeting Response System...")
    
    service = EnhancedChatbotService()
    
    # Test direct greeting method
    print("\n1. Testing _get_greeting_response() method directly:")
    try:
        response = await service._get_greeting_response('hello', [])
        print(f"✅ Direct greeting response: {response[:100]}...")
        print(f"Response type: {type(response)}")
    except Exception as e:
        print(f"❌ Error in direct greeting: {e}")
    
    # Test full chat flow with greeting
    print("\n2. Testing full chat flow with greeting:")
    try:
        chat_request = ChatRequest(
            message="hello",
            conversation_id=None,
            user_id="test_user"
        )
        
        # Mock the cache to avoid database calls
        service.policy_cache = []
        service.countries_cache = []
        service.areas_cache = []
        service.last_cache_update = 999999999999  # Far future to avoid cache update
        
        response = await service.chat(chat_request)
        print(f"✅ Full chat response: {response.response[:100]}...")
        print(f"Conversation ID: {response.conversation_id}")
    except Exception as e:
        print(f"❌ Error in full chat: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_greeting_system())
