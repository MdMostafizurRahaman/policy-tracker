from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime
from typing import Optional
from bson import ObjectId

from ..database.connection import get_db
from ..models.policy_models import PolicyUpdate
from ..services.policy_service import update_submission_status

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/submissions")
async def get_all_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db=Depends(get_db)
):
    try:
        skip = (page - 1) * limit
        filter_dict = {}
        if status:
            filter_dict["submission_status"] = status
        
        cursor = db.temp_policies.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit)
        submissions = []
        async for doc in cursor:
            submissions.append(doc)
        
        total_count = await db.temp_policies.count_documents(filter_dict)
        
        return {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submission/{submission_id}")
async def get_submission_details(submission_id: str, db=Depends(get_db)):
    try:
        submission = await db.temp_policies.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        return submission
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/edit-policy")
async def edit_policy(policy_update: PolicyUpdate, db=Depends(get_db)):
    try:
        submission = await db.temp_policies.find_one({"_id": ObjectId(policy_update.submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        if policy_update.policy_index >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=404, detail="Policy not found")
        
        update_dict = {}
        updated_policy = policy_update.updated_policy.dict()
        for key, value in updated_policy.items():
            update_dict[f"policyInitiatives.{policy_update.policy_index}.{key}"] = value
        
        update_dict["updated_at"] = datetime.utcnow()
        
        await db.temp_policies.update_one(
            {"_id": ObjectId(policy_update.submission_id)},
            {"$set": update_dict}
        )
        
        admin_log = {
            "action": "policy_edited",
            "submission_id": policy_update.submission_id,
            "policy_index": policy_update.policy_index,
            "updated_fields": list(updated_policy.keys()),
            "timestamp": datetime.utcnow()
        }
        await db.admin_actions.insert_one(admin_log)
        
        return {"success": True, "message": "Policy updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-policy")
async def delete_policy(
    delete_request: dict,
    db=Depends(get_db)
):
    """Delete a policy from a submission"""
    try:
        submission = await db.temp_policies.find_one({"_id": ObjectId(delete_request["submission_id"])})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        if delete_request["policy_index"] >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Remove the policy
        policies = submission["policyInitiatives"]
        deleted_policy = policies.pop(delete_request["policy_index"])
        
        # Update the submission
        await db.temp_policies.update_one(
            {"_id": ObjectId(delete_request["submission_id"])},
            {"$set": {
                "policyInitiatives": policies,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Delete associated file if exists
        if deleted_policy.get("policyFile") and deleted_policy["policyFile"].get("file_id"):
            await db.files.delete_one({"_id": ObjectId(deleted_policy["policyFile"]["file_id"])})
        
        # Log admin action
        admin_log = {
            "action": "policy_deleted",
            "submission_id": delete_request["submission_id"],
            "policy_index": delete_request["policy_index"],
            "deleted_policy_name": deleted_policy.get("policyName", "Unknown"),
            "timestamp": datetime.utcnow()
        }
        await db.admin_actions.insert_one(admin_log)
        
        # Update submission status
        await update_submission_status(db.temp_policies, delete_request["submission_id"])
        
        return {"success": True, "message": "Policy deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/master-policies")
async def get_master_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    country: Optional[str] = Query(None),
    policy_area: Optional[str] = Query(None),
    db=Depends(get_db)
):
    """Get approved policies from master database"""
    try:
        skip = (page - 1) * limit
        filter_dict = {"master_status": {"$ne": "deleted"}}
        
        if country:
            filter_dict["country"] = {"$regex": country, "$options": "i"}
        if policy_area:
            filter_dict["policyArea"] = policy_area
        
        cursor = db.master_policies.find(filter_dict).sort("moved_to_master_at", -1).skip(skip).limit(limit)
        policies = []
        async for doc in cursor:
            policies.append(doc)
        
        total_count = await db.master_policies.count_documents(filter_dict)
        
        return {
            "policies": policies,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/master-policy/{policy_id}")
async def delete_master_policy(
    policy_id: str,
    db=Depends(get_db)
):
    """Delete a policy from master database (soft delete)"""
    try:
        result = await db.master_policies.update_one(
            {"_id": ObjectId(policy_id)},
            {"$set": {"master_status": "deleted", "deleted_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 1:
            # Log admin action
            admin_log = {
                "action": "master_policy_deleted",
                "master_policy_id": policy_id,
                "timestamp": datetime.utcnow()
            }
            await db.admin_actions.insert_one(admin_log)
            
            return {"success": True, "message": "Policy deleted successfully"}
        raise HTTPException(status_code=404, detail="Policy not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_admin_statistics(db=Depends(get_db)):
    """Get statistics for admin dashboard"""
    try:
        return {
            "pending_submissions": await db.temp_policies.count_documents({"submission_status": "pending"}),
            "partially_approved": await db.temp_policies.count_documents({"submission_status": "partially_approved"}),
            "fully_approved": await db.temp_policies.count_documents({"submission_status": "fully_approved"}),
            "total_approved_policies": await db.master_policies.count_documents({"master_status": {"$ne": "deleted"}}),
            "total_temp_policies": await db.temp_policies.count_documents({}),
            "recent_actions": await db.admin_actions.find().sort("timestamp", -1).limit(10).to_list(length=10)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))