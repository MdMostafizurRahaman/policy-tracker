"""
Test the specific AI policy Bangladesh issue to identify hallucination
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

async def test_ai_policy_bd():
    """Test the specific AI policy BD query that's causing hallucination"""
    try:
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        from models.chat import ChatRequest
        
        print("🔍 TESTING: AI POLICY IN BANGLADESH")
        print("=" * 60)
        
        # Update cache
        await enhanced_chatbot_service._update_cache()
        
        # Check what we have for Bangladesh
        print("🇧🇩 BANGLADESH POLICIES IN DATABASE:")
        bd_policies = []
        for policy in enhanced_chatbot_service.policy_cache:
            if 'bangladesh' in policy.get('country', '').lower():
                bd_policies.append(policy)
                print(f"Country: {policy.get('country', 'N/A')}")
                print(f"Area: {policy.get('area_name', 'N/A')}")
                print(f"Policy Name: {policy.get('policy_name', 'N/A')}")
                print(f"Description: {policy.get('policy_description', 'N/A')}")
                print(f"Implementation: {policy.get('implementation', 'N/A')}")
                print("---")
        
        print(f"Total Bangladesh policies: {len(bd_policies)}")
        
        # Search for relevant policies using the search function
        print("\n🔍 SEARCHING FOR 'ai policy bangladesh':")
        search_results = await enhanced_chatbot_service._find_relevant_policies("ai policy bangladesh")
        print(f"Search returned {len(search_results)} policies")
        
        for i, policy in enumerate(search_results[:3]):
            print(f"{i+1}. Country: {policy.get('country', 'N/A')}")
            print(f"   Area: {policy.get('area_name', 'N/A')}")
            print(f"   Policy Name: {policy.get('policy_name', 'N/A')}")
            print(f"   Description: {policy.get('policy_description', 'N/A')[:100]}...")
            print()
        
        # Test the actual chat request
        print("\n🤖 TESTING CHAT REQUEST:")
        test_request = ChatRequest(
            message="ai policy in bd",
            conversation_id=None,
            user_id="test_user"
        )
        
        response = await enhanced_chatbot_service.chat(test_request)
        print("RESPONSE:")
        print(response.response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_policy_bd())
