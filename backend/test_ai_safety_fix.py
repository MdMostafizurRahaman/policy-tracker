#!/usr/bin/env python3
"""
Test the updated chatbot with AI Safety query that previously failed
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent))

from config.database import database
from services.chatbot_service import chatbot_service

async def test_ai_safety_query():
    """Test the AI Safety query that previously caused token overflow"""
    print("Initializing database connection...")
    
    # Connect to database
    connected = await database.connect()
    if not connected:
        print("❌ Failed to connect to database")
        return
    
    print("✅ Database connected successfully")
    
    # Test the problematic query
    test_query = "AI Safety"
    print(f"\nTesting query: '{test_query}'")
    print("This query previously failed due to too many policies (182 found)")
    print("Now it should limit the data sent to AI and provide a natural response...")
    
    # Get the response
    response = await chatbot_service.process_query(test_query)
    
    print(f"\nResponse type: {type(response)}")
    print(f"Response length: {len(response)}")
    
    # Check for problematic formatting
    issues = []
    if "🏛️" in response:
        issues.append("Contains building emoji")
    if response.count("•") > 3:  # Allow a few bullets in suggestions, but not in main answer
        issues.append("Contains many bullet points")
    if response.startswith("Found") and "policies" in response[:50]:
        issues.append("Shows structured format instead of natural response")
    
    if issues:
        print(f"❌ ISSUES: {', '.join(issues)}")
        print("\nFirst 300 characters:")
        print(response[:300])
        if "Found" in response[:50]:
            print("\n⚠️  This is the old structured format, not the natural AI response!")
    else:
        print("✅ GOOD: Natural conversational response")
        print(f"\nFirst 200 characters:")
        print(response[:200])
        print("\n" + "="*60)
        print("FULL RESPONSE:")
        print("="*60)
        print(response)
    
    # Disconnect from database
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(test_ai_safety_query())
