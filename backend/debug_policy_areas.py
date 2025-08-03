#!/usr/bin/env python3
"""
Debug policy areas to understand the naming conventions
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chatbot_service_enhanced import EnhancedChatbotService

async def debug_policy_areas():
    service = EnhancedChatbotService()
    await service._update_cache()
    
    # Check policy areas for United States
    usa_policies = [p for p in service.policy_cache if p.get('country') and 'united states' in p['country'].lower()]
    print(f'USA policies: {len(usa_policies)}')
    
    # Group by policy area
    usa_areas = {}
    for p in usa_policies:
        area = p.get('policy_area', 'Unknown')
        if area not in usa_areas:
            usa_areas[area] = []
        usa_areas[area].append(p.get('policy_name', 'Unknown'))
    
    print('\nUSA policies by area:')
    for area, policies in usa_areas.items():
        print(f'  {area}: {len(policies)} policies')
        for policy_name in policies:
            print(f'    - {policy_name[:60]}...')
    
    # Check all unique policy areas across all countries
    print('\nAll unique policy areas:')
    all_areas = set(p.get('policy_area', 'Unknown') for p in service.policy_cache if p.get('policy_area'))
    for area in sorted(all_areas):
        count = len([p for p in service.policy_cache if p.get('policy_area') == area])
        print(f'  {area}: {count} policies')

if __name__ == "__main__":
    asyncio.run(debug_policy_areas())
