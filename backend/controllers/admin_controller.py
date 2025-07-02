"""
Admin Controller
Handles HTTP requests for admin operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
import logging
import time

from middleware.auth import get_admin_user, get_current_user
from services.admin_service import admin_service
from utils.helpers import convert_objectid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/submissions")
async def get_admin_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query("all"),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all submissions for admin review with pagination"""
    try:
        return await admin_service.get_submissions(page=page, limit=limit, status=status)
    except Exception as e:
        logger.error(f"Error getting admin submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")


@router.get("/statistics")
async def get_admin_statistics(admin_user: dict = Depends(get_admin_user)):
    """Get admin statistics with timeout handling"""
    try:
        import asyncio
        
        async def fetch_stats():
            return await admin_service.get_statistics()
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(fetch_stats(), timeout=10.0)
            return result
        except asyncio.TimeoutError:
            logger.warning("Statistics query timeout")
            # Return default statistics instead of error
            return {
                "success": True,
                "statistics": {
                    "users": {"total": 0, "verified": 0, "admin": 0},
                    "submissions": {"total": 0, "pending": 0},
                    "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
                },
                "note": "Statistics temporarily unavailable - database timeout"
            }
    except Exception as e:
        logger.error(f"Error getting admin statistics: {str(e)}")
        # Return default statistics instead of 500 error
        return {
            "success": False,
            "statistics": {
                "users": {"total": 0, "verified": 0, "admin": 0},
                "submissions": {"total": 0, "pending": 0},
                "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
            },
            "error": "Database connection issue - please try again"
        }


@router.get("/statistics-fast")
async def get_admin_statistics_fast(admin_user: dict = Depends(get_admin_user)):
    """Ultra-fast admin statistics with caching"""
    try:
        import asyncio
        
        # Use in-memory cache for 60 seconds
        cache_key = "fast_stats_cache"
        cached_stats = getattr(get_admin_statistics_fast, cache_key, None)
        cache_time = getattr(get_admin_statistics_fast, f"{cache_key}_time", 0)
        
        if cached_stats and (time.time() - cache_time) < 60:
            return {
                "success": True,
                "statistics": cached_stats,
                "cached": True
            }
        
        async def fetch_basic_stats():
            from services.admin_service import admin_service
            return await admin_service.get_statistics()
        
        # Execute with very short timeout
        try:
            result = await asyncio.wait_for(fetch_basic_stats(), timeout=2.0)
            
            # Cache the result
            setattr(get_admin_statistics_fast, cache_key, result.get("statistics", {}))
            setattr(get_admin_statistics_fast, f"{cache_key}_time", time.time())
            
            return result
        except asyncio.TimeoutError:
            logger.warning("Fast statistics timeout")
            
            # Return cached data if available
            if cached_stats:
                return {
                    "success": True,
                    "statistics": cached_stats,
                    "note": "Using cached data due to timeout"
                }
            
            # Return default stats
            return {
                "success": True,
                "statistics": {
                    "users": {"total": 0, "verified": 0, "admin": 0},
                    "submissions": {"total": 0, "pending": 0},
                    "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
                },
                "note": "Fast query timeout"
            }
            
    except Exception as e:
        logger.error(f"Error in fast statistics: {str(e)}")
        return {
            "success": False,
            "statistics": {
                "users": {"total": 0, "verified": 0, "admin": 0},
                "submissions": {"total": 0, "pending": 0},
                "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
            },
            "error": "Fast query failed"
        }


@router.post("/move-to-master")
async def move_submission_to_master(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Move approved policies to master collection"""
    try:
        submission_id = request_data.get("submission_id")
        if not submission_id:
            raise HTTPException(status_code=400, detail="submission_id is required")
        
        return await admin_service.move_to_master(submission_id, admin_user)
    except Exception as e:
        logger.error(f"Error moving to master: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to move to master: {str(e)}")


@router.post("/fix-visibility")
async def fix_policy_visibility(
    admin_user: dict = Depends(get_admin_user)
):
    """Fix policy visibility issues"""
    try:
        return await admin_service.fix_visibility()
    except Exception as e:
        logger.error(f"Error fixing visibility: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fix visibility: {str(e)}")


@router.post("/migrate-old-data")
async def migrate_old_data(
    admin_user: dict = Depends(get_admin_user)
):
    """Migrate old data format to new format"""
    try:
        return await admin_service.migrate_old_data()
    except Exception as e:
        logger.error(f"Error migrating data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to migrate data: {str(e)}")


@router.post("/repair-historical-data")
async def repair_historical_data(
    admin_user: dict = Depends(get_admin_user)
):
    """Repair historical data issues"""
    try:
        return await admin_service.repair_historical_data()
    except Exception as e:
        logger.error(f"Error repairing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to repair data: {str(e)}")


@router.put("/update-policy-status")
async def update_policy_status(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Update the status of a specific policy (approve/reject)"""
    try:
        submission_id = request_data.get("submission_id")
        area_id = request_data.get("area_id")
        policy_index = request_data.get("policy_index")
        status = request_data.get("status")
        admin_notes = request_data.get("admin_notes", "")
        
        if not all([submission_id, area_id is not None, policy_index is not None, status]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        return await admin_service.update_policy_status(
            submission_id, area_id, policy_index, status, admin_notes, admin_user
        )
    except Exception as e:
        logger.error(f"Error updating policy status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update policy status: {str(e)}")


@router.delete("/master-policy/{policy_id}")
async def delete_master_policy(
    policy_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a policy from master collection (removes from DB and map)"""
    try:
        return await admin_service.delete_master_policy(policy_id, admin_user)
    except Exception as e:
        logger.error(f"Error deleting master policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete master policy: {str(e)}")


@router.delete("/submission-policy")
async def delete_submission_policy(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a specific policy from a submission"""
    try:
        submission_id = request_data.get("submission_id")
        area_id = request_data.get("area_id")
        policy_index = request_data.get("policy_index")
        
        if not all([submission_id, area_id is not None, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        return await admin_service.delete_submission_policy(
            submission_id, area_id, policy_index, admin_user
        )
    except Exception as e:
        logger.error(f"Error deleting submission policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete submission policy: {str(e)}")


@router.get("/master-policies")
async def get_master_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get master policies for admin management"""
    try:
        skip = (page - 1) * limit
        
        # Get active master policies
        cursor = admin_service.master_policies_collection.find(
            {"master_status": "active"}
        ).sort("moved_to_master_at", -1).skip(skip).limit(limit)
        
        policies = []
        async for policy in cursor:
            policies.append(convert_objectid(policy))
        
        # Get total count
        total_count = await admin_service.master_policies_collection.count_documents(
            {"master_status": "active"}
        )
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "success": True,
            "policies": policies,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page
        }
    except Exception as e:
        logger.error(f"Error getting master policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get master policies: {str(e)}")
