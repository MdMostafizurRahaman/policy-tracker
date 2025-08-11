"""
Quick test for the exact response format requested
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_exact_responses():
    """Test the exact response formats requested"""
    
    print("🧪 Testing Exact Response Formats")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Non-Policy Query (Moon Question)",
            "query": "tell me who went to the moon first",
            "expected_start": "I really appreciate you reaching out! But I'm sorry."
        },
        {
            "name": "Weather Question", 
            "query": "what's the weather like today?",
            "expected_start": "I really appreciate you reaching out! But I'm sorry."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"Query: '{test_case['query']}'")
        print("-" * 40)
        
        try:
            request = ChatRequest(
                message=test_case['query'],
                conversation_id=f"test_{i}",
                user_id="test_user"
            )
            
            response = await enhanced_chatbot_service.chat(request)
            
            print("Response:")
            print(response.response)
            
            # Check if it starts correctly
            if response.response.startswith(test_case['expected_start']):
                print("✅ CORRECT: Starts with expected text")
            else:
                print("❌ INCORRECT: Does not start with expected text")
                
            # Check for key elements
            key_elements = [
                "passionate policy researcher",
                "10 policy domains", 
                "AI Safety",
                "CyberSafety",
                "Would you be interested in contributing"
            ]
            
            for element in key_elements:
                if element in response.response:
                    print(f"✅ Contains: {element}")
                else:
                    print(f"❌ Missing: {element}")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_exact_responses())
