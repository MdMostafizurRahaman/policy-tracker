#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('.')

from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat import ChatRequest

async def test_russia_disinformation():
    """Test Russia disinformation policy search"""
    print("🇷🇺 Testing Russia Disinformation Policy Search...")
    
    service = EnhancedChatbotService()
    
    # Test Russia disinformation query
    chat_request = ChatRequest(
        message="russia disinformation policy",
        conversation_id=None,
        user_id="test_user"
    )
    
    try:
        response = await service.chat(chat_request)
        print(f"✅ Russia response: {response.response[:200]}...")
        
        # Check if response indicates policies found or not found
        if "don't have" in response.response.lower() or "no " in response.response.lower():
            print("❌ Still showing no data for Russia disinformation")
        else:
            print("✅ Found Russia disinformation policies!")
            
    except Exception as e:
        print(f"❌ Error testing Russia query: {e}")

if __name__ == "__main__":
    asyncio.run(test_russia_disinformation())
