"""
Chat/AI assistant routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from models.chat import ChatRequest, ChatResponse, PolicySearchRequest
from services.chatbot_service import get_chatbot_service
from routers.auth import get_current_user
from models.user import UserResponse
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

router = APIRouter()
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[UserResponse] = Depends(get_current_user),
    chatbot_service = Depends(get_chatbot_service)
):
    """Chat with AI policy assistant"""
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Generate response
        response = await chatbot_service.generate_response(request.message, request.context)
        
        # Save conversation
        user_id = current_user.id if current_user else None
        await chatbot_service.save_conversation(
            conversation_id, 
            request.message, 
            response, 
            user_id
        )
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

@router.get("/conversations")
async def get_user_conversations(
    current_user: UserResponse = Depends(get_current_user),
    chatbot_service = Depends(get_chatbot_service),
    limit: int = 10
):
    """Get user's conversations"""
    try:
        conversations = await chatbot_service.get_user_conversations(current_user.id, limit)
        return {"conversations": conversations}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations"
        )

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_current_user),
    chatbot_service = Depends(get_chatbot_service)
):
    """Get conversation by ID"""
    try:
        conversation = await chatbot_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    chatbot_service = Depends(get_chatbot_service)
):
    """Delete conversation"""
    try:
        success = await chatbot_service.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )

@router.post("/search-policies")
async def search_policies(
    request: PolicySearchRequest,
    chatbot_service = Depends(get_chatbot_service)
):
    """Search policies for chat context"""
    try:
        policies = await chatbot_service.search_policies(request.query, request.limit)
        return {"policies": policies}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy search failed"
        )
