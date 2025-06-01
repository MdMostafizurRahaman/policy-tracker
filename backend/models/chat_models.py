from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel
from .base_models import BaseDBModel

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime

class ChatConversation(BaseDBModel):
    conversation_id: str
    messages: List[ChatMessage]