#!/usr/bin/env python3
"""
Quick test script for the enhanced chatbot
"""
import asyncio
import sys
sys.path.append('.')

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_chat():
    try:
        print("🧪 Testing Enhanced Chatbot Service...")
        
        # Test 1: General policy query
        print("\n1️⃣ Testing: 'What policies does United States have?'")
        request1 = ChatRequest(message="What policies does United States have?")
        response1 = await enhanced_chatbot_service.chat(request1)
        print(f"✅ Response: {response1.response[:200]}...")
        
        # Test 2: Country comparison
        print("\n2️⃣ Testing: 'Compare AI policies between USA and Canada'")
        request2 = ChatRequest(message="Compare AI policies between USA and Canada")
        response2 = await enhanced_chatbot_service.chat(request2)
        print(f"✅ Response: {response2.response[:200]}...")
        
        # Test 3: Non-database query
        print("\n3️⃣ Testing: 'What is the weather today?'")
        request3 = ChatRequest(message="What is the weather today?")
        response3 = await enhanced_chatbot_service.chat(request3)
        print(f"✅ Response: {response3.response[:200]}...")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())
