#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat import ChatRequest, ChatMessage
from datetime import datetime

async def test_final_conversation_flow():
    """Test the exact conversation flow that should work"""
    
    print("🎯 Final Conversation Memory Test")
    print("=" * 50)
    
    # Initialize the service
    service = EnhancedChatbotService()
    
    # Test with a simple mock conversation history
    conversation_id = f"test_final_{datetime.utcnow().timestamp()}"
    
    # Create mock conversation history (as if Step 1 already happened)
    mock_history = [
        ChatMessage(
            role="user",
            content="What AI Safety policies does the United States have?",
            timestamp=datetime.utcnow()
        ),
        ChatMessage(
            role="assistant", 
            content="The United States has several AI Safety policies including...",
            timestamp=datetime.utcnow()
        )
    ]
    
    # Extract context from this history
    context = service._extract_conversation_context(mock_history, "difference between USA AI policy and Russia AI policy")
    print(f"📝 Extracted Context: {context}")
    
    # Test if it's recognized as a policy query
    is_policy = await service._is_policy_related_query("difference between USA AI policy and Russia AI policy", context)
    print(f"🔍 Is Policy Query: {is_policy}")
    
    # Test if it's recognized as a comparison query
    is_comparison = service._is_comparison_query("difference between USA AI policy and Russia AI policy")
    print(f"⚖️  Is Comparison Query: {is_comparison}")
    
    # Test the comparison handler directly
    print(f"\n🎯 Testing direct comparison handling...")
    result = await service._handle_country_comparison(
        "difference between USA AI policy and Russia AI policy", 
        mock_history, 
        context
    )
    
    print(f"\n📋 Comparison Result:")
    print(result)
    
    print("\n" + "=" * 50)
    if "don't have" not in result.lower() and ("united states" in result.lower() and "russia" in result.lower()):
        print("✅ SUCCESS: Conversation memory is now working correctly!")
    else:
        print("❌ Still needs work - checking for specific issues...")
        if "united states" not in result.lower():
            print("   - USA data is not being included in comparison")
        if "russia" not in result.lower():
            print("   - Russia data is not being included in comparison")

if __name__ == "__main__":
    asyncio.run(test_final_conversation_flow())
