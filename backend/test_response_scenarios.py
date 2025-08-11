"""
Test the fixed response logic for different scenarios
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

async def test_response_scenarios():
    """Test different response scenarios"""
    try:
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        from models.chat import ChatRequest
        
        print("🔍 TESTING RESPONSE SCENARIOS")
        print("=" * 60)
        
        test_scenarios = [
            {
                "name": "Policy Query with No Data (should encourage contribution)",
                "query": "digital education policy of india",
                "expected": "Should ask for contribution"
            },
            {
                "name": "Non-Policy Query (should NOT ask for contribution)",
                "query": "who went to the moon first",
                "expected": "Should politely redirect without contribution request"
            },
            {
                "name": "Policy Query with Existing Data (should provide data)",
                "query": "AI policy Germany",
                "expected": "Should provide policy information"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n--- TEST {i}: {scenario['name']} ---")
            print(f"Query: '{scenario['query']}'")
            print(f"Expected: {scenario['expected']}")
            print("Response:")
            print("-" * 50)
            
            test_request = ChatRequest(
                message=scenario['query'],
                conversation_id=None,
                user_id="test_user"
            )
            
            response = await enhanced_chatbot_service.chat(test_request)
            print(response.response)
            print("-" * 50)
            
            # Check if contribution request is present
            has_contribution_request = "Would you be interested in contributing to our policy knowledge base?" in response.response
            print(f"Contains contribution request: {'✅ YES' if has_contribution_request else '❌ NO'}")
            print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_response_scenarios())
