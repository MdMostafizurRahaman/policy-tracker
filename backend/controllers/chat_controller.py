"""
Chat Controller
Handles HTTP requests for chatbot and conversation operations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from models.chat import ChatRequest, ChatResponse, ChatMessage
from services.chatbot_service_dynamodb import chatbot_service
from utils.helpers import convert_objectid
from middleware.auth import get_optional_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_optional_user)
):
    """Chat with the AI assistant for policy queries (works for both authenticated and public access)"""
    try:
        response = await chatbot_service.chat(request)
        return response
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.post("/public", response_model=ChatResponse)
async def public_chat(request: ChatRequest):
    """Public chat endpoint that doesn't require authentication"""
    try:
        response = await chatbot_service.chat(request)
        return response
    except Exception as e:
        logger.error(f"Public chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_optional_user)
):
    """Get conversation history endpoint"""
    try:
        messages = await chatbot_service.get_conversation_history(conversation_id)
        return {
            "conversation_id": conversation_id, 
            "messages": [convert_objectid(msg.dict()) for msg in messages]
        }
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_optional_user)
):
    """Delete conversation endpoint"""
    try:
        success = await chatbot_service.delete_conversation(conversation_id)
        return {
            "success": success, 
            "message": "Conversation deleted" if success else "Conversation not found"
        }
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")


@router.get("/conversations")
async def get_conversations(
    limit: int = 20,
    current_user: dict = Depends(get_optional_user)
):
    """Get conversations list endpoint (works for both authenticated and public access)"""
    try:
        conversations = await chatbot_service.get_user_conversations(limit)
        return {"conversations": convert_objectid(conversations)}
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")


@router.get("/policy-search")
async def policy_search(
    q: str,
    current_user: dict = Depends(get_optional_user)
):
    """Enhanced policy search endpoint for the sidebar"""
    try:
        policies = await chatbot_service.search_policies(q)
        return {"policies": policies}
    except Exception as e:
        logger.error(f"Policy search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in policy search: {str(e)}")


@router.get("/debug/test")
async def chatbot_test():
    """Debug endpoint to test chatbot functionality"""
    try:
        # Test basic functionality
        test_request = ChatRequest(message="help")
        response = await chatbot_service.chat(test_request)
        
        return {
            "status": "success",
            "message": "Chatbot is working",
            "test_response": response.response[:100] + "..." if len(response.response) > 100 else response.response
        }
    except Exception as e:
        logger.error(f"Chatbot test error: {str(e)}")
        return {
            "status": "error",
            "message": f"Chatbot test failed: {str(e)}"
        }