#!/usr/bin/env python3
"""
Debug policy filtering to understand the country matching issue
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chatbot_service_enhanced import EnhancedChatbotService

async def debug_policies():
    service = EnhancedChatbotService()
    await service._update_cache()
    
    print(f'Total policies: {len(service.policy_cache)}')
    
    # Check USA policies
    usa_policies = [p for p in service.policy_cache if p.get('country') and p['country'].lower() == 'united states']
    print(f'USA policies (exact match): {len(usa_policies)}')
    
    # Check exact country names in cache
    unique_countries = set(p.get('country', '') for p in service.policy_cache if p.get('country'))
    print(f'Unique countries: {sorted(unique_countries)}')
    
    # Check for different variations of USA
    usa_variations = ['united states', 'usa', 'us', 'america']
    for variation in usa_variations:
        count = len([p for p in service.policy_cache if p.get('country') and variation in p['country'].lower()])
        print(f'Policies containing "{variation}": {count}')
    
    # Check AI Safety policies for USA (case insensitive)
    usa_ai_policies = [p for p in service.policy_cache 
                      if p.get('country') and 'united states' in p['country'].lower() 
                      and p.get('policy_area') and 'ai' in p['policy_area'].lower()]
    print(f'USA AI policies: {len(usa_ai_policies)}')
    for p in usa_ai_policies:
        print(f'  - Country: {p.get("country")}, Area: {p.get("policy_area")}, Name: {p.get("policy_name", "Unknown")[:50]}...')

if __name__ == "__main__":
    asyncio.run(debug_policies())
