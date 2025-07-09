"""
Test script to demonstrate the AI chatbot responses without database
"""
import asyncio
import os
import json

# Mock policy data for testing
mock_policies = [
    {
        "policyName": "National AI Strategy 2024",
        "country": "United States",
        "policyArea": "AI Safety",
        "policyDescription": "A comprehensive framework for ensuring AI development prioritizes safety, ethics, and American competitiveness while fostering innovation across all sectors."
    },
    {
        "policyName": "Artificial Intelligence Act",
        "country": "European Union",
        "policyArea": "AI Regulation",
        "policyDescription": "The world's first comprehensive AI regulation establishing a risk-based approach to AI governance with strict requirements for high-risk AI systems."
    },
    {
        "policyName": "Digital Education Framework",
        "country": "Germany",
        "policyArea": "Digital Education",
        "policyDescription": "A national strategy to integrate AI and digital technologies into education systems while ensuring data privacy and ethical AI use in learning environments."
    }
]

class MockChatbotService:
    """Mock chatbot service for testing AI responses"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
    
    def create_structured_prompt(self, user_query: str, data_context: list) -> str:
        """Create structured prompt similar to digital wellbeing format"""
        return f"""
You are an AI policy database analyst. Answer the user's question about AI policies using the provided dataset.

User Query: "{user_query}"

Available Policy Data Context:
{json.dumps(data_context, indent=2)}

Guidelines:
1. Answer the question accurately based on the policy data
2. Provide specific policy names, countries, policy areas, and comparisons when relevant
3. If the question cannot be answered with the available data, explain what data would be needed
4. Be conversational but precise with policy information
5. Include relevant insights about AI governance and policy trends
6. Focus only on AI policy-related information from our database
7. Provide natural, conversational responses without HTML styling or formatting

Respond in JSON format:
{{
    "answer": "detailed conversational answer to the user's question with specific policy information (plain text, no HTML)",
    "relevant_policies": {{"key policies and data points that support the answer"}},
    "additional_insights": ["insight1 about AI policy trends", "insight2 about governance patterns"],
    "suggestions": ["suggestion for further policy exploration", "related policy areas to explore"]
}}
"""

async def test_ai_responses():
    """Test AI responses with mock data"""
    print("Testing AI Chatbot Responses")
    print("=" * 40)
    
    service = MockChatbotService()
    
    # Test queries
    test_queries = [
        "Compare AI policies between US and EU",
        "What are the main differences in AI safety approaches?",
        "Tell me about digital education policies",
        "Which countries have the most comprehensive AI regulations?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 30)
        
        # Create the prompt
        prompt = service.create_structured_prompt(query, mock_policies)
        
        # Show what would be sent to AI
        print("Structured Prompt Created:")
        print("✓ User Query:", query)
        print("✓ Policy Context: 3 sample policies provided")
        print("✓ Guidelines: 7 guidelines for natural conversational response")
        print("✓ Expected JSON Response Format:")
        print("  - answer: conversational response (plain text)")
        print("  - relevant_policies: key supporting data")
        print("  - additional_insights: AI governance trends")
        print("  - suggestions: exploration recommendations")
        
        # Mock AI response example
        if "compare" in query.lower() and "us" in query.lower() and "eu" in query.lower():
            mock_response = {
                "answer": "Based on the available policy data, the US and EU take distinctly different approaches to AI governance. The US focuses on maintaining competitive advantage through the National AI Strategy 2024, which emphasizes safety and ethics while fostering innovation across all sectors. In contrast, the EU has implemented the world's first comprehensive AI regulation - the Artificial Intelligence Act - which takes a strict risk-based regulatory approach with specific requirements for high-risk AI systems. The US approach is more innovation-friendly and market-driven, while the EU prioritizes regulatory compliance and consumer protection.",
                "relevant_policies": {
                    "US Policy": "National AI Strategy 2024 - focuses on safety, ethics, and competitiveness",
                    "EU Policy": "Artificial Intelligence Act - comprehensive risk-based regulation"
                },
                "additional_insights": [
                    "The US emphasizes maintaining global AI leadership through innovation",
                    "The EU sets global standards through comprehensive regulatory frameworks",
                    "Both regions prioritize AI safety but through different mechanisms"
                ],
                "suggestions": [
                    "Explore specific AI safety frameworks in both regions",
                    "Compare implementation timelines and compliance requirements",
                    "Look into sector-specific AI policies in healthcare and finance"
                ]
            }
            
            print("\nMock AI Response:")
            print("Answer:", mock_response["answer"])
            print("\nRelevant Policies:")
            for key, value in mock_response["relevant_policies"].items():
                print(f"• {key}: {value}")
            print("\nAdditional Insights:")
            for insight in mock_response["additional_insights"]:
                print(f"• {insight}")
            print("\nSuggestions:")
            for suggestion in mock_response["suggestions"]:
                print(f"• {suggestion}")
        else:
            print("\nMock AI Response: [Would generate contextual response based on query and data]")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_ai_responses())
