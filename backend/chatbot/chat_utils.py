from typing import List, Dict, Optional
from datetime import datetime
import google.generativeai as genai
import asyncio

async def generate_gemini_response(
    model: genai.GenerativeModel,
    system_prompt: str,
    conversation_history: List[Dict],
    user_message: str,
    context: str = ""
) -> str:
    """
    Generate a response using Gemini API with conversation history and context
    """
    try:
        # Prepare the full prompt with context
        full_prompt = f"{system_prompt}\n\n{context}" if context else system_prompt
        
        # Prepare chat history for Gemini
        chat_history = []
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            if msg["role"] == "user":
                chat_history.append({"role": "user", "parts": [msg["content"]]})
            else:
                chat_history.append({"role": "model", "parts": [msg["content"]]})
        
        # Start chat with history
        chat = model.start_chat(history=chat_history)
        
        # Generate response
        response = await asyncio.to_thread(
            chat.send_message,
            f"{full_prompt}\n\nUser: {user_message}"
        )
        
        return response.text
    except Exception as e:
        raise Exception(f"Error generating Gemini response: {str(e)}")

def format_policy_context(policies: List[Dict]) -> str:
    """
    Format policy data into context string for the chatbot
    """
    if not policies:
        return ""
    
    context = "\n\nRelevant policies from the database:\n"
    for policy in policies:
        context += (
            f"- {policy['country']}: {policy['name']} "
            f"({policy['area']}, {policy['year']})\n  "
            f"{policy['description']}\n\n"
        )
    return context

def create_new_conversation(conversation_id: str) -> Dict:
    """
    Create a new conversation structure
    """
    now = datetime.utcnow()
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "created_at": now,
        "updated_at": now
    }