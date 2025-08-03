#!/usr/bin/env python3
"""
Test the improved non-policy question handling
"""
import asyncio
import sys
sys.path.append('.')

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_non_policy_questions():
    """Test that irrelevant questions are properly redirected"""
    print("🧪 Testing Non-Policy Question Handling...")
    
    try:
        irrelevant_questions = [
            "What is the rainbow color?",
            "What's the weather today?",
            "How do I cook pasta?",
            "What's 2+2?",
            "Tell me a joke",
            "What's the capital of France?",
            "How do I lose weight?",
            "What's the latest movie?",
            "What colors are in a rainbow?",
            "How tall is Mount Everest?"
        ]
        
        for i, question in enumerate(irrelevant_questions, 1):
            print(f"\n{i}️⃣ Testing: '{question}'")
            print("-" * 60)
            
            request = ChatRequest(message=question)
            response = await enhanced_chatbot_service.chat(request)
            
            if "I'm sorry, but as an AI Policy Expert Assistant" in response.response:
                print("✅ CORRECTLY REDIRECTED")
            else:
                print("❌ INCORRECTLY ANSWERED")
            
            print(f"Response: {response.response[:200]}...")
            print("-" * 60)
        
        print("\n🎯 Now testing VALID policy questions...")
        
        valid_questions = [
            "What AI policies does United States have?",
            "Tell me about Bangladesh digital policies",
            "How do countries handle AI safety?"
        ]
        
        for i, question in enumerate(valid_questions, 1):
            print(f"\n{i}️⃣ Testing: '{question}'")
            print("-" * 60)
            
            request = ChatRequest(message=question)
            response = await enhanced_chatbot_service.chat(request)
            
            if "I'm sorry, but as an AI Policy Expert Assistant" in response.response:
                print("❌ INCORRECTLY REDIRECTED (should answer)")
            else:
                print("✅ CORRECTLY ANSWERED")
            
            print(f"Response: {response.response[:200]}...")
            print("-" * 60)
        
        print("\n🎉 Testing completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_non_policy_questions())
