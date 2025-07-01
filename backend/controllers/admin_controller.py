"""
Admin Controller
Handles HTTP requests for admin operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
import logging

from middleware.auth import get_admin_user, get_current_user
from services.admin_service import admin_service
from utils.helpers import convert_objectid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/submissions")
async def get_admin_submissions(
    limit: int = Query(50, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all submissions for admin review"""
    try:
        return await admin_service.get_submissions(limit)
    except Exception as e:
        logger.error(f"Error getting admin submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")


@router.get("/statistics")
async def get_admin_statistics(admin_user: dict = Depends(get_admin_user)):
    """Get admin statistics"""
    try:
        return await admin_service.get_statistics()
    except Exception as e:
        logger.error(f"Error getting admin statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


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
