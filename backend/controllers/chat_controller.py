"""
Chat Controller
Handles HTTP requests for chatbot and conversation operations
"""
from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_optional_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/")
async def chat(
    chat_data: dict,
    current_user: dict = Depends(get_optional_user)
):
    """Chat with the AI assistant"""
    try:
        # Import chatbot functionality
        from services.chatbot_service_core import chat_endpoint
        
        # Convert to the expected format
        class ChatRequest:
            def __init__(self, message, conversation_id=None):
                self.message = message
                self.conversation_id = conversation_id
        
        request = ChatRequest(
            message=chat_data.get("message", ""),
            conversation_id=chat_data.get("conversation_id")
        )
        
        # Call the chatbot endpoint
        return await chat_endpoint(request)
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_optional_user)
):
    """Get a specific conversation"""
    try:
        from services.chatbot_service_core import get_conversation_endpoint
        return await get_conversation_endpoint(conversation_id)
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_optional_user)
):
    """Delete a conversation"""
    try:
        from services.chatbot_service_core import delete_conversation_endpoint
        return await delete_conversation_endpoint(conversation_id)
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@router.get("/conversations")
async def get_conversations(
    current_user: dict = Depends(get_optional_user)
):
    """Get all conversations"""
    try:
        from services.chatbot_service_core import get_conversations_endpoint
        return await get_conversations_endpoint()
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/policy-search")
async def policy_search(
    query: str = "",
    current_user: dict = Depends(get_optional_user)
):
    """Search policies using AI"""
    try:
        from services.chatbot_service_core import policy_search_endpoint
        
        class PolicySearchRequest:
            def __init__(self, query):
                self.query = query
        
        request = PolicySearchRequest(query)
        return await policy_search_endpoint(request)
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    except Exception as e:
        logger.error(f"Policy search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Policy search failed: {str(e)}")
