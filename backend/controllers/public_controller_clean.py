"""
Clean Public Controller with DynamoDB integration
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from config.dynamodb import get_dynamodb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["public"])
# Additional router for direct API endpoints
api_router = APIRouter(prefix="/api", tags=["public-api"])

@router.get("/statistics")
async def get_statistics():
    """Get basic statistics"""
    try:
        dynamodb = await get_dynamodb()
        
        # Get user count
        users = await dynamodb.scan_table('users')
        user_count = len(users)
        
        # Get policy count
        policies = await dynamodb.scan_table('policies')
        policy_count = len(policies)
        
        return {
            "status": "success",
            "data": {
                "total_users": user_count,
                "total_policies": policy_count,
                "countries_covered": 30,  # Static for now
                "last_updated": "2025-07-15T00:00:00Z"
            }
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/countries")
async def get_countries():
    """Get list of countries with policies"""
    try:
        # Return in format expected by frontend
        countries = [
            {"name": "United States", "code": "US", "policy_count": 25},
            {"name": "United Kingdom", "code": "GB", "policy_count": 18},
            {"name": "European Union", "code": "EU", "policy_count": 32},
            {"name": "Canada", "code": "CA", "policy_count": 15},
            {"name": "Australia", "code": "AU", "policy_count": 12}
        ]
        return {"success": True, "countries": countries}
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get countries")

@router.get("/master-policies")
async def get_master_policies(
    country: Optional[str] = Query(None),
    policy_area: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get master policies with optional filtering"""
    try:
        dynamodb = await get_dynamodb()
        
        # Get policies from database
        policies = await dynamodb.scan_table('policies')
        
        # Apply filters if provided
        if country:
            policies = [p for p in policies if p.get('country', '').lower() == country.lower()]
        
        if policy_area:
            policies = [p for p in policies if p.get('policy_area', '').lower() == policy_area.lower()]
        
        # Limit results
        policies = policies[:limit]
        
        return {
            "status": "success",
            "data": policies,
            "total": len(policies)
        }
    except Exception as e:
        logger.error(f"Error getting master policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get master policies")

@router.get("/statistics-fast")
async def get_statistics_fast():
    """Get basic statistics (fast version)"""
    try:
        # Use cached/simplified version for speed
        return {
            "success": True,
            "total_policies": 0,
            "countries_with_policies": 5,
            "total_countries": 195,
            "last_updated": "2025-07-15T00:00:00Z",
            "cache_timestamp": "2025-07-15T10:16:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting fast statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/master-policies-fast")
async def get_master_policies_fast(
    limit: int = Query(1000, ge=1, le=2000),
    country: str = None
):
    """Get approved master policies visible on map (fast version)"""
    try:
        dynamodb = await get_dynamodb()
        
        # Get policies from database (simplified query for speed)
        all_policies = await dynamodb.scan_table('policies')
        
        # Filter for approved policies that are visible on map
        approved_policies = []
        for policy in all_policies:
            policy_areas = policy.get('policy_areas', [])
            for area in policy_areas:
                for p in area.get('policies', []):
                    if p.get('status') == 'approved' and p.get('map_visible', False):
                        approved_policy = {
                            "policy_id": policy.get('policy_id'),
                            "country": policy.get('country'),
                            "user_email": policy.get('user_email'),
                            "area_id": area.get('area_id'),
                            "area_name": area.get('area_name'),
                            "policyName": p.get('policyName'),
                            "policyDescription": p.get('policyDescription'),
                            "policyUrl": p.get('policyUrl'),
                            "policyId": p.get('policyId'),
                            "approved_at": p.get('approved_at'),
                            "created_at": policy.get('created_at'),
                            "status": "approved",
                            "map_visible": True
                        }
                        approved_policies.append(approved_policy)
        
        # Apply country filter if provided
        if country:
            approved_policies = [p for p in approved_policies if p.get('country', '').lower() == country.lower()]
        
        # Limit results
        approved_policies = approved_policies[:limit]
        
        return {
            "success": True,
            "policies": approved_policies,
            "total": len(approved_policies),
            "cache_timestamp": "2025-07-16T10:16:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting fast master policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get master policies")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "public-api", "database": "dynamodb"}

# Direct API endpoints for frontend compatibility
@api_router.get("/countries")
async def get_countries_api():
    """Get list of countries with policies (direct API endpoint)"""
    try:
        # Return in format expected by frontend
        countries = [
            {"name": "United States", "code": "US", "policy_count": 25},
            {"name": "United Kingdom", "code": "GB", "policy_count": 18},
            {"name": "European Union", "code": "EU", "policy_count": 32},
            {"name": "Canada", "code": "CA", "policy_count": 15},
            {"name": "Australia", "code": "AU", "policy_count": 12}
        ]
        return {"success": True, "countries": countries}
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get countries")
@router.get("/master-policies-no-dedup")
async def get_master_policies_no_dedup(
    limit: int = Query(1000, ge=1, le=2000),
    country: str = None,
    area: str = None,
    _t: str = Query(None)  # Timestamp parameter to prevent caching
):
    """Get master policies without deduplication for popup display"""
    try:
        logger.info(f"🔍 Getting policies for popup - Country: {country}, Area: {area}, Limit: {limit}")
        
        dynamodb = await get_dynamodb()
        
        # Get approved policies from map_policies table (which stores only approved policies)
        map_policies = await dynamodb.scan_table('map_policies')
        
        # Filter approved policies
        filtered_policies = []
        for policy in map_policies:
            # Must be approved and visible
            if policy.get('status') != 'approved' or not policy.get('visible_on_map', True):
                continue
                
            # Apply country filter
            if country and policy.get('country', '').lower() != country.lower():
                continue
                
            # Apply area filter  
            if area and policy.get('policy_area', '').lower() != area.lower():
                continue
                
            # Transform to expected format for popup
            policy_data = {
                'policyName': policy.get('policy_name', ''),
                'policy_name': policy.get('policy_name', ''),
                'policyDescription': policy.get('policy_description', ''),
                'policy_description': policy.get('policy_description', ''),
                'country': policy.get('country', ''),
                'policyArea': policy.get('policy_area', ''),
                'policy_area': policy.get('policy_area', ''),
                'area_name': policy.get('policy_area', ''),
                'area_id': policy.get('policy_area', ''),
                'status': policy.get('status', 'approved'),
                'master_status': 'active',  # All map policies are active
                'target_groups': policy.get('target_groups', []),
                'policy_link': policy.get('policy_link', ''),
                'implementation': policy.get('implementation', {}),
                'evaluation': policy.get('evaluation', {}),
                'participation': policy.get('participation', {}),
                'alignment': policy.get('alignment', {}),
                'approved_at': policy.get('approved_at', ''),
                'created_at': policy.get('created_at', ''),
                'user_email': policy.get('user_email', ''),
                'map_policy_id': policy.get('map_policy_id', ''),
                'parent_submission_id': policy.get('parent_submission_id', '')
            }
            
            filtered_policies.append(policy_data)
        
        # Apply limit
        filtered_policies = filtered_policies[:limit]
        
        logger.info(f"✅ Found {len(filtered_policies)} policies for popup display")
        
        return {
            "success": True,
            "policies": filtered_policies,
            "total_count": len(filtered_policies),
            "country_filter": country,
            "area_filter": area,
            "data_source": "map_policies (approved only)",
            "cache_bust": _t
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting policies for popup: {str(e)}")
        return {
            "success": False,
            "policies": [],
            "total_count": 0,
            "error": str(e)
        }
