#!/usr/bin/env python3
"""
Debug script to find the lower() error
"""
import asyncio
import sys
sys.path.append('.')

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def debug_test():
    try:
        print("🔍 Debugging the lower() error...")
        
        # Test the specific failing case
        request = ChatRequest(message="What policies does United States have?")
        print(f"Request message type: {type(request.message)}")
        print(f"Request message: {request.message}")
        
        # Test the search function directly
        print("Testing search_policies directly...")
        policies = await enhanced_chatbot_service.search_policies("United States")
        print(f"Found {len(policies)} policies")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_test())
