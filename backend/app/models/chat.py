"""
Chat-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., regex="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime

class ChatConversation(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

class PolicySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: Optional[int] = Field(5, ge=1, le=20)
