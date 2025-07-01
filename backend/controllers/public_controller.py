"""
Public Controller
Handles HTTP requests for public endpoints (no authentication required)
"""
from fastapi import APIRouter, HTTPException, Query
from config.database import get_master_policies_collection
from config.constants import POLICY_AREAS, COUNTRIES
from utils.converters import convert_objectid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Public"])

@router.get("/countries")
async def get_countries():
    """Get list of all countries"""
    return {"success": True, "countries": COUNTRIES}

@router.get("/policy-areas")
async def get_policy_areas():
    """Get list of all policy areas"""
    return {"success": True, "policy_areas": POLICY_AREAS}

@router.get("/public/country-policies/{country_name}")
async def get_country_policies(
    country_name: str,
    limit: int = Query(100, ge=1, le=500)
):
    """Get policies for a specific country"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Get policies for the country
        policies = []
        async for policy in master_policies_collection.find({
            "country": country_name,
            "master_status": "active"
        }).limit(limit):
            policies.append(convert_objectid(policy))
        
        # Group by policy area
        grouped_policies = {}
        for policy in policies:
            area = policy.get("policyArea", "unknown")
            if area not in grouped_policies:
                grouped_policies[area] = []
            grouped_policies[area].append(policy)
        
        return {
            "success": True,
            "country": country_name,
            "total_policies": len(policies),
            "policies_by_area": grouped_policies,
            "all_policies": policies
        }
    
    except Exception as e:
        logger.error(f"Error getting country policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get country policies: {str(e)}")

@router.get("/public/master-policies-no-dedup")
async def get_master_policies_no_dedup(
    limit: int = Query(1000, ge=1, le=2000),
    country: str = None,
    area: str = None
):
    """Get master policies without deduplication"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Build filter
        filter_query = {"master_status": "active"}
        if country:
            filter_query["country"] = country
        if area:
            filter_query["policyArea"] = area
        
        # Get all policies
        policies = []
        async for policy in master_policies_collection.find(filter_query).limit(limit):
            policies.append(convert_objectid(policy))
        
        return {
            "success": True,
            "policies": policies,
            "total_count": len(policies),
            "filters": {
                "country": country,
                "area": area
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting master policies (no dedup): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to AI Policy Tracker API",
        "version": "4.0.0",
        "status": "running",
        "documentation": "/docs",
        "features": [
            "User Authentication",
            "Policy Submission",
            "Admin Dashboard", 
            "AI Chatbot",
            "Global Policy Database"
        ],
        "endpoints": {
            "auth": "/api/auth/*",
            "policies": "/api/submit-enhanced-form, /api/public/master-policies",
            "admin": "/api/admin/*",
            "chat": "/api/chat",
            "public": "/api/countries, /api/policy-areas"
        }
    }
