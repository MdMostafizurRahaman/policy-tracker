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
    request: Request
):
    """Track a website visit with enhanced browser fingerprinting"""
    try:
        # Parse request body
        body = await request.json()
        user_data = body.get("user_data", None)
        is_new_registration = body.get("is_new_registration", False)
        browser_fingerprint = body.get("browser_fingerprint", {})
        visit_context = body.get("visit_context", {})
        
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
        
        # Create enhanced unique visitor identifier
        fingerprint_components = {
            "ip": client_ip,
            "user_agent": browser_fingerprint.get("userAgent", user_agent),
            "screen_resolution": browser_fingerprint.get("screenResolution", "unknown"),
            "timezone": browser_fingerprint.get("timezone", "unknown"),
            "language": browser_fingerprint.get("language", "unknown"),
            "platform": browser_fingerprint.get("platform", "unknown"),
            "canvas_fingerprint": browser_fingerprint.get("canvasFingerprint", "")[:50],  # Truncate for storage
            "webgl_vendor": browser_fingerprint.get("webglVendor", "unknown"),
            "session_id": browser_fingerprint.get("sessionId", "unknown")
        }
        
        # Generate composite unique identifier
        unique_visitor_id = f"{client_ip}|{fingerprint_components['user_agent'][:100]}|{fingerprint_components['screen_resolution']}|{fingerprint_components['timezone']}"
        
        # For registered users, include user ID in unique identifier
        if user_id:
            unique_visitor_id = f"{unique_visitor_id}|user:{user_id}"
        
        # Create visit record
        visit_record = {
            "visit_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "referrer": referrer,
            "user_type": user_type,
            "user_id": user_id,
            "unique_visitor_id": unique_visitor_id,
            "session_start": datetime.now(timezone.utc).isoformat(),
            "page_path": visit_context.get("current_url", request.url.path if hasattr(request.url, 'path') else "/"),
            "page_title": visit_context.get("page_title", "Unknown"),
            "visit_type": visit_context.get("visit_type", "regular_visit"),
            "is_new_registration": is_new_registration,
            "browser_fingerprint": {
                "screen_resolution": fingerprint_components["screen_resolution"],
                "timezone": fingerprint_components["timezone"],
                "language": fingerprint_components["language"],
                "platform": fingerprint_components["platform"],
                "color_depth": browser_fingerprint.get("screenColorDepth", 0),
                "hardware_concurrency": browser_fingerprint.get("hardwareConcurrency", 0),
                "device_memory": browser_fingerprint.get("deviceMemory", 0),
                "cookie_enabled": browser_fingerprint.get("cookieEnabled", True),
                "session_id": fingerprint_components["session_id"]
            }
        }
        
        # Store in DynamoDB
        await dynamodb.insert_item('visits', visit_record)
        
        if is_new_registration:
            logger.info(f"🎉 New user registration tracked: {user_type} user from {client_ip}")
        else:
            logger.info(f"🆔 Unique visitor ID generated: {unique_visitor_id}")
            logger.info(f"🔍 Browser fingerprint: {user_agent[:50]}...")
            logger.info(f"📱 Screen: {fingerprint_components['screen_resolution']} | Timezone: {fingerprint_components['timezone']}")
            logger.info(f"✅ Visit tracked: {user_type} user from {client_ip}")
        
        return {
            "success": True,
            "message": "Visit tracked successfully",
            "visit_id": visit_record["visit_id"],
            "unique_visitor_id": unique_visitor_id  # Return this for debugging
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
        
        # Count unique visitors (enhanced fingerprinting logic)
        unique_visitors = set()
        
        # Count visits by date (last 30 days)
        daily_visits = {}
        
        for visit in all_visits:
            # Count by user type
            user_type = visit.get("user_type", "viewer")
            if user_type in user_type_counts:
                user_type_counts[user_type] += 1
            
            # Use enhanced unique visitor identification
            if visit.get("unique_visitor_id"):
                # Use the composite unique identifier we created during tracking
                unique_visitors.add(visit["unique_visitor_id"])
            else:
                # Fallback for old records - create composite identifier with "legacy_" prefix
                # to avoid conflicts with new format
                client_ip = visit.get("client_ip", "unknown")
                user_id = visit.get("user_id", "")
                user_agent = visit.get("user_agent", "")[:100]  # Truncate
                
                # Create composite unique identifier with legacy prefix
                if user_id:  # Registered/Admin users
                    unique_id = f"legacy_user_{user_id}"
                else:  # Anonymous visitors - use IP + partial user agent with legacy prefix
                    unique_id = f"legacy_{client_ip}|{user_agent}"
                
                unique_visitors.add(unique_id)
            
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
            "unique_visitors": len(unique_visitors),
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
        
        # Count unique visitors (enhanced fingerprinting logic)
        unique_visitors = set()
        for visit in all_visits:
            # Use enhanced unique visitor identification
            if visit.get("unique_visitor_id"):
                # Use the composite unique identifier we created during tracking
                unique_visitors.add(visit["unique_visitor_id"])
            else:
                # Fallback for old records - create composite identifier with "legacy_" prefix
                # to avoid conflicts with new format
                client_ip = visit.get("client_ip", "unknown")
                user_id = visit.get("user_id", "")
                user_agent = visit.get("user_agent", "")[:100]  # Truncate
                
                # Create composite unique identifier with legacy prefix
                if user_id:  # Registered/Admin users
                    unique_id = f"legacy_user_{user_id}"
                else:  # Anonymous visitors - use IP + partial user agent with legacy prefix
                    unique_id = f"legacy_{client_ip}|{user_agent}"
                
                unique_visitors.add(unique_id)
        
        # Debug counting logic
        new_format_count = sum(1 for visit in all_visits if visit.get("unique_visitor_id"))
        old_format_count = len(all_visits) - new_format_count
        
        logger.info(f"📊 Unique visitor counting: Found {len(unique_visitors)} unique visitors from {len(all_visits)} total visits")
        logger.info(f"🔍 New format visits: {new_format_count}, Old format visits: {old_format_count}")
        logger.info(f"🔍 Sample unique IDs: {list(unique_visitors)[:5]}")  # Show first 5 for debugging
        
        # Show some new format unique IDs if they exist
        new_format_ids = [visit["unique_visitor_id"] for visit in all_visits if visit.get("unique_visitor_id")]
        if new_format_ids:
            logger.info(f"🆔 New format unique IDs (last 3): {new_format_ids[-3:]}")
        
        # Show total unique count breakdown
        unique_from_new = set(visit["unique_visitor_id"] for visit in all_visits if visit.get("unique_visitor_id"))
        logger.info(f"📈 Unique visitors from new format: {len(unique_from_new)}")
        
        return {
            "success": True,
            "total_visits": total_visits,
            "unique_visitors": len(unique_visitors),
            "message": f"Website has been visited {total_visits} times by {len(unique_visitors)} unique visitors"
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
