"""
Policy management endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from models.policy import EnhancedSubmission, PolicyStatusUpdate
from services.policy_service import policy_service
from core.security import get_current_user, get_admin_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/submit-enhanced-form")
async def submit_enhanced_form(
    submission: EnhancedSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Enhanced policy submission with better validation"""
    return await policy_service.submit_policy(submission.dict(), current_user)

@router.put("/admin/update-enhanced-policy-status")
async def update_enhanced_policy_status(
    status_update: PolicyStatusUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Enhanced policy status update with automatic master DB movement"""
    return await policy_service.update_policy_status(status_update.dict(), admin_user)

@router.get("/public/master-policies")
async def get_public_master_policies(
    limit: int = Query(1000, ge=1, le=1000),
    country: str = None,
    area: str = None
):
    """Enhanced public endpoint - shows ALL approved policies with better deduplication"""
    try:
        policies = await policy_service.get_public_policies(limit, country, area)
        
        # Get statistics
        total_policies = len(policies)
        countries_represented = len(set(p.get("country") for p in policies if p.get("country")))
        policy_areas = len(set(p.get("policyArea") for p in policies if p.get("policyArea")))
        
        return {
            "success": True,
            "policies": policies,
            "statistics": {
                "total_policies": total_policies,
                "countries_represented": countries_represented,
                "policy_areas_covered": policy_areas,
                "data_sources": ["master_policies", "temp_submissions"]
            },
            "message": f"Retrieved {total_policies} policies"
        }
    
    except Exception as e:
        logger.error(f"Error getting public policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")

@router.get("/debug/policy-counts")
async def debug_policy_counts():
    """Debug endpoint to check policy counts across collections"""
    try:
        from core.database import get_collections
        
        collections = get_collections()
        
        # Count master policies
        master_count = await collections["master_policies"].count_documents({"master_status": "active"})
        
        # Count temp submissions
        temp_count = await collections["temp_submissions"].count_documents({})
        
        # Count approved policies in temp
        approved_in_temp = 0
        async for submission in collections["temp_submissions"].find({}):
            for area in submission.get("policyAreas", []):
                for policy in area.get("policies", []):
                    if policy.get("status") == "approved":
                        approved_in_temp += 1
        
        return {
            "master_policies": master_count,
            "temp_submissions": temp_count,
            "approved_in_temp": approved_in_temp,
            "total_approved": master_count + approved_in_temp
        }
    
    except Exception as e:
        logger.error(f"Error getting policy counts: {str(e)}")
        return {"error": str(e)}

@router.get("/debug/policy-data-analysis")
async def debug_policy_data_analysis():
    """Debug endpoint for policy data analysis"""
    try:
        from core.database import get_collections
        from utils.helpers import convert_objectid
        
        collections = get_collections()
        
        # Sample master policies
        master_sample = []
        async for doc in collections["master_policies"].find({"master_status": "active"}).limit(3):
            master_sample.append({
                "id": str(doc["_id"]),
                "policyName": doc.get("policyName", ""),
                "country": doc.get("country", ""),
                "policyArea": doc.get("policyArea", ""),
                "status": doc.get("status", ""),
                "master_status": doc.get("master_status", "")
            })
        
        # Sample temp policies
        temp_sample = []
        async for submission in collections["temp_submissions"].find({}).limit(2):
            for area in submission.get("policyAreas", []):
                for policy in area.get("policies", []):
                    temp_sample.append({
                        "policyName": policy.get("policyName", ""),
                        "country": submission.get("country", ""),
                        "policyArea": area.get("area_id", ""),
                        "status": policy.get("status", ""),
                        "submission_id": str(submission["_id"])
                    })
                    if len(temp_sample) >= 3:
                        break
                if len(temp_sample) >= 3:
                    break
            if len(temp_sample) >= 3:
                break
        
        return {
            "master_sample": master_sample,
            "temp_sample": temp_sample,
            "analysis": "This shows the structure of both collections"
        }
    
    except Exception as e:
        logger.error(f"Error in policy analysis: {str(e)}")
        return {"error": str(e)}

@router.get("/public/master-policies-no-dedup")
async def get_public_master_policies_no_dedup(
    limit: int = Query(100, ge=1, le=1000)
):
    """Get master policies without deduplication for debugging"""
    try:
        from core.database import get_collections
        from utils.helpers import convert_objectid
        
        collections = get_collections()
        
        policies = []
        async for doc in collections["master_policies"].find({"master_status": "active"}).limit(limit):
            policy_data = convert_objectid(doc)
            policies.append(policy_data)
        
        return {
            "success": True,
            "policies": policies,
            "count": len(policies),
            "message": "Raw master policies without deduplication"
        }
    
    except Exception as e:
        logger.error(f"Error getting raw policies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
