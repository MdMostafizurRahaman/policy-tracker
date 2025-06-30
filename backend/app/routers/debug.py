"""
Debug routes for development and troubleshooting
"""
from fastapi import APIRouter, HTTPException, Depends, status
from routers.auth import get_current_user
from models.user import UserResponse
from config.database import get_database
from services.chatbot_service import get_chatbot_service
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

router = APIRouter()

def get_policies_collection():
    """Get policies collection"""
    db = get_database()
    return db.temp_submissions

def get_master_policies_collection():
    """Get master policies collection"""
    db = get_database()
    return db.master_policies

async def require_admin(current_user: UserResponse = Depends(get_current_user)):
    """Require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/remove-duplicates")
async def remove_duplicates(
    admin_user: UserResponse = Depends(require_admin),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Remove duplicate policies from master collection"""
    try:
        # Get all policies
        policies = await master_policies_collection.find({}).to_list(length=None)
        
        # Group by title and country for duplicate detection
        policy_groups = defaultdict(list)
        for policy in policies:
            key = (policy.get('title', '').lower().strip(), policy.get('country', '').lower().strip())
            policy_groups[key].append(policy)
        
        duplicates_removed = 0
        for key, group in policy_groups.items():
            if len(group) > 1:
                # Keep the most recent one, remove others
                group.sort(key=lambda x: x.get('submittedAt', datetime.min), reverse=True)
                for duplicate in group[1:]:
                    await master_policies_collection.delete_one({"_id": duplicate["_id"]})
                    duplicates_removed += 1
        
        return {
            "message": f"Removed {duplicates_removed} duplicate policies",
            "duplicates_removed": duplicates_removed
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove duplicates: {str(e)}"
        )

@router.get("/policy-counts")
async def get_policy_counts(
    admin_user: UserResponse = Depends(require_admin),
    policies_collection = Depends(get_policies_collection),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Get detailed policy counts and statistics"""
    try:
        # Count temp submissions by status
        temp_counts = {}
        for status in ['pending', 'approved', 'rejected']:
            temp_counts[status] = await policies_collection.count_documents({"status": status})
        
        # Count master policies
        master_count = await master_policies_collection.count_documents({})
        
        # Get country distribution in master policies
        country_pipeline = [
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        country_distribution = await master_policies_collection.aggregate(country_pipeline).to_list(length=None)
        
        # Get policy area distribution
        area_pipeline = [
            {"$group": {"_id": "$policyArea", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        area_distribution = await master_policies_collection.aggregate(area_pipeline).to_list(length=None)
        
        return {
            "temp_submissions": temp_counts,
            "master_policies": master_count,
            "country_distribution": country_distribution,
            "policy_area_distribution": area_distribution,
            "total_policies": sum(temp_counts.values()) + master_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get policy counts: {str(e)}"
        )

@router.get("/policy-data-analysis")
async def policy_data_analysis(
    admin_user: UserResponse = Depends(require_admin),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Analyze policy data for insights"""
    try:
        policies = await master_policies_collection.find({}).to_list(length=None)
        
        # Analyze submission trends
        monthly_submissions = defaultdict(int)
        country_counts = Counter()
        area_counts = Counter()
        
        for policy in policies:
            submitted_at = policy.get('submittedAt')
            if submitted_at:
                month_key = submitted_at.strftime('%Y-%m')
                monthly_submissions[month_key] += 1
            
            country_counts[policy.get('country', 'Unknown')] += 1
            area_counts[policy.get('policyArea', 'Unknown')] += 1
        
        # Data quality analysis
        quality_metrics = {
            "policies_with_description": sum(1 for p in policies if p.get('description')),
            "policies_with_url": sum(1 for p in policies if p.get('url')),
            "policies_with_date": sum(1 for p in policies if p.get('implementationDate')),
            "average_description_length": sum(len(p.get('description', '')) for p in policies) / len(policies) if policies else 0
        }
        
        return {
            "total_policies": len(policies),
            "monthly_trends": dict(monthly_submissions),
            "top_countries": dict(country_counts.most_common(10)),
            "top_policy_areas": dict(area_counts.most_common(10)),
            "data_quality": quality_metrics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze policy data: {str(e)}"
        )

@router.get("/master-policies-timeline")
async def master_policies_timeline(
    admin_user: UserResponse = Depends(require_admin),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Get timeline of master policies"""
    try:
        # Get policies with submission dates
        pipeline = [
            {"$match": {"submittedAt": {"$exists": True}}},
            {"$sort": {"submittedAt": 1}},
            {"$project": {
                "title": 1,
                "country": 1,
                "policyArea": 1,
                "submittedAt": 1,
                "implementationDate": 1
            }}
        ]
        
        timeline = await master_policies_collection.aggregate(pipeline).to_list(length=None)
        
        # Group by month for trend analysis
        monthly_stats = defaultdict(lambda: {"count": 0, "countries": set(), "areas": set()})
        
        for policy in timeline:
            month_key = policy['submittedAt'].strftime('%Y-%m')
            monthly_stats[month_key]["count"] += 1
            monthly_stats[month_key]["countries"].add(policy.get('country', 'Unknown'))
            monthly_stats[month_key]["areas"].add(policy.get('policyArea', 'Unknown'))
        
        # Convert sets to counts
        monthly_summary = {}
        for month, stats in monthly_stats.items():
            monthly_summary[month] = {
                "policy_count": stats["count"],
                "unique_countries": len(stats["countries"]),
                "unique_areas": len(stats["areas"])
            }
        
        return {
            "timeline": timeline,
            "monthly_summary": monthly_summary,
            "total_policies": len(timeline)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timeline: {str(e)}"
        )

@router.get("/database-content")
async def database_content(
    admin_user: UserResponse = Depends(require_admin)
):
    """Get overview of all database collections"""
    try:
        db = get_database()
        
        # Get all collection names
        collections = await db.list_collection_names()
        
        collection_info = {}
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            
            # Get sample document structure
            sample = await collection.find_one({})
            sample_keys = list(sample.keys()) if sample else []
            
            collection_info[collection_name] = {
                "document_count": count,
                "sample_fields": sample_keys
            }
        
        return {
            "collections": collection_info,
            "total_collections": len(collections)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database content: {str(e)}"
        )

@router.get("/chatbot-test")
async def test_chatbot(
    query: str = "What are the environmental policies in the database?",
    chatbot_service = Depends(get_chatbot_service)
):
    """Test chatbot functionality"""
    try:
        # Test basic chatbot response
        response = await chatbot_service.generate_response(query)
        
        # Test policy search
        policies = await chatbot_service.search_policies(query, limit=5)
        
        return {
            "query": query,
            "chatbot_response": response,
            "related_policies_count": len(policies),
            "sample_policies": policies[:2] if policies else [],
            "test_status": "success"
        }
        
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "test_status": "failed"
        }

@router.post("/fix-visibility")
async def fix_policy_visibility(
    admin_user: UserResponse = Depends(require_admin),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Fix policy visibility settings"""
    try:
        # Update all policies to have proper visibility
        result = await master_policies_collection.update_many(
            {"isPublic": {"$exists": False}},
            {"$set": {"isPublic": True}}
        )
        
        return {
            "message": f"Updated {result.modified_count} policies with visibility settings",
            "modified_count": result.modified_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix visibility: {str(e)}"
        )
