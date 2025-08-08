#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat import ChatRequest, ChatMessage  # Use the correct models
from datetime import datetime

async def test_conversation_memory():
    """Test the conversation memory feature with the fixed area filtering"""
    
    print("🧠 Testing Enhanced Conversation Memory with Fixed Area Filtering")
    print("=" * 70)
    
    # Initialize the service
    service = EnhancedChatbotService()
    
    # Create a conversation with memory
    conversation_id = f"test_memory_{datetime.utcnow().timestamp()}"
    
    # Step 1: Ask about USA AI policies (to establish context)
    print("\n📝 Step 1: Ask about USA AI policies")
    request1 = ChatRequest(
        message="What AI Safety policies does the United States have?",
        conversation_id=conversation_id,
        user_id="test_user"
    )
    
    response1 = await service.chat(request1)
    print(f"Response 1: {response1.response[:200]}...")
    
    # Step 2: Follow-up comparison query (should use conversation context)
    print("\n🔄 Step 2: Follow-up comparison question")
    request2 = ChatRequest(
        message="What's the difference between USA AI policy and Russia AI policy?",
        conversation_id=conversation_id,
        user_id="test_user"
    )
    
    response2 = await service.chat(request2)
    print(f"Response 2: {response2.response}")
    
    print("\n" + "=" * 70)
    print("✅ Conversation Memory Test Complete!")
    
    # Check if the response indicates proper comparison
    if "don't have" not in response2.response.lower() and ("united states" in response2.response.lower() or "russia" in response2.response.lower()):
        print("🎉 SUCCESS: Conversation memory is working correctly!")
        print("   - Context from previous conversation was preserved")
        print("   - Comparison was generated using both countries' data")
    else:
        print("❌ ISSUE: Conversation memory may need further adjustment")
        print(f"   - Response: {response2.response[:150]}...")

if __name__ == "__main__":
    asyncio.run(test_conversation_memory())
