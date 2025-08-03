#!/usr/bin/env python3
"""
Debug conversation memory functionality
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chatbot_service_enhanced import EnhancedChatbotService

async def debug_conversation_context():
    """Debug conversation context extraction"""
    
    print("🔍 Debugging Conversation Context Extraction")
    print("=" * 50)
    
    try:
        service = EnhancedChatbotService()
        await service._update_cache()
        
        # Mock conversation history
        from models.chat_dynamodb import ChatMessage
        from datetime import datetime
        
        mock_history = [
            ChatMessage(
                message_type="user",
                content="Tell me about USA AI Safety policy",
                created_at=datetime.utcnow().isoformat()
            ),
            ChatMessage(
                message_type="ai", 
                content="In the United States, there are several AI Safety policies...",
                created_at=datetime.utcnow().isoformat()
            )
        ]
        
        # Extract context
        current_message = "difference between usa ai policy and russia ai policy"
        context = service._extract_conversation_context(mock_history, current_message)
        
        print("📋 Extracted Context:")
        print(f"  Mentioned Countries: {context.get('mentioned_countries', [])}")
        print(f"  Mentioned Areas: {context.get('mentioned_areas', [])}")
        print(f"  Recent Queries: {context.get('recent_queries', [])}")
        print(f"  Last Topic: {context.get('last_topic')}")
        
        # Test policy-related detection
        is_policy_related = await service._is_policy_related_query(current_message, context)
        print(f"\n🎯 Is Policy Related: {is_policy_related}")
        
        # Test comparison detection  
        is_comparison = service._is_comparison_query(current_message)
        print(f"🔄 Is Comparison Query: {is_comparison}")
        
        # Test policy finding with context
        policies = await service._find_relevant_policies_with_context(current_message, context)
        print(f"\n📊 Found Policies with Context: {len(policies)}")
        for i, policy in enumerate(policies[:3]):
            print(f"  {i+1}. {policy.get('country', 'Unknown')} - {policy.get('policy_area', 'Unknown')} - {policy.get('policy_name', 'Unknown')[:50]}...")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_conversation_context())
