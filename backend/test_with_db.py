#!/usr/bin/env python3
"""
Test chatbot with proper database initialization
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent))

from config.database import database
from services.chatbot_service import chatbot_service

async def test_with_database():
    """Test chatbot with proper database connection"""
    print("Initializing database connection...")
    
    # Connect to database
    connected = await database.connect()
    if not connected:
        print("❌ Failed to connect to database")
        return
    
    print("✅ Database connected successfully")
    
    # Test with a simple country query
    test_query = "United States"
    print(f"\nTesting query: '{test_query}'")
    
    # Get the response
    response = await chatbot_service.process_query(test_query)
    
    print(f"\nResponse type: {type(response)}")
    print(f"Response length: {len(response)}")
    print(f"\nFirst 200 characters:")
    print(response[:200])
    print("\n" + "="*50)
    print("FULL RESPONSE:")
    print("="*50)
    print(response)
    
    # Check if it contains structured formatting
    if "🏛️" in response or "•" in response or "**" in response:
        print("\n❌ ISSUE: Response contains structured formatting!")
        print("This should be natural conversational text.")
    else:
        print("\n✅ Good: Response appears to be natural text.")
    
    # Check if AI was called
    if "No AI policies found" in response:
        print("❌ ISSUE: Falling back to 'No policies found' message")
        print("This suggests either no policies in DB or AI not being called")
    
    # Disconnect from database
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(test_with_database())
