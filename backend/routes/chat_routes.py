from fastapi import APIRouter, HTTPException, Query, Depends
from ..models.chat_models import ChatRequest
from ..chatbot.chatbot import chatbot_instance
from ..database.connection import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("")
async def chat(request: ChatRequest):
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    return await chatbot_instance.chat(request)

@router.get("/conversations")
async def get_conversations(limit: int = Query(20, ge=1, le=100)):
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    return await chatbot_instance.get_user_conversations(limit)

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    messages = await chatbot_instance.get_conversation_history(conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}

@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    if not chatbot_instance:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    success = await chatbot_instance.delete_conversation(conversation_id)
    return {"success": success, "message": "Conversation deleted" if success else "Conversation not found"}

@router.get("/policy-search")
async def search_policies_for_chat(
    q: str = Query(..., min_length=1),
    db=Depends(get_db)
):
    try:
        search_terms = q.lower().split()
        search_conditions = []
        
        for term in search_terms:
            search_conditions.extend([
                {"policyName": {"$regex": term, "$options": "i"}},
                {"policyDescription": {"$regex": term, "$options": "i"}},
                {"country": {"$regex": term, "$options": "i"}},
                {"policyArea": {"$regex": term, "$options": "i"}}
            ])
        
        if search_conditions:
            cursor = db.master_policies.find(
                {
                    "$and": [
                        {"master_status": {"$ne": "deleted"}},
                        {"$or": search_conditions}
                    ]
                }
            ).limit(10)
            
            policies = []
            async for policy in cursor:
                policies.append({
                    "id": str(policy["_id"]),
                    "country": policy.get("country", ""),
                    "name": policy.get("policyName", ""),
                    "area": policy.get("policyArea", ""),
                    "description": policy.get("policyDescription", "")[:200] + "..." if len(policy.get("policyDescription", "")) > 200 else policy.get("policyDescription", ""),
                    "year": policy.get("implementation", {}).get("deploymentYear", "N/A")
                })
            
            return {"policies": policies, "total": len(policies)}
        
        return {"policies": [], "total": 0}
    except Exception as e:
        raise HTTPException