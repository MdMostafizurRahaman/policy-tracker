from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from ..models.chat_models import ChatConversation

async def get_conversation(collection: AsyncIOMotorCollection, conversation_id: str) -> Optional[ChatConversation]:
    try:
        conversation_doc = await collection.find_one({"conversation_id": conversation_id})
        if conversation_doc:
            return ChatConversation(**conversation_doc)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_conversation(collection: AsyncIOMotorCollection, conversation: ChatConversation):
    try:
        await collection.update_one(
            {"conversation_id": conversation.conversation_id},
            {"$set": conversation.dict()},
            upsert=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_conversations(collection: AsyncIOMotorCollection, limit: int = 20) -> List[Dict]:
    try:
        cursor = collection.find().sort("updated_at", -1).limit(limit)
        conversations = []
        async for conv in cursor:
            last_message = conv["messages"][-1] if conv["messages"] else None
            conversations.append({
                "conversation_id": conv["conversation_id"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "message_count": len(conv["messages"]),
                "last_message": last_message["content"][:100] + "..." if last_message and len(last_message["content"]) > 100 else last_message["content"] if last_message else ""
            })
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))