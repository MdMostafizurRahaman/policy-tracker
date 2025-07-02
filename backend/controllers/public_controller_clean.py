"""
Public Controller - Clean and Simple
Handles HTTP requests for public endpoints (no authentication required)
"""
from fastapi import APIRouter, HTTPException, Query
from config.database import get_master_policies_collection
from config.constants import POLICY_AREAS, COUNTRIES
from utils.converters import convert_objectid
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

@router.get("/public/master-policies")
async def get_master_policies(
    limit: int = Query(500, ge=1, le=1000),
    country: str = None,
    area: str = None
):
    """Get approved master policies for map visualization"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Build filter for approved policies only
        filter_query = {"master_status": "active"}
        if country:
            filter_query["country"] = country
        if area:
            filter_query["policyArea"] = area
        
        # Get policies
        policies = []
        async for policy in master_policies_collection.find(filter_query).limit(limit):
            policies.append(convert_objectid(policy))
        
        return {
            "success": True,
            "policies": policies,
            "total_count": len(policies),
            "filters": {"country": country, "area": area}
        }
        
    except Exception as e:
        logger.error(f"Error getting master policies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get policies")

@router.get("/public/statistics")
async def get_public_statistics():
    """Get basic statistics for the map"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Count approved policies
        total_policies = await master_policies_collection.count_documents({"master_status": "active"})
        
        # Count countries with approved policies
        countries_with_policies = len(
            await master_policies_collection.distinct("country", {"master_status": "active"})
        )
        
        return {
            "success": True,
            "total_policies": total_policies,
            "countries_with_policies": countries_with_policies,
            "total_countries": len(COUNTRIES)
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/public/country-policies/{country_name}")
async def get_country_policies(
    country_name: str,
    limit: int = Query(100, ge=1, le=500)
):
    """Get approved policies for a specific country"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Get approved policies for the country
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
        raise HTTPException(status_code=500, detail="Failed to get country policies")
