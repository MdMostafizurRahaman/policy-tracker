"""
Test script for the enhanced intelligent chatbot service
Tests the human-like, smart responses for different scenarios
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_intelligent_chatbot():
    """Test the enhanced intelligent chatbot responses"""
    
    print("🤖 Testing Enhanced Intelligent Chatbot Service")
    print("=" * 60)
    
    # Test scenarios as requested by the user
    test_scenarios = [
        {
            "name": "Greeting Test - Should explain services intelligently",
            "message": "Hello",
            "expected_behavior": "Human-like greeting with smart service description"
        },
        {
            "name": "Policy Query Test - Should show smart database response", 
            "message": "Tell me about AI safety policies in the United States",
            "expected_behavior": "Intelligent response using only database information"
        },
        {
            "name": "Non-Policy Query Test - Should apologize humanly",
            "message": "What's the weather like?", 
            "expected_behavior": "Human-like apology and polite redirection to policy topics"
        },
        {
            "name": "Missing Data Test - Should ask politely for contribution",
            "message": "What are the space exploration policies in Mars?",
            "expected_behavior": "Human-like apology and polite request for data contribution"
        },
        {
            "name": "Help Request - Should be smart and engaging",
            "message": "What can you help me with?",
            "expected_behavior": "Intelligent explanation of capabilities"
        },
        {
            "name": "Country Comparison - Should be intelligent",
            "message": "Compare AI policies between US and Canada", 
            "expected_behavior": "Smart comparison using database information"
        },
        {
            "name": "Thank You Response - Should be warm and human-like",
            "message": "Thank you",
            "expected_behavior": "Warm, human-like acknowledgment"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"Input: '{scenario['message']}'")
        print(f"Expected: {scenario['expected_behavior']}")
        print("-" * 50)
        
        try:
            # Create chat request
            request = ChatRequest(
                message=scenario['message'],
                conversation_id=f"test_conv_{i}",
                user_id="test_user"
            )
            
            # Get response
            response = await enhanced_chatbot_service.chat(request)
            
            print(f"🤖 Response:")
            print(response.response)
            print()
            
            # Quick analysis
            response_text = response.response.lower()
            
            # Check for human-like elements
            human_indicators = [
                "😊", "🌟", "💡", "🚀", "🌍", # Emojis
                "i'm", "i'd", "i'll", "genuinely", "absolutely", "delighted", # Personal language
                "excited", "thrilled", "passionate", "wonderful", "fantastic" # Enthusiastic words
            ]
            
            has_human_elements = any(indicator in response_text for indicator in human_indicators)
            
            if scenario['name'].startswith("Greeting"):
                if has_human_elements and "policy" in response_text:
                    print("✅ PASS: Human-like greeting with service description")
                else:
                    print("⚠️  REVIEW: May need more human-like elements or service description")
                    
            elif scenario['name'].startswith("Non-Policy"):
                if "sorry" in response_text or "apologize" in response_text:
                    print("✅ PASS: Contains apology for non-policy query")
                else:
                    print("⚠️  REVIEW: Should contain human-like apology")
                    
            elif scenario['name'].startswith("Missing Data"):
                if ("sorry" in response_text or "apologize" in response_text) and "contribute" in response_text:
                    print("✅ PASS: Contains apology and contribution request")
                else:
                    print("⚠️  REVIEW: Should contain apology and contribution request")
                    
            else:
                if has_human_elements:
                    print("✅ PASS: Contains human-like elements")
                else:
                    print("⚠️  REVIEW: Could be more human-like")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
    
    print("\n🎯 Enhancement Summary:")
    print("The chatbot has been enhanced to be:")
    print("• More intelligent and human-like in responses")
    print("• Smart about explaining its services in greetings")
    print("• Better at handling database information intelligently")  
    print("• More human in apologizing for non-policy queries")
    print("• Polite in requesting data contributions when information is missing")
    print("• Focused exclusively on its own database knowledge")

if __name__ == "__main__":
    asyncio.run(test_intelligent_chatbot())
