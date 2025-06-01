from typing import Dict, List, Optional
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from ..models.policy_models import FormSubmission, PolicyInitiative

async def update_submission_status(
    temp_collection: AsyncIOMotorCollection,
    submission_id: str
) -> None:
    try:
        submission = await temp_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            return
        
        if not submission.get("policyInitiatives"):
            new_status = "empty"
        else:
            policy_statuses = [p.get("status", "pending") for p in submission["policyInitiatives"]]
            
            if all(status == "approved" for status in policy_statuses):
                new_status = "fully_approved"
            elif all(status in ["approved", "rejected"] for status in policy_statuses):
                new_status = "fully_processed"
            elif any(status == "approved" for status in policy_statuses):
                new_status = "partially_approved"
            else:
                new_status = "pending"
        
        await temp_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {"submission_status": new_status, "updated_at": datetime.utcnow()}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating submission status: {str(e)}")

async def move_policy_to_master(
    temp_collection: AsyncIOMotorCollection,
    master_collection: AsyncIOMotorCollection,
    actions_collection: AsyncIOMotorCollection,
    submission_id: str,
    policy_index: int
) -> Dict:
    try:
        submission = await temp_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        if policy_index >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=404, detail="Policy not found")
        
        policy = submission["policyInitiatives"][policy_index]
        
        if policy.get("status") != "approved":
            raise HTTPException(status_code=400, detail="Only approved policies can be moved to master database")
        
        master_policy = {
            **policy,
            "country": submission["country"],
            "original_submission_id": submission_id,
            "moved_to_master_at": datetime.utcnow(),
            "master_status": "active"
        }
        
        result = await master_collection.insert_one(master_policy)
        
        if result.inserted_id:
            admin_log = {
                "action": "moved_to_master",
                "submission_id": submission_id,
                "policy_index": policy_index,
                "master_policy_id": str(result.inserted_id),
                "timestamp": datetime.utcnow()
            }
            await actions_collection.insert_one(admin_log)
            
            return {
                "success": True,
                "message": "Policy moved to master database",
                "master_id": str(result.inserted_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to move policy to master database")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move to master failed: {str(e)}")