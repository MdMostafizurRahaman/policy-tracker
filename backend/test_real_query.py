#!/usr/bin/env python3
"""
Test real policy query to see the exact output format
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent))

from services.chatbot_service import chatbot_service

async def test_real_query():
    """Test a real policy query"""
    print("Testing real policy query...")
    
    # Test with a simple country query
    test_query = "United States"
    print(f"\nQuery: '{test_query}'")
    
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

if __name__ == "__main__":
    asyncio.run(test_real_query())
