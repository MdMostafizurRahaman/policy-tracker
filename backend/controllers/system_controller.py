"""
System Controller for debugging and health checks
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from middleware.auth import get_current_user, get_admin_user
from services.policy_service_dynamodb import policy_service
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/health")
async def health_check():
    """System health check"""
    try:
        return {
            "status": "healthy",
            "message": "Policy Tracker API is running",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="System unhealthy")

@router.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to show available routes"""
    return {
        "available_routes": {
            "authentication": [
                "POST /api/auth/register",
                "POST /api/auth/login",
                "GET /api/auth/me"
            ],
            "policy_submission": [
                "POST /api/policy/submit",
                "POST /api/policy/submit-enhanced-form",
                "POST /api/policy/upload-policy-file",
                "POST /api/policy/submit-with-file",
                "GET /api/policy/user-submissions"
            ],
            "admin": [
                "GET /api/admin/submissions",
                "PUT /api/policy/admin/update-status",
                "GET /api/admin/statistics"
            ],
            "map_visualization": [
                "GET /api/policy/approved-for-map",
                "GET /api/policy/country/{country_name}"
            ],
            "ai_analysis": [
                "POST /api/ai-analysis/analyze-policy-document",
                "POST /api/ai-analysis/analyze-uploaded-file",
                "GET /api/ai-analysis/status"
            ]
        }
    }

@router.get("/debug/config")
async def debug_config():
    """Debug endpoint to show system configuration"""
    return {
        "environment_variables": {
            "groq_api_configured": bool(os.getenv('GROQ_API_KEY') and os.getenv('GROQ_API_KEY') != 'gsk_placeholder_key_replace_with_actual_key'),
            "aws_configured": bool(os.getenv('AWS_ACCESS_KEY_ID')),
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "database": {
            "type": "DynamoDB",
            "region": os.getenv("AWS_DYNAMODB_REGION", "us-east-1")
        }
    }

@router.get("/debug/test-db")
async def test_database():
    """Test database connectivity"""
    try:
        # Test policy service
        stats = await policy_service.get_policy_statistics()
        return {
            "database_status": "connected",
            "test_query_result": stats,
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return {
            "database_status": "error",
            "error": str(e),
            "message": "Database connection failed"
        }

@router.get("/debug/submissions-no-auth")
async def debug_submissions_no_auth():
    """Debug endpoint to show submissions WITHOUT authentication (temporary)"""
    try:
        from services.admin_service_dynamodb import admin_service
        result = await admin_service.get_submissions(page=1, limit=50, status="all")
        return {
            "total_submissions": len(result.get("data", [])),
            "submissions": result.get("data", []),
            "database_available": result.get("status") == "success",
            "message": "Retrieved submissions without authentication (debug only)"
        }
    except Exception as e:
        logger.error(f"Error getting submissions: {str(e)}")
        return {
            "error": str(e),
            "message": "Failed to retrieve submissions"
        }

@router.get("/debug/test-admin-auth")
async def debug_test_admin_auth():
    """Debug endpoint to test admin authentication"""
    try:
        # Check what admin users exist
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        users = await db.scan_table('users')
        
        admin_users = []
        for user in users:
            if user.get('role') in ['admin', 'super_admin']:
                admin_users.append({
                    "user_id": user.get("user_id"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                    "is_verified": user.get("is_verified", False)
                })
        
        return {
            "admin_users_found": len(admin_users),
            "admin_users": admin_users,
            "message": "Found admin users - they need to login to get valid tokens",
            "login_endpoint": "/api/auth/login"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to check admin users"
        }

@router.post("/debug/test-submission")
async def debug_test_submission():
    """Debug endpoint to create a test policy submission"""
    try:
        from config.dynamodb import get_dynamodb
        from datetime import datetime
        import uuid
        
        db = await get_dynamodb()
        
        # Get a test user (prefer admin)
        users = await db.scan_table('users')
        test_user = None
        for user in users:
            if user.get('role') in ['admin', 'super_admin']:
                test_user = user
                break
        
        if not test_user and users:
            test_user = users[0]  # Use any user
        
        if not test_user:
            return {"error": "No users found to create test submission"}
        
        # Create test policy submission
        test_policy = {
            "policy_id": str(uuid.uuid4()),
            "user_id": test_user["user_id"],
            "user_email": test_user["email"],
            "country": "Test Country",
            "submission_type": "debug_test",
            "policy_areas": [{
                "area_id": "test_area",
                "area_name": "Test Area",
                "policies": [{
                    "policyName": "Debug Test Policy",
                    "policyDescription": "This is a test policy created for debugging",
                    "targetGroups": ["Government", "Industry"]
                }]
            }],
            "status": "pending_review",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "total_policies": 1,
            "score": 0,
            "completeness_score": 0,
            "admin_notes": ""
        }
        
        # Insert into database
        success = await db.insert_item('policies', test_policy)
        
        if success:
            return {
                "success": True,
                "policy_id": test_policy["policy_id"],
                "message": "Test policy submission created successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to create test policy submission"
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to create test submission"
        }

@router.get("/debug/create-admin-token")
async def debug_create_admin_token():
    """Debug endpoint to create admin token (temporary)"""
    try:
        # Get admin user from database
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        users = await db.scan_table('users')
        
        admin_user = None
        for user in users:
            if user.get('role') in ['admin', 'super_admin']:
                admin_user = user
                break
        
        if not admin_user:
            return {
                "error": "No admin user found",
                "available_users": [{"email": u.get("email"), "role": u.get("role")} for u in users]
            }
        
        # Create a simple token payload (not a real JWT, just for testing)
        token_data = {
            "user_id": admin_user.get("user_id"),
            "email": admin_user.get("email"), 
            "role": admin_user.get("role"),
            "exp": "2025-12-31"  # Far future
        }
        
        return {
            "admin_found": True,
            "admin_email": admin_user.get("email"),
            "admin_role": admin_user.get("role"),
            "token_data": token_data,
            "message": "Admin user found - use this data for authentication"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to find admin user"
        }

@router.get("/debug/pending-submissions")
async def debug_pending_submissions(admin_user: dict = Depends(get_admin_user)):
    """Debug endpoint to show pending submissions for admin"""
    try:
        from services.admin_service_dynamodb import admin_service
        result = await admin_service.get_submissions(page=1, limit=20, status="pending_review")
        return {
            "pending_submissions": result.get("data", []),
            "count": len(result.get("data", [])),
            "message": "Retrieved pending submissions successfully"
        }
    except Exception as e:
        logger.error(f"Error getting pending submissions: {str(e)}")
        return {
            "error": str(e),
            "message": "Failed to retrieve pending submissions"
        }

@router.post("/debug/approve-all-pending")
async def debug_approve_all_pending(admin_user: dict = Depends(get_admin_user)):
    """Debug endpoint to approve all pending submissions (USE WITH CAUTION)"""
    try:
        from services.admin_service_dynamodb import admin_service
        
        # Get all pending submissions
        result = await admin_service.get_submissions(page=1, limit=100, status="pending_review")
        pending_submissions = result.get("data", [])
        
        approved_count = 0
        for submission in pending_submissions:
            try:
                status_update = {
                    "submission_id": submission["policy_id"],
                    "status": "approved",
                    "admin_notes": "Auto-approved via debug endpoint"
                }
                await policy_service.update_policy_status(status_update, admin_user)
                approved_count += 1
            except Exception as e:
                logger.warning(f"Failed to approve submission {submission['policy_id']}: {str(e)}")
        
        return {
            "message": f"Approved {approved_count} submissions",
            "approved_count": approved_count,
            "total_pending": len(pending_submissions)
        }
        
    except Exception as e:
        logger.error(f"Error in bulk approval: {str(e)}")
        return {
            "error": str(e),
            "message": "Failed to perform bulk approval"
        }

# Export router
system_router = router
