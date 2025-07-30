"""
Visit Tracking Controller
Handles HTTP requests for tracking website visits and providing visit statistics
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime, timezone
import uuid
from config.dynamodb import get_dynamodb

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/visits", tags=["Visits"])

@router.post("/track")
async def track_visit(
    request: Request,
    user_data: Dict[str, Any] = None
):
    """Track a website visit"""
    try:
        dynamodb = await get_dynamodb()
        
        # Get client info
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "Unknown")
        referrer = request.headers.get("referer", "Direct")
        
        # Determine user type
        user_type = "viewer"  # Default
        user_id = None
        
        if user_data:
            if user_data.get("is_admin") or user_data.get("role") == "admin":
                user_type = "admin"
            elif user_data.get("user_id") or user_data.get("email"):
                user_type = "registered"
            user_id = user_data.get("user_id") or user_data.get("email")
        
        # Create visit record
        visit_record = {
            "visit_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "referrer": referrer,
            "user_type": user_type,
            "user_id": user_id,
            "session_start": datetime.now(timezone.utc).isoformat(),
            "page_path": request.url.path if hasattr(request.url, 'path') else "/"
        }
        
        # Store in DynamoDB
        await dynamodb.insert_item('visits', visit_record)
        
        logger.info(f"✅ Visit tracked: {user_type} user from {client_ip}")
        
        return {
            "success": True,
            "message": "Visit tracked successfully",
            "visit_id": visit_record["visit_id"]
        }
        
    except Exception as e:
        logger.error(f"Error tracking visit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to track visit: {str(e)}")

@router.get("/statistics")
async def get_visit_statistics():
    """Get comprehensive visit statistics"""
    try:
        dynamodb = await get_dynamodb()
        
        # Get all visits
        all_visits = await dynamodb.scan_table('visits')
        
        # Calculate statistics
        total_visits = len(all_visits)
        
        # Count by user type
        user_type_counts = {
            "viewer": 0,
            "registered": 0, 
            "admin": 0
        }
        
        # Count unique visitors by IP
        unique_ips = set()
        
        # Count visits by date (last 30 days)
        daily_visits = {}
        
        for visit in all_visits:
            # Count by user type
            user_type = visit.get("user_type", "viewer")
            if user_type in user_type_counts:
                user_type_counts[user_type] += 1
            
            # Count unique IPs
            if visit.get("client_ip"):
                unique_ips.add(visit.get("client_ip"))
            
            # Count daily visits
            try:
                visit_date = visit.get("timestamp", "")[:10]  # Get YYYY-MM-DD part
                if visit_date:
                    daily_visits[visit_date] = daily_visits.get(visit_date, 0) + 1
            except:
                pass
        
        # Get today's visits
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_visits = daily_visits.get(today, 0)
        
        statistics = {
            "total_visits": total_visits,
            "unique_visitors": len(unique_ips),
            "today_visits": today_visits,
            "user_type_breakdown": user_type_counts,
            "daily_visits": daily_visits,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"📊 Visit statistics retrieved: {total_visits} total visits")
        
        return {
            "success": True,
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"Error getting visit statistics: {str(e)}")
        # Return default statistics on error
        return {
            "success": False,
            "statistics": {
                "total_visits": 0,
                "unique_visitors": 0,
                "today_visits": 0,
                "user_type_breakdown": {
                    "viewer": 0,
                    "registered": 0,
                    "admin": 0
                },
                "daily_visits": {},
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        }

@router.get("/summary")
async def get_visit_summary():
    """Get simple visit summary for display on home page"""
    try:
        dynamodb = await get_dynamodb()
        
        # Get all visits
        all_visits = await dynamodb.scan_table('visits')
        total_visits = len(all_visits)
        
        # Count unique visitors
        unique_ips = set()
        for visit in all_visits:
            if visit.get("client_ip"):
                unique_ips.add(visit.get("client_ip"))
        
        return {
            "success": True,
            "total_visits": total_visits,
            "unique_visitors": len(unique_ips),
            "message": f"Website has been visited {total_visits} times by {len(unique_ips)} unique visitors"
        }
        
    except Exception as e:
        logger.error(f"Error getting visit summary: {str(e)}")
        return {
            "success": False,
            "total_visits": 0,
            "unique_visitors": 0,
            "message": "Visit data unavailable",
            "error": str(e)
        }

# Export router
visit_router = router
