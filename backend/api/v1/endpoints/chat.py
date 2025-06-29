"""
Chat/Chatbot endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from models.chat import ChatRequest
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Enhanced chat endpoint with user context"""
    try:
        # Import the chatbot functions
        from chatbot import chat_endpoint as chatbot_chat_endpoint
        
        # Add user context to the request
        request_dict = request.dict()
        request_dict["user_id"] = str(current_user["_id"])
        
        # Call the chatbot
        response = await chatbot_chat_endpoint(ChatRequest(**request_dict))
        return response
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    """Get user's conversation history"""
    try:
        from chatbot import get_conversations_endpoint
        
        user_id = str(current_user["_id"])
        response = await get_conversations_endpoint(user_id)
        return response
    
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific conversation"""
    try:
        from chatbot import get_conversation_endpoint
        
        response = await get_conversation_endpoint(conversation_id)
        return response
    
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete specific conversation"""
    try:
        from chatbot import delete_conversation_endpoint
        
        response = await delete_conversation_endpoint(conversation_id)
        return response
    
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@router.get("/policy-search")
async def policy_search(q: str):
    """Enhanced policy search for chatbot sidebar"""
    try:
        from chatbot import policy_search_endpoint
        
        response = await policy_search_endpoint(q)
        return response
    except Exception as e:
        logger.error(f"Policy search error: {str(e)}")
        return {"policies": []}

@router.get("/debug/chatbot-test")
async def test_chatbot():
    """Test chatbot functionality"""
    try:
        from chatbot import chatbot_instance
        
        if not chatbot_instance:
            return {"error": "Chatbot not initialized"}
        
        # Test basic searches
        test_results = {}
        
        # Test country search
        countries = await chatbot_instance.get_countries_list()
        test_results["countries_count"] = len(countries)
        test_results["sample_countries"] = countries[:5]
        
        # Test policy areas
        areas = await chatbot_instance.get_policy_areas_list()
        test_results["areas_count"] = len(areas)
        test_results["sample_areas"] = areas[:5]
        
        # Test policy search
        if countries:
            first_country = countries[0]
            policies = await chatbot_instance.search_policies_by_country(first_country)
            test_results["sample_country_policies"] = len(policies)
            test_results["sample_country"] = first_country
        
        return {
            "chatbot_status": "initialized",
            "database_connection": "ok",
            "test_results": test_results
        }
    
    except Exception as e:
        logger.error(f"Chatbot test error: {str(e)}")
        return {"error": str(e)}
