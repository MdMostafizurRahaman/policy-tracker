#!/usr/bin/env python3
"""
Debug the complete comparison flow
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chatbot_service_enhanced import EnhancedChatbotService
from models.chat_dynamodb import ChatMessage
from datetime import datetime

async def debug_comparison_flow():
    service = EnhancedChatbotService()
    await service._update_cache()
    
    # Mock conversation history
    mock_history = [
        ChatMessage(
            message_type="user",
            content="Tell me about USA AI Safety policy",
            created_at=datetime.utcnow().isoformat()
        ),
        ChatMessage(
            message_type="ai", 
            content="In the United States, there are several AI Safety policies...",
            created_at=datetime.utcnow().isoformat()
        )
    ]
    
    # Extract context
    message = "difference between usa ai policy and russia ai policy"
    context = service._extract_conversation_context(mock_history, message)
    print(f"Context: {context}")
    
    # Test country detection in comparison
    mentioned_countries = []
    message_lower = message.lower()
    
    # Start with countries from conversation context
    if context and context.get('mentioned_countries'):
        for country in context['mentioned_countries']:
            if country not in mentioned_countries:
                mentioned_countries.append(country)
    
    # Enhanced country detection
    for country in service.countries_cache:
        if country:
            country_lower = country.lower()
            if country_lower in message_lower:
                if country not in mentioned_countries:
                    mentioned_countries.append(country)
            elif country_lower == "united states" and any(term in message_lower for term in ["usa", "us ", " us", "america", "american"]):
                if country not in mentioned_countries:
                    mentioned_countries.append(country)
    
    print(f"Detected countries: {mentioned_countries}")
    
    # Get policies for mentioned countries
    comparison_data = {}
    for country in mentioned_countries[:3]:
        country_policies = [p for p in service.policy_cache 
                          if p.get('country') and p['country'].lower() == country.lower()]
        
        print(f"Raw policies for {country}: {len(country_policies)}")
        
        # Apply context-based filtering if we have AI Safety in context
        if context and context.get('mentioned_areas'):
            area_filtered_policies = []
            for policy in country_policies:
                policy_area = policy.get('policy_area', '').lower()
                policy_name = policy.get('policy_name', '').lower()
                policy_desc = policy.get('policy_description', '').lower()
                
                for mentioned_area in context['mentioned_areas']:
                    mentioned_area_lower = mentioned_area.lower()
                    if (mentioned_area_lower in policy_area or
                        mentioned_area_lower in policy_name or
                        mentioned_area_lower in policy_desc or
                        (mentioned_area == "AI Safety" and any(term in policy_name or term in policy_desc 
                            for term in ["ai", "artificial intelligence", "machine learning", "automation"]))):
                        area_filtered_policies.append(policy)
                        print(f"  Matched: {policy.get('policy_name', 'Unknown')[:50]}...")
                        break
            
            if area_filtered_policies:
                country_policies = area_filtered_policies
                
        print(f"Filtered policies for {country}: {len(country_policies)}")
        comparison_data[country] = country_policies
    
    print(f"Final comparison data: {[(k, len(v)) for k, v in comparison_data.items()]}")
    
    # Check if there's sufficient data
    countries_with_data = [country for country, policies in comparison_data.items() if policies]
    countries_without_data = [country for country, policies in comparison_data.items() if not policies]
    
    print(f"Countries with data: {countries_with_data}")
    print(f"Countries without data: {countries_without_data}")

if __name__ == "__main__":
    asyncio.run(debug_comparison_flow())
