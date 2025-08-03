#!/usr/bin/env python3
"""
Test the enhanced chatbot with your policy data training
"""
import asyncio
import sys
sys.path.append('.')

from services.chatbot_service_enhanced import enhanced_chatbot_service
from models.chat import ChatRequest

async def test_enhanced_chatbot():
    """Test the enhanced chatbot with your data training"""
    print("🚀 Testing Enhanced Chatbot with Your Policy Data Training...")
    
    try:
        # Generate training data first
        print("\n📚 Generating training data from your policy database...")
        training_file = await enhanced_chatbot_service.export_training_data_for_finetuning()
        if training_file:
            print(f"✅ Training data exported to: {training_file}")
        
        print("\n🧪 Testing Enhanced Responses...")
        
        test_queries = [
            "What AI policies does United States have?",
            "Compare AI policies between USA and Canada", 
            "Tell me about Bangladesh digital policies",
            "What are the key differences in AI safety approaches globally?",
            "How do different countries handle AI ethics?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}️⃣ Testing: '{query}'")
            print("-" * 60)
            
            request = ChatRequest(message=query)
            response = await enhanced_chatbot_service.chat(request)
            
            print(f"🤖 Response: {response.response}")
            print("-" * 60)
        
        print("\n🎉 Enhanced chatbot testing completed!")
        print("\n💡 The model is now using your policy database as training context to provide expert-level responses!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_chatbot())
