"""
Test the updated chatbot logic to ensure AI is called
"""
import asyncio
import os

# Mock data for testing
mock_policies = [
    {
        "policyName": "iran",
        "country": "Iran", 
        "policyArea": "AI Safety",
        "policyDescription": ""
    },
    {
        "policyName": "Cybersecurity",
        "country": "Iran",
        "policyArea": "cyber-safety", 
        "policyDescription": "Iran is the best"
    }
]

async def test_chatbot_logic():
    """Test the decision logic for using AI vs structured response"""
    
    print("Testing Chatbot Decision Logic")
    print("=" * 40)
    
    # Mock chatbot service
    class MockChatbot:
        def __init__(self, has_api_key=True):
            self.groq_api_key = "test_key" if has_api_key else None
        
        def is_ai_enabled(self):
            return bool(self.groq_api_key)
        
        async def get_simple_ai_response(self, query, policies):
            # Mock AI response
            return f"AI Response: Iran has {len(policies)} AI policies covering areas like AI Safety and cybersecurity. This shows Iran's commitment to developing comprehensive AI governance frameworks."
        
        async def format_policies_response(self, policies, query_type, query):
            # Mock structured response (the problematic format)
            return f"""Found {len(policies)} AI Policies {query_type} "{query}"

🏛️ Iran ({len(policies)} policies)
========================

📄 iran
Area: AI Safety
Year: 2025
Status: approved
Description:

📄 Cybersecurity  
Area: cyber-safety
Year: TBD
Status: Active
Description: Iran is the best"""
    
    # Test with AI enabled
    print("Test 1: AI Enabled")
    print("-" * 20)
    chatbot_with_ai = MockChatbot(has_api_key=True)
    
    if chatbot_with_ai.is_ai_enabled():
        ai_response = await chatbot_with_ai.get_simple_ai_response("Iran", mock_policies)
        if ai_response:
            print("✅ AI Response Used:")
            print(ai_response)
        else:
            structured_response = await chatbot_with_ai.format_policies_response(mock_policies, "for country", "Iran")
            print("❌ Fallback to Structured Response:")
            print(structured_response[:200] + "...")
    
    print("\n" + "=" * 40)
    
    # Test with AI disabled
    print("Test 2: AI Disabled")
    print("-" * 20)
    chatbot_no_ai = MockChatbot(has_api_key=False)
    
    if chatbot_no_ai.is_ai_enabled():
        ai_response = await chatbot_no_ai.get_simple_ai_response("Iran", mock_policies)
        if ai_response:
            print("✅ AI Response Used:")
            print(ai_response)
        else:
            structured_response = await chatbot_no_ai.format_policies_response(mock_policies, "for country", "Iran")
            print("❌ Fallback to Structured Response:")
            print(structured_response[:200] + "...")
    else:
        structured_response = await chatbot_no_ai.format_policies_response(mock_policies, "for country", "Iran")
        print("❌ No AI Available - Using Structured Response:")
        print(structured_response[:200] + "...")
    
    print("\n" + "=" * 40)
    print("CONCLUSION:")
    print("✅ With API key: Should use AI for natural responses")
    print("❌ Without API key: Should fallback to structured format")
    print("The user is getting structured format, which means either:")
    print("1. AI API call is failing")
    print("2. Logic is not calling AI properly")
    print("3. API key is not set")

if __name__ == "__main__":
    asyncio.run(test_chatbot_logic())
