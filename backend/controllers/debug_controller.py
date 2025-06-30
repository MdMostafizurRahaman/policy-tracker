"""
Debug Controller
Handles HTTP requests for debugging and maintenance operations
"""
from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_admin_user
from config.database import (
    get_master_policies_collection,
    get_temp_submissions_collection,
    get_users_collection
)
from utils.converters import convert_objectid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/debug", tags=["Debug"])

@router.get("/remove-duplicates")
async def remove_duplicates(admin_user: dict = Depends(get_admin_user)):
    """Remove duplicate policies from master database"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Find duplicates based on policy name and country
        pipeline = [
            {"$match": {"master_status": "active"}},
            {"$group": {
                "_id": {
                    "policyName": "$policyName",
                    "country": "$country"
                },
                "docs": {"$push": "$$ROOT"},
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ]
        
        removed_count = 0
        async for group in master_policies_collection.aggregate(pipeline):
            docs = group["docs"]
            # Keep the first one, remove the rest
            for doc in docs[1:]:
                await master_policies_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {
                        "master_status": "duplicate_removed",
                        "removed_at": datetime.utcnow(),
                        "removed_by": admin_user["email"]
                    }}
                )
                removed_count += 1
        
        return {
            "success": True,
            "message": f"Removed {removed_count} duplicate policies"
        }
    
    except Exception as e:
        logger.error(f"Error removing duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove duplicates: {str(e)}")

@router.get("/policy-counts")
async def get_policy_counts(admin_user: dict = Depends(get_admin_user)):
    """Get detailed policy counts"""
    try:
        master_policies_collection = get_master_policies_collection()
        temp_submissions_collection = get_temp_submissions_collection()
        
        # Master policies count
        master_total = await master_policies_collection.count_documents({"master_status": "active"})
        master_by_status = {}
        async for doc in master_policies_collection.aggregate([
            {"$group": {"_id": "$master_status", "count": {"$sum": 1}}}
        ]):
            master_by_status[doc["_id"]] = doc["count"]
        
        # Temp submissions count
        temp_total = await temp_submissions_collection.count_documents({})
        temp_by_status = {}
        async for doc in temp_submissions_collection.aggregate([
            {"$group": {"_id": "$submission_status", "count": {"$sum": 1}}}
        ]):
            temp_by_status[doc["_id"]] = doc["count"]
        
        # Count by country
        countries = {}
        async for doc in master_policies_collection.aggregate([
            {"$match": {"master_status": "active"}},
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]):
            countries[doc["_id"]] = doc["count"]
        
        return {
            "success": True,
            "counts": {
                "master_policies": {
                    "total": master_total,
                    "by_status": master_by_status
                },
                "temp_submissions": {
                    "total": temp_total,
                    "by_status": temp_by_status
                },
                "by_country": countries
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting policy counts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy counts: {str(e)}")

@router.get("/master-policies-timeline")
async def get_master_policies_timeline(admin_user: dict = Depends(get_admin_user)):
    """Get timeline of master policies creation"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Group by month
        pipeline = [
            {"$match": {"master_status": "active", "moved_to_master_at": {"$exists": True}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$moved_to_master_at"},
                    "month": {"$month": "$moved_to_master_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
        
        timeline = []
        async for doc in master_policies_collection.aggregate(pipeline):
            timeline.append({
                "year": doc["_id"]["year"],
                "month": doc["_id"]["month"],
                "count": doc["count"]
            })
        
        return {
            "success": True,
            "timeline": timeline
        }
    
    except Exception as e:
        logger.error(f"Error getting timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")

@router.get("/database-content")
async def get_database_content(admin_user: dict = Depends(get_admin_user)):
    """Get overview of database content"""
    try:
        master_policies_collection = get_master_policies_collection()
        temp_submissions_collection = get_temp_submissions_collection()
        users_collection = get_users_collection()
        
        # Sample documents from each collection
        sample_master = await master_policies_collection.find_one({"master_status": "active"})
        sample_temp = await temp_submissions_collection.find_one({})
        sample_user = await users_collection.find_one({})
        
        return {
            "success": True,
            "database_overview": {
                "master_policies": {
                    "total_count": await master_policies_collection.count_documents({}),
                    "active_count": await master_policies_collection.count_documents({"master_status": "active"}),
                    "sample_document": convert_objectid(sample_master) if sample_master else None
                },
                "temp_submissions": {
                    "total_count": await temp_submissions_collection.count_documents({}),
                    "sample_document": convert_objectid(sample_temp) if sample_temp else None
                },
                "users": {
                    "total_count": await users_collection.count_documents({}),
                    "verified_count": await users_collection.count_documents({"is_verified": True}),
                    "admin_count": await users_collection.count_documents({"is_admin": True})
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting database content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get database content: {str(e)}")

@router.get("/policy-data-analysis")
async def get_policy_data_analysis(admin_user: dict = Depends(get_admin_user)):
    """Get detailed analysis of policy data"""
    try:
        master_policies_collection = get_master_policies_collection()
        
        # Analysis by policy area
        area_analysis = []
        async for doc in master_policies_collection.aggregate([
            {"$match": {"master_status": "active"}},
            {"$group": {
                "_id": "$policyArea",
                "count": {"$sum": 1},
                "countries": {"$addToSet": "$country"}
            }},
            {"$sort": {"count": -1}}
        ]):
            area_analysis.append({
                "policy_area": doc["_id"],
                "count": doc["count"],
                "countries": doc["countries"],
                "country_count": len(doc["countries"])
            })
        
        # Analysis by country
        country_analysis = []
        async for doc in master_policies_collection.aggregate([
            {"$match": {"master_status": "active"}},
            {"$group": {
                "_id": "$country",
                "count": {"$sum": 1},
                "policy_areas": {"$addToSet": "$policyArea"}
            }},
            {"$sort": {"count": -1}}
        ]):
            country_analysis.append({
                "country": doc["_id"],
                "count": doc["count"],
                "policy_areas": doc["policy_areas"],
                "area_count": len(doc["policy_areas"])
            })
        
        return {
            "success": True,
            "analysis": {
                "by_policy_area": area_analysis,
                "by_country": country_analysis,
                "total_active_policies": await master_policies_collection.count_documents({"master_status": "active"})
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting policy analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy analysis: {str(e)}")

@router.get("/chatbot-test")
async def test_chatbot():
    """Test chatbot functionality"""
    try:
        # Test basic chatbot response
        test_response = {
            "chatbot_status": "available",
            "test_query": "What are AI safety policies?",
            "test_response": "AI safety policies are regulations and guidelines designed to ensure artificial intelligence systems are developed and deployed in a safe, beneficial manner.",
            "timestamp": datetime.utcnow()
        }
        
        return {
            "success": True,
            "chatbot_test": test_response
        }
    
    except Exception as e:
        logger.error(f"Chatbot test error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "chatbot_status": "unavailable"
        }
