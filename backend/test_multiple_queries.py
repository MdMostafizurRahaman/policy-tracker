#!/usr/bin/env python3
"""
Test multiple queries to ensure consistent natural responses
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent))

from config.database import database
from services.chatbot_service import chatbot_service

async def test_multiple_queries():
    """Test multiple queries to ensure consistent natural responses"""
    print("Initializing database connection...")
    
    # Connect to database
    connected = await database.connect()
    if not connected:
        print("❌ Failed to connect to database")
        return
    
    print("✅ Database connected successfully")
    
    # Test queries
    test_queries = [
        "United States",
        "AI Safety",
        "European Union",
        "What AI policies exist?",
        "Tell me about data protection policies"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {query}")
        print('='*60)
        
        response = await chatbot_service.process_query(query)
        
        # Check response characteristics
        print(f"Response length: {len(response)}")
        
        # Check for problematic formatting
        issues = []
        if "🏛️" in response:
            issues.append("Contains building emoji")
        if response.count("•") > 2:
            issues.append("Contains bullet points")
        if "**" in response:
            issues.append("Contains markdown bold")
        if response.startswith("No AI policies found"):
            issues.append("Fallback to 'No policies found'")
        
        if issues:
            print(f"❌ ISSUES: {', '.join(issues)}")
        else:
            print("✅ GOOD: Natural conversational response")
        
        print(f"\nFirst 150 chars: {response[:150]}...")
        
        # Print full response for detailed inspection
        if len(issues) > 0 or i == 1:  # Show first one and any problematic ones
            print(f"\nFULL RESPONSE:")
            print("-" * 40)
            print(response)
    
    # Disconnect from database
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(test_multiple_queries())
