"""
Policy Controller
Handles HTTP requests for policy operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from middleware.auth import get_current_user, get_admin_user
from services.policy_service import get_policy_service
from models.policy import EnhancedSubmission, PolicyStatusUpdate

router = APIRouter(prefix="/api", tags=["Policies"])

@router.post("/submit-enhanced-form")
async def submit_enhanced_form(
    submission: EnhancedSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Submit enhanced policy form"""
    policy_service = get_policy_service()
    return await policy_service.submit_enhanced_form(submission, str(current_user["_id"]))

@router.put("/admin/update-enhanced-policy-status")
async def update_enhanced_policy_status(
    status_update: PolicyStatusUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update policy status (admin only)"""
    policy_service = get_policy_service()
    return await policy_service.update_policy_status(status_update, admin_user)

@router.get("/public/master-policies")
async def get_public_master_policies(
    limit: int = Query(1000, ge=1, le=1000),
    country: str = None,
    area: str = None
):
    """Get public master policies with filtering"""
    policy_service = get_policy_service()
    return await policy_service.get_public_master_policies(limit, country, area)
