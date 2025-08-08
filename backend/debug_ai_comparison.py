#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat import ChatRequest, ChatMessage
from datetime import datetime

async def debug_comparison_logic():
    """Debug the comparison logic to see why USA data isn't being found"""
    
    print("🔍 Debugging USA vs Russia AI Policy Comparison")
    print("=" * 60)
    
    # Initialize the service
    service = EnhancedChatbotService()
    await service._update_cache()
    
    # Check what USA policies exist
    print("\n📋 USA Policies in Database:")
    usa_policies = [p for p in service.policy_cache if p.get('country', '').lower() == 'united states']
    print(f"Total USA policies: {len(usa_policies)}")
    
    for i, policy in enumerate(usa_policies[:5]):
        print(f"  {i+1}. {policy.get('policy_name', 'Unknown')} - Area: {policy.get('area_name', 'Unknown')}")
    
    # Check what Russia policies exist  
    print("\n📋 Russia Policies in Database:")
    russia_policies = [p for p in service.policy_cache if p.get('country', '').lower() == 'russia']
    print(f"Total Russia policies: {len(russia_policies)}")
    
    for i, policy in enumerate(russia_policies[:5]):
        print(f"  {i+1}. {policy.get('policy_name', 'Unknown')} - Area: {policy.get('area_name', 'Unknown')}")
    
    # Test the AI filtering logic
    print("\n🤖 Testing AI-related filtering:")
    
    # USA AI policies
    usa_ai_policies = []
    for policy in usa_policies:
        policy_area = policy.get('area_name', '').lower()
        policy_name = policy.get('policy_name', '').lower()
        policy_desc = policy.get('policy_description', '').lower()
        
        # Check if AI-related
        if ('ai safety' in policy_area or
            any(term in policy_name or term in policy_desc for term in ["ai", "artificial intelligence", "machine learning", "automation"])):
            usa_ai_policies.append(policy)
    
    print(f"USA AI-related policies: {len(usa_ai_policies)}")
    for policy in usa_ai_policies:
        print(f"  - {policy.get('policy_name', 'Unknown')} (Area: {policy.get('area_name', 'Unknown')})")
    
    # Russia AI policies
    russia_ai_policies = []
    for policy in russia_policies:
        policy_area = policy.get('area_name', '').lower()
        policy_name = policy.get('policy_name', '').lower()
        policy_desc = policy.get('policy_description', '').lower()
        
        # Check if AI-related
        if ('ai safety' in policy_area or
            any(term in policy_name or term in policy_desc for term in ["ai", "artificial intelligence", "machine learning", "automation"])):
            russia_ai_policies.append(policy)
    
    print(f"Russia AI-related policies: {len(russia_ai_policies)}")
    for policy in russia_ai_policies:
        print(f"  - {policy.get('policy_name', 'Unknown')} (Area: {policy.get('area_name', 'Unknown')})")
    
    print("\n" + "=" * 60)
    
    if usa_ai_policies and russia_ai_policies:
        print("✅ Both countries have AI-related policies - comparison should work!")
    elif usa_ai_policies:
        print("⚠️  USA has AI policies but Russia doesn't - partial comparison possible")
    elif russia_ai_policies:
        print("⚠️  Russia has AI policies but USA doesn't - partial comparison possible")
    else:
        print("❌ Neither country has detectable AI policies")

if __name__ == "__main__":
    asyncio.run(debug_comparison_logic())
