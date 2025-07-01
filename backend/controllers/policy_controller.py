"""
Policy Controller
Handles HTTP requests for policy operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional
import logging

from middleware.auth import get_current_user, get_admin_user
from services.policy_service import policy_service
from models.policy import EnhancedSubmission, PolicyStatusUpdate, PolicyResponse
from utils.helpers import convert_objectid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Policies"])


@router.post("/submit-enhanced-form")
async def submit_enhanced_form(
    submission: EnhancedSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Submit enhanced policy form"""
    try:
        return await policy_service.submit_enhanced_form(submission, str(current_user["_id"]))
    except Exception as e:
        logger.error(f"Policy submission error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/admin/update-enhanced-policy-status")
async def update_enhanced_policy_status(
    status_update: PolicyStatusUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update policy status (admin only)"""
    try:
        return await policy_service.update_policy_status(status_update, admin_user)
    except Exception as e:
        logger.error(f"Policy status update error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/public/master-policies")
async def get_public_master_policies(
    limit: int = Query(1000, ge=1, le=1000),
    country: Optional[str] = None,
    area: Optional[str] = None
):
    """Get public master policies with filtering"""
    try:
        return await policy_service.get_public_master_policies(limit, country, area)
    except Exception as e:
        logger.error(f"Get master policies error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/master-policies-no-dedup")
async def get_master_policies_no_dedup():
    """Get master policies without deduplication"""
    try:
        return await policy_service.get_master_policies_no_dedup()
    except Exception as e:
        logger.error(f"Get master policies no dedup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/country-policies/{country_name}")
async def get_country_policies(country_name: str):
    """Get policies for a specific country"""
    try:
        return await policy_service.get_country_policies(country_name)
    except Exception as e:
        logger.error(f"Get country policies error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/countries")
async def get_countries():
    """Get list of countries"""
    try:
        from config.constants import COUNTRIES
        return {"countries": COUNTRIES}
    except Exception as e:
        logger.error(f"Get countries error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy-areas")
async def get_policy_areas():
    """Get list of policy areas"""
    try:
        from config.constants import POLICY_AREAS
        return {"policy_areas": POLICY_AREAS}
    except Exception as e:
        logger.error(f"Get policy areas error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
