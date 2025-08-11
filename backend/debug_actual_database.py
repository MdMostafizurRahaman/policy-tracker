"""
Debug what's actually in the database vs what the chatbot is returning
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

async def debug_actual_database():
    """Check what's actually in the database"""
    try:
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        from models.chat import ChatRequest
        
        print("🔍 DEBUGGING ACTUAL DATABASE CONTENT")
        print("=" * 60)
        
        # Update cache to get real data
        await enhanced_chatbot_service._update_cache()
        
        print(f"Total policies in cache: {len(enhanced_chatbot_service.policy_cache)}")
        print(f"Countries: {enhanced_chatbot_service.countries_cache}")
        print(f"Areas: {enhanced_chatbot_service.areas_cache}")
        
        # Search for Bangladesh policies
        print("\n🇧🇩 BANGLADESH POLICIES IN DATABASE:")
        print("=" * 50)
        
        bd_policies = []
        for policy in enhanced_chatbot_service.policy_cache:
            if 'bangladesh' in policy.get('country', '').lower():
                bd_policies.append(policy)
                print(f"✅ {policy.get('title', 'No title')} - {policy.get('area', 'No area')}")
                print(f"   Country: {policy.get('country', 'No country')}")
                print(f"   Description: {policy.get('description', 'No description')[:100]}...")
                print()
        
        print(f"Total Bangladesh policies found: {len(bd_policies)}")
        
        # Search for AI policies in Bangladesh
        print("\n🤖 AI POLICIES IN BANGLADESH:")
        print("=" * 50)
        
        ai_bd_policies = []
        for policy in enhanced_chatbot_service.policy_cache:
            country = policy.get('country', '').lower()
            area = policy.get('area', '').lower()
            title = policy.get('title', '').lower()
            
            if 'bangladesh' in country and ('ai' in area or 'ai' in title or 'artificial intelligence' in title):
                ai_bd_policies.append(policy)
                print(f"✅ {policy.get('title', 'No title')}")
                print(f"   Area: {policy.get('area', 'No area')}")
                print(f"   Description: {policy.get('description', 'No description')[:150]}...")
                print()
        
        print(f"Total AI policies in Bangladesh: {len(ai_bd_policies)}")
        
        # Test the actual search function
        print("\n🔍 TESTING SEARCH FUNCTION:")
        print("=" * 50)
        
        search_results = await enhanced_chatbot_service._find_relevant_policies("ai policy bangladesh")
        print(f"Search results for 'ai policy bangladesh': {len(search_results)} policies")
        
        for i, policy in enumerate(search_results[:3], 1):
            print(f"{i}. {policy.get('title', 'No title')} ({policy.get('country', 'No country')} - {policy.get('area', 'No area')})")
            print(f"   Description: {policy.get('description', 'No description')[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_actual_database())
