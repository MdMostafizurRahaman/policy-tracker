"""
Pydantic models for chatbot interactions.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: Optional[datetime] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)

class ChatConversation(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

class ConversationResponse(BaseModel):
    id: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
