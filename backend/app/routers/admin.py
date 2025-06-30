"""
Admin routes for policy management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from models.policy import PolicyApproval
from routers.auth import get_current_user
from models.user import UserResponse
from config.database import get_database
from typing import List
from datetime import datetime
from bson import ObjectId

router = APIRouter()

def get_policies_collection():
    """Get policies collection"""
    db = get_database()
    return db.temp_submissions

def get_master_policies_collection():
    """Get master policies collection"""
    db = get_database()
    return db.master_policies

async def require_admin(current_user: UserResponse = Depends(get_current_user)):
    """Require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/pending-policies")
async def get_pending_policies(
    admin_user: UserResponse = Depends(require_admin),
    policies_collection = Depends(get_policies_collection)
):
    """Get pending policies for review"""
    try:
        policies = await policies_collection.find(
            {"status": "pending"}
        ).sort("submittedAt", -1).to_list(length=100)
        
        return {"policies": policies}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending policies"
        )

@router.post("/approve-policy")
async def approve_policy(
    approval: PolicyApproval,
    admin_user: UserResponse = Depends(require_admin),
    policies_collection = Depends(get_policies_collection),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Approve or reject policy"""
    try:
        # Find the policy
        policy = await policies_collection.find_one({"_id": ObjectId(approval.policy_id)})
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        if policy["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Policy is not pending approval"
            )
        
        if approval.action == "approve":
            # Move to master policies
            policy_doc = {**policy}
            policy_doc.pop("_id", None)
            policy_doc["status"] = "approved"
            policy_doc["approvedBy"] = admin_user.id
            policy_doc["approvedAt"] = datetime.utcnow()
            
            await master_policies_collection.insert_one(policy_doc)
            
            # Update temp submission
            await policies_collection.update_one(
                {"_id": policy["_id"]},
                {
                    "$set": {
                        "status": "approved",
                        "approvedBy": admin_user.id,
                        "approvedAt": datetime.utcnow()
                    }
                }
            )
            
            message = "Policy approved successfully"
            
        else:  # reject
            await policies_collection.update_one(
                {"_id": policy["_id"]},
                {
                    "$set": {
                        "status": "rejected",
                        "rejectedBy": admin_user.id,
                        "rejectedAt": datetime.utcnow(),
                        "rejectionReason": approval.reason
                    }
                }
            )
            
            message = "Policy rejected"
        
        return {"message": message}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid policy ID"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process approval"
        )

@router.get("/stats")
async def get_admin_stats(
    admin_user: UserResponse = Depends(require_admin),
    policies_collection = Depends(get_policies_collection),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Get admin dashboard statistics"""
    try:
        # Count policies by status
        pending_count = await policies_collection.count_documents({"status": "pending"})
        approved_count = await policies_collection.count_documents({"status": "approved"})
        rejected_count = await policies_collection.count_documents({"status": "rejected"})
        master_count = await master_policies_collection.count_documents({})
        
        # Get recent submissions
        recent_submissions = await policies_collection.find(
            {}
        ).sort("submittedAt", -1).limit(5).to_list(length=5)
        
        return {
            "stats": {
                "pending_policies": pending_count,
                "approved_policies": approved_count,
                "rejected_policies": rejected_count,
                "master_policies": master_count,
                "total_submissions": pending_count + approved_count + rejected_count
            },
            "recent_submissions": recent_submissions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )
