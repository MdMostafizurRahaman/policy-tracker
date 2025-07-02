"""
Public Controller
Handles public endpoints for viewing map data and general information
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

@router.get("/public/approved-policies")
async def get_approved_policies(
    country: str = None,
    policy_area: str = None,
    limit: int = Query(1000, ge=1, le=2000)
):
    """Get approved policies for map visualization - only policies approved by admin"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Build filter - only approved policies shown on map (master_status: active)
        filter_query = {"master_status": "active"}
        if country:
            filter_query["country"] = country
        if policy_area:
            filter_query["policyArea"] = policy_area
        
        policies = []
        async for policy in master_policies_collection.find(filter_query).limit(limit):
            policies.append(convert_objectid(policy))
        
        return {
            "success": True,
            "policies": policies,
            "total_count": len(policies),
            "filters": {"country": country, "policy_area": policy_area}
        }
        
    except Exception as e:
        logger.error(f"Error getting approved policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")

@router.get("/public/statistics")
async def get_public_statistics():
    """Get basic statistics for the public dashboard"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Count approved policies only (master_status: active)
        total_approved = await master_policies_collection.count_documents({"master_status": "active"})
        
        # Count countries with approved policies
        countries_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$country"}},
            {"$count": "total"}
        ]
        countries_result = await master_policies_collection.aggregate(countries_pipeline).to_list(1)
        countries_with_policies = countries_result[0]["total"] if countries_result else 0
        
        # Count by policy areas
        areas_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$policyArea", "count": {"$sum": 1}}}
        ]
        areas_result = await master_policies_collection.aggregate(areas_pipeline).to_list(None)
        policies_by_area = {area["_id"]: area["count"] for area in areas_result}
        
        return {
            "success": True,
            "total_approved_policies": total_approved,
            "countries_with_policies": countries_with_policies,
            "total_countries": len(COUNTRIES),
            "policies_by_area": policies_by_area,
            "statistics": {
                "policies": {
                    "approved": total_approved,
                    "master": total_approved
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return {
            "success": True,
            "total_approved_policies": 0,
            "countries_with_policies": 0,
            "total_countries": len(COUNTRIES),
            "policies_by_area": {},
            "statistics": {
                "policies": {
                    "approved": 0,
                    "master": 0
                }
            }
        }

@router.get("/public/statistics-fast")
async def get_public_statistics_fast():
    """Get basic statistics quickly for the frontend"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Count approved policies only (master_status: active)
        total_approved = await master_policies_collection.count_documents({"master_status": "active"})
        
        # Count countries with approved policies
        countries_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$country"}},
            {"$count": "total"}
        ]
        countries_result = await master_policies_collection.aggregate(countries_pipeline).to_list(1)
        countries_with_policies = countries_result[0]["total"] if countries_result else 0
        
        # Count by policy areas
        areas_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$policyArea", "count": {"$sum": 1}}}
        ]
        areas_result = await master_policies_collection.aggregate(areas_pipeline).to_list(None)
        policies_by_area = {area["_id"]: area["count"] for area in areas_result}
        
        return {
            "success": True,
            "total_approved_policies": total_approved,
            "countries_with_policies": countries_with_policies,
            "total_countries": len(COUNTRIES),
            "policies_by_area": policies_by_area,
            "statistics": {
                "policies": {
                    "approved": total_approved,
                    "master": total_approved
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting fast statistics: {str(e)}")
        return {
            "success": True,
            "total_approved_policies": 0,
            "countries_with_policies": 0,
            "total_countries": len(COUNTRIES),
            "policies_by_area": {},
            "statistics": {
                "policies": {
                    "approved": 0,
                    "master": 0
                }
            }
        }

@router.get("/public/master-policies")
async def get_master_policies(
    limit: int = Query(1000, ge=1, le=2000),
    country: str = None,
    area: str = None
):
    """Get approved master policies for map visualization"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Build filter - only approved policies (master_status: active)
        filter_query = {"master_status": "active"}
        if country:
            filter_query["country"] = country
        if area:
            filter_query["policyArea"] = area
        
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
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")

@router.get("/public/master-policies-fast")
async def get_master_policies_fast(
    limit: int = Query(1000, ge=1, le=2000),
    country: str = None
):
    """Fast master policies endpoint"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Build filter - only approved policies (master_status: active)
        filter_query = {"master_status": "active"}
        if country:
            filter_query["country"] = country
        
        policies = []
        async for policy in master_policies_collection.find(filter_query).limit(limit):
            policies.append(convert_objectid(policy))
        
        return {
            "success": True,
            "policies": policies,
            "total_count": len(policies),
            "filters": {"country": country}
        }
        
    except Exception as e:
        logger.error(f"Error getting fast policies: {str(e)}")
        return {
            "success": False,
            "policies": [],
            "total_count": 0,
            "error": "Fast query failed"
        }

@router.get("/public/master-policies-no-dedup")
async def get_master_policies_no_dedup(
    limit: int = Query(1000, ge=1, le=2000),
    country: str = None,
    area: str = None
):
    """Get master policies without deduplication"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Build filter - only approved policies (master_status: active)
        filter_query = {"master_status": "active"}
        if country:
            filter_query["country"] = country
        if area:
            filter_query["policyArea"] = area
        
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
        return {
            "success": False,
            "policies": [],
            "total_count": 0,
            "error": str(e)
        }

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to AI Policy Tracker API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "description": "Global policy tracking platform with user submissions and admin approval workflow"
    }
