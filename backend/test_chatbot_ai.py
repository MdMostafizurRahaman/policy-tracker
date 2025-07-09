"""
Test script for the updated chatbot service with AI integration
"""
import asyncio
import os
import sys
import json

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chatbot_service import ChatbotService

async def test_chatbot_service():
    """Test the chatbot service with sample queries"""
    
    chatbot = ChatbotService()
    
    # Test queries
    test_queries = [
        "Hello",
        "What AI policies does the United States have?",
        "Tell me about AI Safety policies",
        "Help",
        "Countries",
        "Compare AI policies between US and EU"
    ]
    
    print("Testing Chatbot Service with AI Integration")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 30)
        
        try:
            response = await chatbot.process_query(query)
            
            # If response is HTML, show a truncated version
            if response.startswith("<div"):
                print("Response: [HTML Response Generated]")
                print(f"Length: {len(response)} characters")
                # Extract title from response
                if '<span class="policy-title">' in response:
                    start = response.find('<span class="policy-title">') + len('<span class="policy-title">')
                    end = response.find('</span>', start)
                    title = response[start:end]
                    print(f"Title: {title}")
            else:
                print(f"Response: {response}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        print()
    
    # Test AI analysis if enabled
    if chatbot.is_ai_enabled():
        print("\n" + "=" * 50)
        print("AI Analysis Test")
        print("=" * 50)
        
        sample_policies = [
            {
                "policyName": "National AI Strategy",
                "country": "United States",
                "policyArea": "AI Safety",
                "policyDescription": "Comprehensive framework for AI development and deployment with focus on safety and ethics."
            },
            {
                "policyName": "AI Act",
                "country": "European Union",
                "policyArea": "AI Regulation",
                "policyDescription": "Regulatory framework for artificial intelligence applications with risk-based approach."
            }
        ]
        
        try:
            ai_response = await chatbot.analyze_query_with_ai(
                "Compare AI safety approaches between US and EU",
                sample_policies
            )
            
            if ai_response:
                print("AI Analysis Response Generated Successfully")
                print(f"Length: {len(ai_response)} characters")
            else:
                print("AI Analysis returned None")
                
        except Exception as e:
            print(f"AI Analysis Error: {e}")
    else:
        print("\nAI Analysis not enabled (GROQ_API_KEY not found)")

if __name__ == "__main__":
    asyncio.run(test_chatbot_service())
