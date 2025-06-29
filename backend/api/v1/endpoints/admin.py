"""
Admin management endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from core.security import get_admin_user
from core.database import get_collections
from utils.helpers import convert_objectid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/submissions")
async def get_admin_submissions(
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """Get submissions for admin review"""
    try:
        collections = get_collections()
        
        # Build filter
        filter_query = {}
        if status:
            filter_query["submission_status"] = status
        
        # Get submissions
        submissions = []
        async for submission in collections["temp_submissions"].find(filter_query).limit(limit).sort("created_at", -1):
            submissions.append(convert_objectid(submission))
        
        return {
            "success": True,
            "submissions": submissions,
            "count": len(submissions)
        }
    
    except Exception as e:
        logger.error(f"Error getting admin submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def get_admin_users(
    limit: int = Query(50, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get users for admin management"""
    try:
        collections = get_collections()
        
        # Get users (excluding passwords)
        users = []
        async for user in collections["users"].find({}, {"password": 0}).limit(limit).sort("created_at", -1):
            users.append(convert_objectid(user))
        
        return {
            "success": True,
            "users": users,
            "count": len(users)
        }
    
    except Exception as e:
        logger.error(f"Error getting admin users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_admin_statistics(admin_user: dict = Depends(get_admin_user)):
    """Get admin dashboard statistics"""
    try:
        collections = get_collections()
        
        # Count users
        total_users = await collections["users"].count_documents({})
        verified_users = await collections["users"].count_documents({"is_verified": True})
        admin_users = await collections["users"].count_documents({"is_admin": True})
        
        # Count submissions
        total_submissions = await collections["temp_submissions"].count_documents({})
        pending_submissions = await collections["temp_submissions"].count_documents({"submission_status": "pending"})
        approved_submissions = await collections["temp_submissions"].count_documents({"submission_status": "approved"})
        
        # Count master policies
        master_policies = await collections["master_policies"].count_documents({"master_status": "active"})
        
        # Count by country
        country_pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_countries = []
        async for result in collections["master_policies"].aggregate(country_pipeline):
            top_countries.append({"country": result["_id"], "count": result["count"]})
        
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
                "policies": {
                    "master_policies": master_policies
                },
                "top_countries": top_countries
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting admin statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/actions")
async def get_admin_actions(
    limit: int = Query(50, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get admin action history"""
    try:
        collections = get_collections()
        
        # Get admin actions
        actions = []
        async for action in collections["admin_actions"].find({}).limit(limit).sort("timestamp", -1):
            actions.append(convert_objectid(action))
        
        return {
            "success": True,
            "actions": actions,
            "count": len(actions)
        }
    
    except Exception as e:
        logger.error(f"Error getting admin actions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
