"""
Admin Controller
Handles HTTP requests for admin operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from middleware.auth import get_admin_user, get_current_user
from config.database import (
    get_temp_submissions_collection,
    get_master_policies_collection,
    get_admin_actions_collection,
    get_users_collection
)
from config.data_constants import POLICY_AREAS, COUNTRIES
from utils.converters import convert_objectid
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/submissions")
async def get_admin_submissions(
    limit: int = Query(50, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all submissions for admin review"""
    try:
        temp_submissions_collection = get_temp_submissions_collection()
        
        submissions = []
        async for submission in temp_submissions_collection.find({}).limit(limit).sort("created_at", -1):
            submissions.append(convert_objectid(submission))
        
        return {
            "success": True,
            "submissions": submissions,
            "total_count": len(submissions)
        }
    
    except Exception as e:
        logger.error(f"Error getting admin submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")

@router.get("/statistics")
async def get_admin_statistics(admin_user: dict = Depends(get_admin_user)):
    """Get admin statistics"""
    try:
        users_collection = get_users_collection()
        temp_submissions_collection = get_temp_submissions_collection()
        master_policies_collection = get_master_policies_collection()
        
        # Count users
        total_users = await users_collection.count_documents({})
        verified_users = await users_collection.count_documents({"is_verified": True})
        admin_users = await users_collection.count_documents({"is_admin": True})
        
        # Count submissions
        total_submissions = await temp_submissions_collection.count_documents({})
        pending_submissions = await temp_submissions_collection.count_documents({"submission_status": "pending"})
        approved_submissions = await temp_submissions_collection.count_documents({"submission_status": "approved"})
        
        # Count master policies
        total_master_policies = await master_policies_collection.count_documents({"master_status": "active"})
        
        return {
            "success": True,
            "statistics": {
                "users": {
                    "total": total_users,
                    "verified": verified_users,
                    "admins": admin_users
                },
                "submissions": {
                    "total": total_submissions,
                    "pending": pending_submissions,
                    "approved": approved_submissions
                },
                "master_policies": {
                    "total": total_master_policies
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting admin statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/move-to-master")
async def move_to_master(
    data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Move approved policies to master database"""
    try:
        submission_id = data.get("submission_id")
        if not submission_id:
            raise HTTPException(status_code=400, detail="submission_id is required")
        
        temp_submissions_collection = get_temp_submissions_collection()
        master_policies_collection = get_master_policies_collection()
        
        # Get submission
        submission = await temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        moved_count = 0
        for area in submission.get("policyAreas", []):
            for i, policy in enumerate(area.get("policies", [])):
                if policy.get("status") == "approved":
                    # Check if already in master
                    existing = await master_policies_collection.find_one({
                        "original_submission_id": submission_id,
                        "policyArea": area["area_id"],
                        "policy_index": i
                    })
                    
                    if not existing:
                        # Get area info
                        area_info = next((a for a in POLICY_AREAS if a["id"] == area["area_id"]), None)
                        
                        master_policy = {
                            **policy,
                            "country": submission["country"],
                            "policyArea": area["area_id"],
                            "area_name": area_info["name"] if area_info else area["area_id"],
                            "area_icon": area_info["icon"] if area_info else "📄",
                            "area_color": area_info["color"] if area_info else "from-gray-500 to-gray-600",
                            "user_id": submission["user_id"],
                            "user_email": submission.get("user_email", ""),
                            "user_name": submission.get("user_name", ""),
                            "original_submission_id": submission_id,
                            "policy_index": i,
                            "moved_to_master_at": datetime.utcnow(),
                            "approved_by": str(admin_user["_id"]),
                            "approved_by_email": admin_user["email"],
                            "master_status": "active"
                        }
                        
                        await master_policies_collection.insert_one(master_policy)
                        moved_count += 1
        
        return {
            "success": True,
            "message": f"Moved {moved_count} policies to master database"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving to master: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to move to master: {str(e)}")

@router.put("/edit-policy")
async def edit_policy(
    data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Edit a policy in master database"""
    try:
        policy_id = data.get("policy_id")
        updates = data.get("updates", {})
        
        if not policy_id:
            raise HTTPException(status_code=400, detail="policy_id is required")
        
        master_policies_collection = get_master_policies_collection()
        
        # Update policy
        result = await master_policies_collection.update_one(
            {"_id": ObjectId(policy_id)},
            {"$set": {
                **updates,
                "last_modified": datetime.utcnow(),
                "modified_by": admin_user["email"]
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return {
            "success": True,
            "message": "Policy updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to edit policy: {str(e)}")

@router.delete("/delete-policy")
async def delete_policy(
    data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a policy from master database"""
    try:
        policy_id = data.get("policy_id")
        
        if not policy_id:
            raise HTTPException(status_code=400, detail="policy_id is required")
        
        master_policies_collection = get_master_policies_collection()
        
        # Soft delete by updating status
        result = await master_policies_collection.update_one(
            {"_id": ObjectId(policy_id)},
            {"$set": {
                "master_status": "deleted",
                "deleted_at": datetime.utcnow(),
                "deleted_by": admin_user["email"]
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return {
            "success": True,
            "message": "Policy deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")

@router.post("/admin-login")
async def admin_login(
    login_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Additional admin verification"""
    try:
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return {
            "success": True,
            "message": "Admin access verified",
            "admin": {
                "id": str(current_user["_id"]),
                "email": current_user["email"],
                "is_super_admin": current_user.get("is_super_admin", False)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Admin login failed: {str(e)}")

@router.post("/fix-visibility")
async def fix_visibility(admin_user: dict = Depends(get_admin_user)):
    """Fix visibility issues in master policies"""
    try:
        from services.admin_service import admin_service
        return await admin_service.fix_visibility_issues(admin_user)
    except Exception as e:
        logger.error(f"Error fixing visibility: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fix visibility: {str(e)}")

@router.post("/migrate-old-data")
async def migrate_old_data(admin_user: dict = Depends(get_admin_user)):
    """Migrate old data format to new format"""
    try:
        from services.admin_service import admin_service
        return await admin_service.migrate_old_data(admin_user)
    except Exception as e:
        logger.error(f"Error migrating data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to migrate data: {str(e)}")

@router.post("/repair-historical-data")
async def repair_historical_data(admin_user: dict = Depends(get_admin_user)):
    """Repair historical data inconsistencies"""
    try:
        from services.admin_service import admin_service
        return await admin_service.repair_historical_data(admin_user)
    except Exception as e:
        logger.error(f"Error repairing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to repair data: {str(e)}")
