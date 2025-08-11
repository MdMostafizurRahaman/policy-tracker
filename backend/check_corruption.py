"""
Check for database corruption - policies with wrong country assignments
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

async def check_database_corruption():
    """Check for policies with mismatched country/content"""
    try:
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        
        print("🔍 CHECKING FOR DATABASE CORRUPTION")
        print("=" * 60)
        
        await enhanced_chatbot_service._update_cache()
        
        corruption_issues = []
        
        for policy in enhanced_chatbot_service.policy_cache:
            country = policy.get('country', '').lower()
            policy_name = policy.get('policy_name', '').lower()
            description = policy.get('policy_description', '').lower()
            
            # Check for obvious mismatches
            mismatches = []
            
            if country == 'bangladesh':
                if 'german' in policy_name or 'germany' in description:
                    mismatches.append("German content in Bangladesh policy")
                if 'turing institute' in description or 'uk' in description:
                    mismatches.append("UK content in Bangladesh policy")
                if 'algeria' in policy_name or 'algerian' in description:
                    mismatches.append("Algerian content in Bangladesh policy")
                if 'united states' in description or 'america' in description:
                    mismatches.append("US content in Bangladesh policy")
            
            if country == 'united states':
                if 'german' in policy_name or 'germany' in description:
                    mismatches.append("German content in US policy")
                if 'uk' in description or 'britain' in description:
                    mismatches.append("UK content in US policy")
            
            # Add more country checks as needed
            
            if mismatches:
                corruption_issues.append({
                    'country': policy.get('country'),
                    'policy_name': policy.get('policy_name'),
                    'description': policy.get('policy_description')[:200],
                    'issues': mismatches
                })
        
        print(f"🚨 FOUND {len(corruption_issues)} CORRUPTION ISSUES:")
        print("=" * 60)
        
        for i, issue in enumerate(corruption_issues, 1):
            print(f"{i}. COUNTRY: {issue['country']}")
            print(f"   POLICY: {issue['policy_name']}")
            print(f"   ISSUES: {', '.join(issue['issues'])}")
            print(f"   DESCRIPTION: {issue['description']}...")
            print()
        
        if corruption_issues:
            print("🔧 RECOMMENDATION:")
            print("The database has serious country assignment corruption.")
            print("Policies are assigned to wrong countries!")
            print("This needs to be fixed before the chatbot can work properly.")
        else:
            print("✅ No obvious corruption detected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database_corruption())
