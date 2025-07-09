#!/usr/bin/env python3
"""
Test the cleaned up responses to ensure no UI formatting remains
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent))

from config.database import database
from services.chatbot_service import chatbot_service

async def test_clean_responses():
    """Test responses to ensure no UI formatting"""
    print("Initializing database connection...")
    
    # Connect to database
    connected = await database.connect()
    if not connected:
        print("❌ Failed to connect to database")
        return
    
    print("✅ Database connected successfully")
    
    # Test the commands that might show UI formatting
    test_queries = [
        "countries",
        "areas", 
        "nonexistent policy query"  # This should trigger the fallback
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"TEST {i}: {query}")
        print('='*50)
        
        response = await chatbot_service.process_query(query)
        
        # Check for UI formatting
        issues = []
        if "🏛️" in response:
            issues.append("Contains building emoji")
        if "💡" in response:
            issues.append("Contains lightbulb emoji")
        if "•" in response:
            issues.append("Contains bullet points")
        if "📄" in response:
            issues.append("Contains file emoji")
        
        if issues:
            print(f"❌ ISSUES: {', '.join(issues)}")
        else:
            print("✅ CLEAN: No UI formatting detected")
        
        print(f"Response length: {len(response)}")
        print(f"First 150 chars: {response[:150]}...")
        
        # Show problem areas if any
        if issues:
            print(f"\nFull response:")
            print(response)
    
    # Disconnect from database
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(test_clean_responses())
