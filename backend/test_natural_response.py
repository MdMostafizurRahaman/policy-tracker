"""
Test the updated chatbot response format
"""
import asyncio
import os
import json

# Mock chatbot for testing the prompt format
class TestChatbot:
    def __init__(self):
        self.groq_api_key = "test_key"  # Mock API key
    
    def create_structured_prompt(self, user_query: str, data_context: list) -> str:
        """Create structured prompt similar to digital wellbeing format"""
        return f"""
You are an AI policy database analyst. Answer the user's question about AI policies using the provided dataset in a natural, conversational way like ChatGPT or Claude.

User Query: "{user_query}"

Available Policy Data Context:
{json.dumps(data_context, indent=2) if data_context else "No specific policies found, but provide guidance on available data in our AI policy database."}

Guidelines:
1. Answer in a natural, conversational tone like a knowledgeable assistant
2. Provide specific policy names, countries, policy areas, and comparisons when relevant
3. If the question cannot be answered with the available data, explain what data would be needed
4. Be conversational and friendly while being precise with policy information
5. Include relevant insights about AI governance and policy trends naturally in the conversation
6. Focus only on AI policy-related information from our database
7. Write like you're having a conversation with a colleague, not like a formal report
8. Use natural language flow, not bullet points or structured lists in the main answer

Respond in JSON format:
{{
    "answer": "natural conversational response as if you're ChatGPT or Claude explaining the policies (plain text, no HTML, no bullet points in main answer - write naturally)",
    "relevant_policies": {{"key policies and data points that support the answer"}},
    "additional_insights": ["insight1 about AI policy trends", "insight2 about governance patterns"],
    "suggestions": ["suggestion for further policy exploration", "related policy areas to explore"]
}}
"""

# Mock Iran policies data similar to what was shown
iran_policies = [
    {
        "policyName": "iran",
        "country": "Iran",
        "policyArea": "AI Safety",
        "policyDescription": ""
    },
    {
        "policyName": "Cybersecurity",
        "country": "Iran",
        "policyArea": "cyber-safety",
        "policyDescription": "Iran is the best"
    },
    {
        "policyName": "Digital",
        "country": "Iran",
        "policyArea": "digital-education",
        "policyDescription": "hejhshjcbshjdbc sjcgsjhd hjsdhj sfvbkjshv hjuh fdhvisvhja dc"
    },
    {
        "policyName": "Iran DisInformation",
        "country": "Iran",
        "policyArea": "disinformation",
        "policyDescription": "Iran has taken new steps to avoid misinformation"
    }
]

def show_expected_ai_response():
    """Show what the AI response should look like"""
    chatbot = TestChatbot()
    
    user_query = "Iran"
    prompt = chatbot.create_structured_prompt(user_query, iran_policies)
    
    print("=== CURRENT ISSUE ===")
    print("The chatbot is returning structured data format instead of natural conversation")
    print()
    
    print("=== EXPECTED AI RESPONSE EXAMPLE ===")
    print("Query: 'Iran'")
    print()
    print("Expected Natural Response:")
    print("-" * 50)
    
    expected_response = """Iran has implemented several AI policies across different areas. The country has established policies focusing on AI Safety, cybersecurity, digital education, and combating disinformation.

Their cybersecurity initiative emphasizes Iran's capabilities in this domain, while their digital education policy aims to integrate AI technologies into educational frameworks. Additionally, Iran has taken specific steps to address misinformation through their anti-disinformation policy.

The policies span from 2025 with their AI Safety framework to ongoing initiatives in cybersecurity and digital education. This shows Iran's commitment to developing a comprehensive AI governance approach that addresses both technological advancement and social responsibility.

What's particularly interesting is their focus on disinformation - this reflects a growing global trend where countries are recognizing the importance of AI in information integrity and media literacy."""
    
    print(expected_response)
    print()
    print("=== CURRENT PROBLEMATIC OUTPUT ===")
    print("Found 4 AI Policies for country \"Iran\"")
    print("🏛️ Iran (4 policies)")
    print("========================")
    print("📄 iran")
    print("Area: AI Safety")
    print("Year: 2025")
    print("Status: approved")
    print("Description:")
    print("...")
    print()
    
    print("=== SOLUTION ===")
    print("The AI should always be called for policy queries to provide natural responses")
    print("The structured format should only be used as fallback when AI is unavailable")
    print()
    
    print("=== UPDATED PROMPT ===")
    print("Key changes made to prompt:")
    print("- Emphasized natural conversational tone")
    print("- Specified 'like ChatGPT or Claude'")
    print("- Added 'no bullet points in main answer'")
    print("- Emphasized natural language flow")
    print()

if __name__ == "__main__":
    show_expected_ai_response()
