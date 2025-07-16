"""
Admin Controller
Handles HTTP requests for admin operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
import logging
import time
import uuid
import traceback
import asyncio
from datetime import datetime

from middleware.auth import get_admin_user, get_current_user
from services.admin_service_dynamodb import admin_service
from services.policy_service_dynamodb import policy_service
from utils.helpers import convert_objectid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/submissions")
async def get_admin_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query("all"),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all submissions for admin review with pagination"""
    try:
        return await admin_service.get_submissions(page=page, limit=limit, status=status)
    except Exception as e:
        logger.error(f"Error getting admin submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")

@router.get("/admin-dashboard-data")
async def get_admin_dashboard_data():
    """Get comprehensive admin dashboard data including submissions, map data, and statistics"""
    try:
        logger.info("Getting comprehensive admin dashboard data")
        
        # Get submissions with user data and enhanced country status
        submissions_result = await get_submissions_with_country_status(page=1, limit=50, status="all")
        
        # Get map visualization data with area-based point system (only approved policies)
        try:
            from config.dynamodb import get_dynamodb
            db = await get_dynamodb()
            
            # Get only approved policies from map_policies table
            map_policies = await db.scan_table('map_policies')
            approved_map_policies = [p for p in map_policies if p.get('status') == 'approved']
            
            # Group by country and calculate area points
            country_data = {}
            
            for policy in approved_map_policies:
                country = policy.get('country', 'Unknown')
                area = policy.get('policy_area', 'Unknown Area')
                
                if country not in country_data:
                    country_data[country] = {
                        'country': country,
                        'areas': {},  # Track areas with approved policies
                        'total_approved_policies': 0
                    }
                
                # Track this area (each area gets max 1 point regardless of policy count)
                if area not in country_data[country]['areas']:
                    country_data[country]['areas'][area] = {
                        'area_name': area,
                        'approved_policies': []
                    }
                
                # Add policy to area
                country_data[country]['areas'][area]['approved_policies'].append({
                    'policy_name': policy.get('policy_name', ''),
                    'policy_description': policy.get('policy_description', ''),
                    'approved_at': policy.get('approved_at', '')
                })
                
                country_data[country]['total_approved_policies'] += 1
            
            # Calculate final country statistics with area-based coloring
            countries_list = []
            
            for country, data in country_data.items():
                area_points = len(data['areas'])  # Number of areas with approved policies
                
                # Updated color system: 1-3 red, 4-7 yellow, 8-10 green
                if area_points == 0:
                    color = 'gray'
                    level = 'no_approved_areas'
                elif area_points <= 3:
                    color = 'red'
                    level = 'low'
                elif area_points <= 7:
                    color = 'yellow'
                    level = 'medium'
                else:
                    color = 'green'
                    level = 'high'
                
                countries_list.append({
                    'country': country,
                    'area_points': area_points,  # Key metric for coloring
                    'total_approved_policies': data['total_approved_policies'],
                    'areas_with_approved_policies': list(data['areas'].keys()),
                    'areas_detail': list(data['areas'].values()),
                    'color': color,
                    'level': level,
                    'status': 'approved' if area_points > 0 else 'no_approved_policies'
                })
            
            map_data = {
                "success": True,
                "countries": countries_list,
                "total_countries": len(countries_list),
                "total_approved_policies": sum(c['total_approved_policies'] for c in countries_list),
                "area_point_system": {
                    "explanation": "Each area gets 1 point if it has at least one approved policy",
                    "color_coding": "Based on total area points per country"
                },
                "color_legend": {
                    "gray": "No approved areas (0 points)",
                    "red": "Low: 1-3 approved areas", 
                    "yellow": "Medium: 4-7 approved areas",
                    "green": "High: 8-10 approved areas"
                },
                "data_source": "Only approved policies from map_policies table"
            }
        except Exception as e:
            logger.warning(f"Could not get map data: {e}")
            map_data = {"countries": [], "total_countries": 0, "total_policies": 0}
        
        # Get basic statistics - from actual DynamoDB data
        try:
            from config.dynamodb import get_dynamodb
            db = await get_dynamodb()
            
            # Get real statistics from DynamoDB
            statistics = {
                "users": {"total": 0, "verified": 0, "admin": 0},
                "submissions": {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "under_review": 0},
                "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0},
                "countries_with_policies": 0,
                "total_policies": 0
            }
            
            # Count users
            all_users = await db.scan_table('users')
            statistics["users"]["total"] = len(all_users)
            for user in all_users:
                if user.get("role") == "admin":
                    statistics["users"]["admin"] += 1
                if user.get("verified", False):
                    statistics["users"]["verified"] += 1
            
            # Count submissions and their statuses
            all_submissions = await db.scan_table('policies')
            statistics["submissions"]["total"] = len(all_submissions)
            
            for submission in all_submissions:
                status = submission.get("status", "pending").lower()
                if status in statistics["submissions"]:
                    statistics["submissions"][status] += 1
            
            # Count all policies from submissions (individual policies within areas)
            total_individual_policies = 0
            approved_individual_policies = 0
            rejected_individual_policies = 0
            pending_individual_policies = 0
            
            for submission in all_submissions:
                for area in submission.get("policy_areas", []):
                    for policy in area.get("policies", []):
                        total_individual_policies += 1
                        policy_status = policy.get("status", "pending").lower()
                        if policy_status == "approved":
                            approved_individual_policies += 1
                        elif policy_status == "rejected":
                            rejected_individual_policies += 1
                        else:
                            pending_individual_policies += 1
            
            # Count master policies (if they exist in a separate table)
            try:
                master_policies = await db.scan_table('master_policies')
                statistics["policies"]["master"] = len(master_policies)
            except:
                statistics["policies"]["master"] = 0
            
            # Update policy statistics with individual policy counts
            statistics["policies"]["approved"] = approved_individual_policies
            statistics["policies"]["rejected"] = rejected_individual_policies
            statistics["policies"]["under_review"] = pending_individual_policies
            statistics["total_policies"] = total_individual_policies
            
            # Set countries count from map data
            statistics["countries_with_policies"] = map_data.get("total_countries", 0)
            
            logger.info(f"✅ Statistics calculated: {statistics}")
            
        except Exception as e:
            logger.warning(f"Could not get detailed statistics: {e}")
            statistics = {
                "users": {"total": 1, "verified": 1, "admin": 1},
                "submissions": {"total": len(submissions_result.get("data", [])), "pending": 0, "approved": 0, "rejected": 0, "under_review": 0},
                "policies": {"master": 0, "approved": map_data.get("total_policies", 0), "rejected": 0, "under_review": 0},
                "countries_with_policies": map_data.get("total_countries", 0)
            }
            
            # Count submission statuses from fetched data
            for submission in submissions_result.get("data", []):
                status = submission.get("status", "pending").lower()
                if status in statistics["submissions"]:
                    statistics["submissions"][status] += 1
        
        return {
            "success": True,
            "data": {
                "submissions": submissions_result,
                "map_visualization": map_data,
                "statistics": statistics,
                "timestamp": datetime.now().isoformat()
            },
            "debug_info": {
                "endpoint": "admin-dashboard-data",
                "provides": ["submissions_with_user_data", "map_visualization", "statistics"],
                "authentication": "bypassed for debugging"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard data: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "submissions": {"data": [], "total": 0},
                "map_visualization": {"countries": [], "total_countries": 0, "total_policies": 0},
                "statistics": {}
            }
        }

@router.get("/dynamic-statistics")
async def get_dynamic_statistics():
    """Get fully dynamic statistics from DynamoDB for admin dashboard"""
    try:
        logger.info("📊 Getting dynamic statistics from DynamoDB")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Initialize statistics
        stats = {
            "users": {"total": 0, "verified": 0, "admin": 0},
            "submissions": {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "under_review": 0},
            "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0, "total": 0},
            "countries_with_policies": 0,
            "map_data": {"total_approved_policies": 0, "total_countries": 0}
        }
        
        # Count users
        all_users = await db.scan_table('users')
        stats["users"]["total"] = len(all_users)
        
        for user in all_users:
            if user.get("role") == "admin":
                stats["users"]["admin"] += 1
            if user.get("verified", False):
                stats["users"]["verified"] += 1
        
        # Count submissions
        all_submissions = await db.scan_table('policies')
        stats["submissions"]["total"] = len(all_submissions)
        
        # Count individual policies within submissions
        total_policies = 0
        approved_policies = 0
        rejected_policies = 0
        pending_policies = 0
        
        for submission in all_submissions:
            # Count submission status
            submission_status = submission.get("status", "pending").lower()
            if submission_status in stats["submissions"]:
                stats["submissions"][submission_status] += 1
            
            # Count individual policies within areas
            for area in submission.get("policy_areas", []):
                for policy in area.get("policies", []):
                    total_policies += 1
                    policy_status = policy.get("status", "pending").lower()
                    if policy_status == "approved":
                        approved_policies += 1
                    elif policy_status == "rejected":
                        rejected_policies += 1
                    else:
                        pending_policies += 1
        
        stats["policies"]["total"] = total_policies
        stats["policies"]["approved"] = approved_policies
        stats["policies"]["rejected"] = rejected_policies
        stats["policies"]["under_review"] = pending_policies
        
        # Count master policies
        try:
            master_policies = await db.scan_table('master_policies')
            stats["policies"]["master"] = len(master_policies)
        except:
            stats["policies"]["master"] = 0
        
        # Get map data
        try:
            map_policies = await db.scan_table('map_policies')
            approved_map_policies = [p for p in map_policies if p.get('status') == 'approved']
            
            countries = set()
            for policy in approved_map_policies:
                countries.add(policy.get('country', 'Unknown'))
            
            stats["map_data"]["total_approved_policies"] = len(approved_map_policies)
            stats["map_data"]["total_countries"] = len(countries)
            stats["countries_with_policies"] = len(countries)
        except Exception as e:
            logger.warning(f"Could not get map data: {e}")
            stats["countries_with_policies"] = 0
        
        return {
            "success": True,
            "statistics": stats,
            "summary": {
                "pending_submissions": stats["submissions"]["pending"],
                "under_review_policies": stats["policies"]["under_review"],
                "approved_policies": stats["policies"]["approved"],
                "master_policies": stats["policies"]["master"],
                "countries_with_policies": stats["countries_with_policies"],
                "total_policies": stats["policies"]["total"]
            },
            "timestamp": datetime.now().isoformat(),
            "data_source": "Dynamic calculation from DynamoDB"
        }
        
    except Exception as e:
        logger.error(f"❌ Dynamic statistics failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "statistics": {
                "users": {"total": 0, "verified": 0, "admin": 0},
                "submissions": {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "under_review": 0},
                "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0, "total": 0},
                "countries_with_policies": 0
            }
        }

@router.get("/search")
async def search_submissions(
    query: str = Query("", description="Search query for country, policy name, or policy ID"),
    status: str = Query("all", description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Search across all submissions and policies with filters"""
    try:
        logger.info(f"Searching with query: '{query}', status: '{status}'")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Get all submissions from DynamoDB
        all_submissions = await db.scan_table('policies')
        
        # Enhance with user data
        for submission in all_submissions:
            user_id = submission.get("user_id")
            if user_id:
                try:
                    user = await db.get_item('users', {'user_id': user_id})
                    if user:
                        submission["user_name"] = user.get("name", "Unknown User")
                        submission["user_full_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                        if not submission["user_full_name"]:
                            submission["user_full_name"] = user.get("name", "Unknown User")
                    else:
                        submission["user_name"] = "User Not Found"
                        submission["user_full_name"] = "User Not Found"
                except Exception as e:
                    submission["user_name"] = "Unknown User"
                    submission["user_full_name"] = "Unknown User"
        
        # Apply search filters
        filtered_submissions = []
        
        for submission in all_submissions:
            # Status filter
            if status != "all" and submission.get("status", "").lower() != status.lower():
                continue
                
            # Search query filter
            if query:
                query_lower = query.lower()
                match = False
                
                # Search in submission fields
                if (query_lower in submission.get("country", "").lower() or
                    query_lower in submission.get("policy_id", "").lower() or
                    query_lower in submission.get("user_email", "").lower() or
                    query_lower in submission.get("user_name", "").lower()):
                    match = True
                
                # Search in policy areas and individual policies
                if not match:
                    for area in submission.get("policy_areas", []):
                        if query_lower in area.get("area_name", "").lower():
                            match = True
                            break
                            
                        for policy in area.get("policies", []):
                            if (query_lower in policy.get("policyName", "").lower() or
                                query_lower in policy.get("policyDescription", "").lower() or
                                query_lower in policy.get("policyId", "").lower()):
                                match = True
                                break
                        
                        if match:
                            break
                
                if not match:
                    continue
            
            filtered_submissions.append(submission)
        
        # Apply pagination
        total = len(filtered_submissions)
        start = (page - 1) * limit
        end = start + limit
        paginated_submissions = filtered_submissions[start:end]
        
        return {
            "status": "success",
            "data": paginated_submissions,
            "total": total,
            "page": page,
            "limit": limit,
            "filtered_by": status,
            "search_query": query,
            "total_pages": (total + limit - 1) // limit,
            "debug_info": {
                "endpoint": "search",
                "authentication": "bypassed for debugging",
                "timestamp": datetime.now().isoformat(),
                "enhanced_with_user_data": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search submissions: {str(e)}")

@router.get("/submissions-with-country-status")
async def get_submissions_with_country_status(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query("all")
):
    """Get submissions with proper country and individual policy status calculation"""
    try:
        logger.info("Getting submissions with country status calculation")
        
        # Get base submissions with user data
        result = await get_admin_submissions_debug(page=page, limit=limit, status=status)
        
        # Calculate both individual policy status and country-level status
        for submission in result.get("data", []):
            # Calculate individual policy statuses within areas
            for area in submission.get("policy_areas", []):
                individual_policies = area.get("policies", [])
                
                if not individual_policies:
                    area["area_status"] = "no_policies"
                    continue
                
                # Count individual policy statuses
                approved_count = 0
                rejected_count = 0
                pending_count = 0
                
                for policy in individual_policies:
                    policy_status = policy.get("status", "pending").lower()
                    if policy_status == "approved":
                        approved_count += 1
                    elif policy_status == "rejected":
                        rejected_count += 1
                    else:
                        pending_count += 1
                
                # Area status logic: if at least one policy is approved, area is approved
                if approved_count > 0:
                    area["area_status"] = "approved"
                elif rejected_count == len(individual_policies):
                    area["area_status"] = "rejected"
                else:
                    area["area_status"] = "pending"
                
                area["policy_counts"] = {
                    "total": len(individual_policies),
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "pending": pending_count
                }
            
            # Calculate country-level status (submission status)
            all_policies = []
            for area in submission.get("policy_areas", []):
                all_policies.extend(area.get("policies", []))
            
            if all_policies:
                total_approved = sum(1 for p in all_policies if p.get("status", "").lower() == "approved")
                total_policies = len(all_policies)
                
                if total_approved == total_policies:
                    submission["country_status"] = "fully_approved"  # All policies approved
                elif total_approved > 0:
                    submission["country_status"] = "approved"  # At least one approved
                else:
                    submission["country_status"] = "pending"  # No approved policies
                
                submission["country_policy_summary"] = {
                    "total_policies": total_policies,
                    "approved_policies": total_approved,
                    "pending_policies": total_policies - total_approved
                }
            else:
                submission["country_status"] = "no_policies"
                submission["country_policy_summary"] = {"total_policies": 0, "approved_policies": 0, "pending_policies": 0}
        
        # Add status explanation to result
        result["status_explanation"] = {
            "country_status": {
                "fully_approved": "All policies in this country submission are approved",
                "approved": "At least one policy is approved (but not all)",
                "pending": "No policies are approved yet",
                "no_policies": "No policies submitted"
            },
            "individual_policy_status": "Each policy keeps its own status (approved/pending/rejected)"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting submissions with country status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")

@router.get("/submissions-with-area-status")
async def get_submissions_with_area_status(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query("all")
):
    """Get submissions with proper policy area status calculation"""
    try:
        logger.info("Getting submissions with calculated area status")
        
        # Get base submissions with user data
        result = await get_admin_submissions_debug(page=page, limit=limit, status=status)
        
        # Calculate policy area statuses based on individual policy statuses
        for submission in result.get("data", []):
            for area in submission.get("policy_areas", []):
                individual_policies = area.get("policies", [])
                
                if not individual_policies:
                    area["area_status"] = "no_policies"
                    continue
                
                # Check individual policy statuses
                approved_count = 0
                rejected_count = 0
                pending_count = 0
                
                for policy in individual_policies:
                    policy_status = policy.get("status", "pending").lower()
                    if policy_status == "approved":
                        approved_count += 1
                    elif policy_status == "rejected":
                        rejected_count += 1
                    else:
                        pending_count += 1
                
                # Policy area status logic:
                # If at least one policy is approved, the area is considered approved
                # But individual policies keep their inherent status
                if approved_count > 0:
                    area["area_status"] = "approved"
                elif rejected_count == len(individual_policies):
                    area["area_status"] = "rejected"  # All policies rejected
                elif pending_count > 0:
                    area["area_status"] = "pending"  # Some policies still pending
                else:
                    area["area_status"] = "under_review"
                
                # Add counts for transparency
                area["policy_counts"] = {
                    "total": len(individual_policies),
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "pending": pending_count
                }
        
        # Add area status summary to result
        result["area_status_info"] = {
            "logic": "If at least one policy in an area is approved, the whole area is considered approved",
            "individual_policies": "Keep their inherent status (approved/rejected/pending)"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting submissions with area status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")

@router.post("/clean-map-duplicates")
async def clean_map_duplicates():
    """Clean duplicate entries from map_policies table"""
    try:
        logger.info("🧹 Cleaning duplicate map entries")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Get all map policies
        all_map_policies = await db.scan_table('map_policies')
        logger.info(f"Found {len(all_map_policies)} map policies")
        
        # Group by parent_submission_id and policy_name to find duplicates
        grouped = {}
        for policy in all_map_policies:
            key = f"{policy.get('parent_submission_id')}_{policy.get('policy_name')}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(policy)
        
        # Keep only the latest entry for each group and delete duplicates
        deleted_count = 0
        kept_count = 0
        
        for key, policies in grouped.items():
            if len(policies) > 1:
                # Sort by approved_at (keep the latest)
                policies.sort(key=lambda x: x.get('approved_at', ''), reverse=True)
                keep_policy = policies[0]  # Keep the latest
                delete_policies = policies[1:]  # Delete the rest
                
                for policy_to_delete in delete_policies:
                    await db.delete_item('map_policies', {'map_policy_id': policy_to_delete['map_policy_id']})
                    deleted_count += 1
                    logger.info(f"Deleted duplicate: {policy_to_delete['map_policy_id']}")
                
                kept_count += 1
            else:
                kept_count += 1
        
        return {
            "success": True,
            "message": f"Cleaned map duplicates: deleted {deleted_count}, kept {kept_count}",
            "deleted_count": deleted_count,
            "kept_count": kept_count,
            "total_before": len(all_map_policies)
        }
        
    except Exception as e:
        logger.error(f"❌ Clean duplicates failed: {str(e)}")
        return {"success": False, "error": str(e)}

@router.post("/sync-map-with-approved-policies")
async def sync_map_with_approved_policies():
    """Sync map_policies table with only approved individual policies and implement area point system"""
    try:
        logger.info("🗺️ Syncing map with approved policies only")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Step 1: Clear existing map_policies table
        logger.info("Step 1: Clearing existing map policies...")
        all_map_policies = await db.scan_table('map_policies')
        for map_policy in all_map_policies:
            await db.delete_item('map_policies', {'map_policy_id': map_policy['map_policy_id']})
        
        # Step 2: Get all policies and extract only approved individual policies
        logger.info("Step 2: Getting approved individual policies...")
        all_policies = await db.scan_table('policies')
        
        approved_count = 0
        area_points = {}  # Track points per area per country
        
        for policy in all_policies:
            country = policy.get('country', 'Unknown')
            if country not in area_points:
                area_points[country] = {}
            
            # Check each policy area
            for area in policy.get("policy_areas", []):
                area_name = area.get("area_name", "Unknown Area")
                area_has_approved = False
                
                # Check individual policies in this area
                for individual_policy in area.get("policies", []):
                    if individual_policy.get("status", "").lower() == "approved":
                        area_has_approved = True
                        
                        # Create map entry for this approved policy
                        map_policy_entry = {
                            "map_policy_id": str(uuid.uuid4()),
                            "parent_submission_id": policy["policy_id"],
                            "policy_name": individual_policy.get("policyName", ""),
                            "policy_description": individual_policy.get("policyDescription", ""),
                            "country": country,
                            "policy_area": area_name,
                            "target_groups": individual_policy.get("targetGroups", []),
                            "policy_link": individual_policy.get("policyLink", ""),
                            "implementation": individual_policy.get("implementation", {}),
                            "evaluation": individual_policy.get("evaluation", {}),
                            "participation": individual_policy.get("participation", {}),
                            "alignment": individual_policy.get("alignment", {}),
                            "status": "approved",  # Only approved policies
                            "visible_on_map": True,
                            "approved_at": datetime.utcnow().isoformat(),
                            "created_at": datetime.utcnow().isoformat(),
                            "user_id": policy.get("user_id", ""),
                            "user_email": policy.get("user_email", "")
                        }
                        
                        await db.insert_item('map_policies', map_policy_entry)
                        approved_count += 1
                
                # Area gets 1 point if at least one policy is approved
                if area_has_approved and area_name not in area_points[country]:
                    area_points[country][area_name] = 1
        
        # Step 3: Calculate country colors based on area points
        logger.info("Step 3: Calculating area-based colors...")
        country_stats = []
        
        for country, areas in area_points.items():
            total_area_points = len(areas)  # Number of areas with at least one approved policy
            
            # Updated color system: 1-3 red, 4-7 yellow, 8-10 green
            if total_area_points == 0:
                color = 'gray'
                level = 'no_approved_areas'
            elif total_area_points <= 3:
                color = 'red'
                level = 'low'
            elif total_area_points <= 7:
                color = 'yellow'
                level = 'medium'
            else:
                color = 'green'
                level = 'high'
            
            country_stats.append({
                "country": country,
                "area_points": total_area_points,
                "areas_with_approved_policies": list(areas.keys()),
                "color": color,
                "level": level
            })
        
        return {
            "success": True,
            "message": f"Map synced with {approved_count} approved policies",
            "approved_policies_added": approved_count,
            "countries_processed": len(area_points),
            "area_point_system": {
                "explanation": "Each area gets 1 point if at least one policy in that area is approved",
                "coloring": "Based on total area points per country (not individual policy count)"
            },
            "country_statistics": country_stats,
            "color_legend": {
                "gray": "No approved areas (0 points)",
                "red": "Low: 1-3 approved areas",
                "yellow": "Medium: 4-7 approved areas",
                "green": "High: 8-10 approved areas"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Map sync failed: {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/map-visualization-with-area-points")
async def get_map_visualization_with_area_points():
    """Get map visualization data with area-based point system (only approved policies)"""
    try:
        logger.info("🗺️ Getting map visualization with area point system")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Get only approved policies from map_policies table
        map_policies = await db.scan_table('map_policies')
        approved_map_policies = [p for p in map_policies if p.get('status') == 'approved']
        
        # Group by country and calculate area points
        country_data = {}
        
        for policy in approved_map_policies:
            country = policy.get('country', 'Unknown')
            area = policy.get('policy_area', 'Unknown Area')
            
            if country not in country_data:
                country_data[country] = {
                    'country': country,
                    'areas': {},  # Track areas with approved policies
                    'total_approved_policies': 0,
                    'area_points': 0
                }
            
            # Track this area (each area gets max 1 point regardless of policy count)
            if area not in country_data[country]['areas']:
                country_data[country]['areas'][area] = {
                    'area_name': area,
                    'approved_policies': [],
                    'has_approved': True  # This area has at least one approved policy
                }
            
            # Add policy to area
            country_data[country]['areas'][area]['approved_policies'].append({
                'policy_name': policy.get('policy_name', ''),
                'policy_description': policy.get('policy_description', ''),
                'approved_at': policy.get('approved_at', '')
            })
            
            country_data[country]['total_approved_policies'] += 1
        
        # Calculate final country statistics with area-based coloring
        countries_list = []
        
        for country, data in country_data.items():
            area_points = len(data['areas'])  # Number of areas with approved policies
            
            # Updated color system: 1-3 red, 4-7 yellow, 8-10 green
            if area_points == 0:
                color = 'gray'
                level = 'no_approved_areas'
            elif area_points <= 3:
                color = 'red'
                level = 'low'
            elif area_points <= 7:
                color = 'yellow'
                level = 'medium'
            else:
                color = 'green'
                level = 'high'
            
            countries_list.append({
                'country': country,
                'area_points': area_points,  # Number of areas with approved policies
                'total_approved_policies': data['total_approved_policies'],
                'areas_with_approved_policies': list(data['areas'].keys()),
                'areas_detail': list(data['areas'].values()),
                'color': color,
                'level': level,
                'status': 'approved' if area_points > 0 else 'no_approved_policies'
            })
        
        return {
            "success": True,
            "countries": countries_list,
            "total_countries": len(countries_list),
            "total_approved_policies": sum(c['total_approved_policies'] for c in countries_list),
            "area_point_system": {
                "explanation": "Each area gets 1 point if it has at least one approved policy",
                "color_coding": "Based on total area points per country"
            },
            "color_legend": {
                "gray": "No approved areas (0 points)",
                "red": "Low: 1-3 approved areas", 
                "yellow": "Medium: 4-7 approved areas",
                "green": "High: 8-10 approved areas"
            },
            "data_source": "Only approved policies from map_policies table"
        }
        
    except Exception as e:
        logger.error(f"❌ Map visualization failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "countries": [],
            "total_countries": 0,
            "total_approved_policies": 0
        }

@router.post("/demo-mixed-status/{submission_id}")
async def demo_mixed_status(submission_id: str):
    """Demo endpoint: Set one policy to approved and one to pending to demonstrate area status logic"""
    try:
        logger.info(f"🔍 DEMO: Setting mixed status for {submission_id}")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Get the policy
        policy = await db.get_item('policies', {'policy_id': submission_id})
        if not policy:
            return {"success": False, "error": "Policy not found", "submission_id": submission_id}
        
        # Update individual policy statuses - mixed status
        for area_idx, area in enumerate(policy.get("policy_areas", [])):
            for policy_idx, individual_policy in enumerate(area.get("policies", [])):
                if policy_idx == 0:
                    individual_policy["status"] = "approved"  # First policy approved
                else:
                    individual_policy["status"] = "pending"   # Others pending
        
        # Update the submission to pending (since not all are approved)
        table = db.tables['policies']
        table.update_item(
            Key={'policy_id': submission_id},
            UpdateExpression="SET #status = :status, policy_areas = :policy_areas, updated_at = :updated_at",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'pending',  # Overall status pending
                ':policy_areas': policy.get("policy_areas", []),
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": "Mixed status demo set - first policy approved, others pending",
            "submission_id": submission_id,
            "expected_area_status": "approved (because at least one policy is approved)",
            "expected_individual_statuses": "mixed (first=approved, others=pending)",
            "debug": "Demo mixed status for testing area approval logic"
        }
        
    except Exception as e:
        logger.error(f"❌ DEMO: Mixed status failed: {str(e)}")
        return {"success": False, "error": str(e), "submission_id": submission_id}

@router.get("/submissions-debug")
async def get_admin_submissions_debug(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query("all")
):
    """Debug endpoint: Get all submissions without authentication (TEMPORARY)"""
    try:
        logger.info("DEBUG: Getting submissions without authentication")
        result = await admin_service.get_submissions(page=page, limit=limit, status=status)
        
        # Enhance submissions with user data
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        for submission in result.get("data", []):
            user_id = submission.get("user_id")
            if user_id:
                try:
                    # Get user information
                    user = await db.get_item('users', {'user_id': user_id})
                    if user:
                        submission["user_name"] = user.get("name", "Unknown User")
                        submission["user_full_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                        if not submission["user_full_name"]:
                            submission["user_full_name"] = user.get("name", "Unknown User")
                    else:
                        submission["user_name"] = "User Not Found"
                        submission["user_full_name"] = "User Not Found"
                except Exception as e:
                    logger.warning(f"Could not fetch user data for {user_id}: {e}")
                    submission["user_name"] = "Unknown User"
                    submission["user_full_name"] = "Unknown User"
        
        # Add extra debug info
        result["debug_info"] = {
            "endpoint": "submissions-debug",
            "authentication": "bypassed for debugging",
            "timestamp": datetime.now().isoformat(),
            "enhanced_with_user_data": True
        }
        
        return result
    except Exception as e:
        logger.error(f"Error getting admin submissions (debug): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")

@router.post("/debug-approval/{submission_id}")
async def debug_approval(
    submission_id: str
):
    """Debug approval with detailed logging"""
    try:
        logger.info(f"🔍 DEBUG: Starting approval for {submission_id}")
        
        from config.dynamodb import get_dynamodb
        
        db = await get_dynamodb()
        
        # Step 1: Get the policy
        policy = await db.get_item('policies', {'policy_id': submission_id})
        if not policy:
            return {"success": False, "error": "Policy not found", "submission_id": submission_id}
        
        logger.info(f"✅ Found policy: {policy.get('user_email')} - {policy.get('country')}")
        
        # Step 2: Update policy status directly AND individual policy statuses
        table = db.tables['policies']
        
        # First, update the individual policy statuses to approved
        for area_idx, area in enumerate(policy.get("policy_areas", [])):
            for policy_idx, individual_policy in enumerate(area.get("policies", [])):
                individual_policy["status"] = "approved"
        
        update_response = table.update_item(
            Key={'policy_id': submission_id},
            UpdateExpression="SET #status = :status, visible_on_map = :visible, approved_at = :approved_at, updated_at = :updated_at, policy_areas = :policy_areas",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'approved',
                ':visible': True,
                ':approved_at': datetime.utcnow().isoformat(),
                ':updated_at': datetime.utcnow().isoformat(),
                ':policy_areas': policy.get("policy_areas", [])
            },
            ReturnValues="UPDATED_NEW"
        )
        
        logger.info(f"✅ Policy and individual policy statuses updated: {update_response}")
        
        # Step 3: Create map policy entries
        map_entries = []
        if policy.get("policy_areas"):
            for area in policy["policy_areas"]:
                for individual_policy in area.get("policies", []):
                    map_policy_entry = {
                        "map_policy_id": str(uuid.uuid4()),
                        "parent_submission_id": policy["policy_id"],
                        "policy_name": individual_policy.get("policyName", ""),
                        "policy_description": individual_policy.get("policyDescription", ""),
                        "country": policy["country"],
                        "policy_area": area["area_name"],
                        "target_groups": individual_policy.get("targetGroups", []),
                        "policy_link": individual_policy.get("policyLink", ""),
                        "implementation": individual_policy.get("implementation", {}),
                        "evaluation": individual_policy.get("evaluation", {}),
                        "participation": individual_policy.get("participation", {}),
                        "alignment": individual_policy.get("alignment", {}),
                        "status": "approved",
                        "visible_on_map": True,
                        "approved_by": "debug@admin.com",
                        "approved_at": datetime.utcnow().isoformat(),
                        "created_at": datetime.utcnow().isoformat(),
                        "user_id": policy["user_id"],
                        "user_email": policy["user_email"]
                    }
                    
                    # Insert into map_policies table
                    await db.insert_item('map_policies', map_policy_entry)
                    map_entries.append(map_policy_entry["map_policy_id"])
                    logger.info(f"✅ Created map policy: {map_policy_entry['map_policy_id']}")
        
        return {
            "success": True,
            "message": "Policy approved successfully with map creation",
            "submission_id": submission_id,
            "status": "approved",
            "map_entries_created": len(map_entries),
            "map_policy_ids": map_entries,
            "debug": "Direct database update with map creation"
        }
        
    except Exception as e:
        logger.error(f"❌ DEBUG: Approval failed: {str(e)}")
        import traceback
        logger.error(f"❌ DEBUG: Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "submission_id": submission_id,
            "debug": "Error in debug approval",
            "traceback": traceback.format_exc()
        }

@router.post("/debug-rejection/{submission_id}")
async def debug_rejection(
    submission_id: str
):
    """Debug rejection with detailed logging"""
    try:
        logger.info(f"🔍 DEBUG: Starting rejection for {submission_id}")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Step 1: Check if policy exists
        logger.info("Step 1: Getting policy...")
        policy = await db.get_item('policies', {'policy_id': submission_id})
        if not policy:
            return {"error": "Policy not found", "submission_id": submission_id}
        
        logger.info(f"Step 1 ✅: Found policy for user {policy.get('user_email')}")
        
        # Step 2: Simple update to rejected status
        logger.info("Step 2: Updating policy status to rejected...")
        
        try:
            # Get the table directly
            table = db.tables['policies']
            
            # Simple update to rejected status
            response = table.update_item(
                Key={'policy_id': submission_id},
                UpdateExpression="SET #status = :status, reviewed_at = :reviewed_at",
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'rejected',
                    ':reviewed_at': datetime.utcnow().isoformat()
                },
                ReturnValues="UPDATED_NEW"
            )
            
            logger.info("Step 2 ✅: Policy status updated to rejected")
            
            return {
                "success": True,
                "message": "Policy rejected successfully",
                "submission_id": submission_id,
                "update_response": response,
                "debug": "Direct DynamoDB update successful"
            }
            
        except Exception as update_error:
            logger.error(f"Update failed: {str(update_error)}")
            return {"error": f"Update failed: {str(update_error)}"}
        
    except Exception as e:
        logger.error(f"DEBUG rejection failed: {str(e)}")
        return {
            "error": str(e),
            "message": "Debug rejection failed"
        }

@router.post("/approve-submission-simple/{submission_id}")
async def approve_submission_simple(
    submission_id: str,
    admin_notes: str = ""
):
    """Simple approval endpoint without map entries (TEMPORARY)"""
    try:
        logger.info(f"DEBUG: Simple approval for submission {submission_id}")
        
        # Direct database update
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Get the policy first
        policy = await db.get_item('policies', {'policy_id': submission_id})
        if not policy:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Simple update without map creation
        update_data = {
            "status": "approved",
            "admin_notes": admin_notes or "Approved via simple debug endpoint",
            "reviewed_by": "debug_admin@system.local",
            "reviewed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "visible_on_map": True,
            "approved_at": datetime.utcnow().isoformat()
        }
        
        success = await db.update_item('policies', {'policy_id': submission_id}, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update policy status")
        
        return {
            "success": True,
            "message": f"Submission {submission_id} approved successfully (simple mode)",
            "policy_id": submission_id,
            "new_status": "approved",
            "visible_on_map": True
        }
        
    except Exception as e:
        logger.error(f"Error in simple approval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve submission: {str(e)}")

@router.post("/approve-submission/{submission_id}")
async def approve_submission_debug(
    submission_id: str,
    admin_notes: str = ""
):
    """Debug endpoint: Approve a submission without authentication (TEMPORARY)"""
    try:
        logger.info(f"DEBUG: Approving submission {submission_id} without authentication")
        
        # Use policy service to update status
        from services.policy_service_dynamodb import policy_service
        
        # Create fake admin user for approval
        fake_admin = {
            "email": "debug_admin@system.local",
            "user_id": "debug_admin",
            "role": "admin"
        }
        
        status_update = {
            "submission_id": submission_id,
            "status": "approved",
            "admin_notes": admin_notes or "Approved via debug endpoint"
        }
        
        result = await policy_service.update_policy_status(status_update, fake_admin)
        
        return {
            "success": True,
            "message": f"Submission {submission_id} approved successfully",
            "result": result,
            "debug_info": {
                "endpoint": "approve-submission-debug",
                "authentication": "bypassed for debugging"
            }
        }
        
    except Exception as e:
        logger.error(f"Error approving submission (debug): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve submission: {str(e)}")


@router.get("/statistics")
async def get_admin_statistics(admin_user: dict = Depends(get_admin_user)):
    """Get admin statistics with timeout handling"""
    try:
        import asyncio
        
        async def fetch_stats():
            return await admin_service.get_statistics()
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(fetch_stats(), timeout=10.0)
            return result
        except asyncio.TimeoutError:
            logger.warning("Statistics query timeout")
            # Return default statistics instead of error
            return {
                "success": True,
                "statistics": {
                    "users": {"total": 0, "verified": 0, "admin": 0},
                    "submissions": {"total": 0, "pending": 0},
                    "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
                },
                "note": "Statistics temporarily unavailable - database timeout"
            }
    except Exception as e:
        logger.error(f"Error getting admin statistics: {str(e)}")
        # Return default statistics instead of 500 error
        return {
            "success": False,
            "statistics": {
                "users": {"total": 0, "verified": 0, "admin": 0},
                "submissions": {"total": 0, "pending": 0},
                "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
            },
            "error": "Database connection issue - please try again"
        }


@router.get("/statistics-fast")
async def get_admin_statistics_fast(admin_user: dict = Depends(get_admin_user)):
    """Ultra-fast admin statistics with caching"""
    try:
        import asyncio
        
        # Use in-memory cache for 60 seconds
        cache_key = "fast_stats_cache"
        cached_stats = getattr(get_admin_statistics_fast, cache_key, None)
        cache_time = getattr(get_admin_statistics_fast, f"{cache_key}_time", 0)
        
        if cached_stats and (time.time() - cache_time) < 60:
            return {
                "success": True,
                "statistics": cached_stats,
                "cached": True
            }
        
        async def fetch_basic_stats():
            from services.admin_service import admin_service
            return await admin_service.get_statistics()
        
        # Execute with very short timeout
        try:
            result = await asyncio.wait_for(fetch_basic_stats(), timeout=2.0)
            
            # Cache the result
            setattr(get_admin_statistics_fast, cache_key, result.get("statistics", {}))
            setattr(get_admin_statistics_fast, f"{cache_key}_time", time.time())
            
            return result
        except asyncio.TimeoutError:
            logger.warning("Fast statistics timeout")
            
            # Return cached data if available
            if cached_stats:
                return {
                    "success": True,
                    "statistics": cached_stats,
                    "note": "Using cached data due to timeout"
                }
            
            # Return default stats
            return {
                "success": True,
                "statistics": {
                    "users": {"total": 0, "verified": 0, "admin": 0},
                    "submissions": {"total": 0, "pending": 0},
                    "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
                },
                "note": "Fast query timeout"
            }
            
    except Exception as e:
        logger.error(f"Error in fast statistics: {str(e)}")
        return {
            "success": False,
            "statistics": {
                "users": {"total": 0, "verified": 0, "admin": 0},
                "submissions": {"total": 0, "pending": 0},
                "policies": {"master": 0, "approved": 0, "rejected": 0, "under_review": 0}
            },
            "error": "Fast query failed"
        }


@router.post("/move-to-master")
async def move_submission_to_master(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Move approved policies to master collection"""
    try:
        submission_id = request_data.get("submission_id")
        if not submission_id:
            raise HTTPException(status_code=400, detail="submission_id is required")
        
        return await admin_service.move_to_master(submission_id, admin_user)
    except Exception as e:
        logger.error(f"Error moving to master: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to move to master: {str(e)}")


@router.post("/fix-visibility")
async def fix_policy_visibility(
    admin_user: dict = Depends(get_admin_user)
):
    """Fix policy visibility issues"""
    try:
        return await admin_service.fix_visibility()
    except Exception as e:
        logger.error(f"Error fixing visibility: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fix visibility: {str(e)}")


@router.post("/migrate-old-data")
async def migrate_old_data(
    admin_user: dict = Depends(get_admin_user)
):
    """Migrate old data format to new format"""
    try:
        return await admin_service.migrate_old_data()
    except Exception as e:
        logger.error(f"Error migrating data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to migrate data: {str(e)}")


@router.post("/repair-historical-data")
async def repair_historical_data(
    admin_user: dict = Depends(get_admin_user)
):
    """Repair historical data issues"""
    try:
        return await admin_service.repair_historical_data()
    except Exception as e:
        logger.error(f"Error repairing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to repair data: {str(e)}")


@router.put("/update-policy-status")
async def update_policy_status(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Update the status of a specific policy (approve/reject)"""
    try:
        submission_id = request_data.get("submission_id")
        area_id = request_data.get("area_id")
        policy_index = request_data.get("policy_index")
        status = request_data.get("status")
        admin_notes = request_data.get("admin_notes", "")
        
        if not all([submission_id, area_id is not None, policy_index is not None, status]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        return await admin_service.update_policy_status(
            submission_id, area_id, policy_index, status, admin_notes, admin_user
        )
    except Exception as e:
        logger.error(f"Error updating policy status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update policy status: {str(e)}")


@router.delete("/master-policy/{policy_id}")
async def delete_master_policy(
    policy_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a policy from master collection (removes from DB and map)"""
    try:
        return await admin_service.delete_master_policy(policy_id, admin_user)
    except Exception as e:
        logger.error(f"Error deleting master policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete master policy: {str(e)}")


@router.delete("/submission-policy")
async def delete_submission_policy(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a specific policy from a submission"""
    try:
        submission_id = request_data.get("submission_id")
        area_id = request_data.get("area_id")
        policy_index = request_data.get("policy_index")
        
        if not all([submission_id, area_id is not None, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        return await admin_service.delete_submission_policy(
            submission_id, area_id, policy_index, admin_user
        )
    except Exception as e:
        logger.error(f"Error deleting submission policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete submission policy: {str(e)}")


@router.get("/master-policies")
async def get_master_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get master policies for admin management"""
    try:
        skip = (page - 1) * limit
        
        # Get active master policies
        cursor = admin_service.master_policies_collection.find(
            {"master_status": "active"}
        ).sort("moved_to_master_at", -1).skip(skip).limit(limit)
        
        policies = []
        async for policy in cursor:
            policies.append(convert_objectid(policy))
        
        # Get total count
        total_count = await admin_service.master_policies_collection.count_documents(
            {"master_status": "active"}
        )
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "success": True,
            "policies": policies,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page
        }
    except Exception as e:
        logger.error(f"Error getting master policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get master policies: {str(e)}")


@router.post("/approve-policy")
async def approve_policy(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Approve a policy and make it visible on the map"""
    try:
        submission_id = request_data.get("submission_id")
        area_id = request_data.get("area_id") 
        policy_index = request_data.get("policy_index")
        admin_notes = request_data.get("admin_notes", "")
        
        if not all([submission_id, area_id is not None, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        return await admin_service.approve_policy(
            submission_id, area_id, policy_index, admin_notes, admin_user
        )
    except Exception as e:
        logger.error(f"Error approving policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve policy: {str(e)}")


@router.post("/reject-policy")
async def reject_policy(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Reject a policy and remove it from map visibility"""
    try:
        submission_id = request_data.get("submission_id")
        area_id = request_data.get("area_id")
        policy_index = request_data.get("policy_index") 
        admin_notes = request_data.get("admin_notes", "Policy rejected by admin")
        
        if not all([submission_id, area_id is not None, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        return await admin_service.reject_policy(
            submission_id, area_id, policy_index, admin_notes, admin_user
        )
    except Exception as e:
        logger.error(f"Error rejecting policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reject policy: {str(e)}")


@router.post("/commit-policy")
async def commit_policy(
    request_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Commit an approved policy to the master database"""
    try:
        submission_id = request_data.get("submission_id")
        area_id = request_data.get("area_id")
        policy_index = request_data.get("policy_index")
        
        if not all([submission_id, area_id is not None, policy_index is not None]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        return await admin_service.commit_policy_to_master(
            submission_id, area_id, policy_index, admin_user
        )
    except Exception as e:
        logger.error(f"Error committing policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to commit policy: {str(e)}")


@router.delete("/policy/{policy_id}")
async def delete_policy_completely(
    policy_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Completely delete a policy from database and map"""
    try:
        return await admin_service.delete_policy_completely(policy_id, admin_user)
    except Exception as e:
        logger.error(f"Error deleting policy completely: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")


@router.get("/approved-policies")
async def get_approved_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_user: dict = Depends(get_admin_user)
):
    """Get all approved policies for map visualization"""
    try:
        return await admin_service.get_approved_policies(page=page, limit=limit)
    except Exception as e:
        logger.error(f"Error getting approved policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get approved policies: {str(e)}")


@router.get("/policy-files/{policy_id}")
async def get_policy_files(
    policy_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get all files associated with a policy"""
    try:
        return await admin_service.get_policy_files(policy_id)
    except Exception as e:
        logger.error(f"Error getting policy files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy files: {str(e)}")


@router.post("/policy/{policy_id}/upload-file")
async def upload_policy_file(
    policy_id: str,
    file_data: Dict[str, Any],
    admin_user: dict = Depends(get_admin_user)
):
    """Upload a file for a specific policy"""
    try:
        return await admin_service.upload_policy_file(policy_id, file_data, admin_user)
    except Exception as e:
        logger.error(f"Error uploading policy file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload policy file: {str(e)}")

@router.get("/policy/{policy_id}/files")
async def get_policy_files(
    policy_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get all files associated with a policy"""
    try:
        logger.info(f"Getting files for policy {policy_id}")
        
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Get the policy first
        policy = await db.get_item('policies', {'policy_id': policy_id})
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Collect all files from all policy areas and individual policies
        all_files = []
        
        for area in policy.get("policy_areas", []):
            for individual_policy in area.get("policies", []):
                # Check for uploaded files
                if individual_policy.get("policyFile"):
                    file_info = individual_policy["policyFile"]
                    if isinstance(file_info, dict):
                        all_files.append({
                            "file_id": file_info.get("file_id", str(uuid.uuid4())),
                            "name": file_info.get("name", "Unknown File"),
                            "type": file_info.get("type", "application/octet-stream"),
                            "size": file_info.get("size", 0),
                            "upload_date": file_info.get("upload_date", datetime.utcnow().isoformat()),
                            "policy_area": area.get("area_name", "Unknown Area"),
                            "policy_name": individual_policy.get("policyName", "Unnamed Policy"),
                            "data": file_info.get("data"),  # Base64 encoded file data
                            "file_path": file_info.get("file_path")  # Server file path if applicable
                        })
        
        # Also check for files stored in separate file metadata table
        try:
            file_metadata_items = await db.scan_table('file_metadata')
            policy_files = [f for f in file_metadata_items if f.get('policy_id') == policy_id]
            
            for file_meta in policy_files:
                all_files.append({
                    "file_id": file_meta.get("file_id"),
                    "name": file_meta.get("filename"),
                    "type": file_meta.get("content_type"),
                    "size": file_meta.get("file_size"),
                    "upload_date": file_meta.get("created_at"),
                    "policy_area": file_meta.get("policy_area", "General"),
                    "policy_name": file_meta.get("policy_name", ""),
                    "file_path": file_meta.get("file_path")
                })
        except Exception as e:
            logger.warning(f"Could not fetch file metadata: {e}")
        
        return {
            "success": True,
            "files": all_files,
            "total_files": len(all_files),
            "policy_id": policy_id
        }
        
    except Exception as e:
        logger.error(f"Error getting policy files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy files: {str(e)}")

@router.get("/file/{file_id}")
async def get_file(
    file_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Download a specific file"""
    try:
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Try to find file in file_metadata table first
        try:
            file_metadata = await db.get_item('file_metadata', {'file_id': file_id})
            if file_metadata:
                # Return file data or redirect to file path
                if file_metadata.get('file_data'):
                    return {
                        "success": True,
                        "file_data": file_metadata['file_data'],
                        "filename": file_metadata.get('filename'),
                        "content_type": file_metadata.get('content_type')
                    }
                elif file_metadata.get('file_path'):
                    # Return file path for server-side file access
                    return {
                        "success": True,
                        "file_path": file_metadata['file_path'],
                        "filename": file_metadata.get('filename'),
                        "content_type": file_metadata.get('content_type')
                    }
        except Exception as e:
            logger.warning(f"File not found in metadata table: {e}")
        
        # Fallback: search in policies for embedded files
        all_policies = await db.scan_table('policies')
        for policy in all_policies:
            for area in policy.get("policy_areas", []):
                for individual_policy in area.get("policies", []):
                    if individual_policy.get("policyFile") and individual_policy["policyFile"].get("file_id") == file_id:
                        file_info = individual_policy["policyFile"]
                        return {
                            "success": True,
                            "file_data": file_info.get("data"),
                            "filename": file_info.get("name"),
                            "content_type": file_info.get("type")
                        }
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except Exception as e:
        logger.error(f"Error getting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")

@router.delete("/file/{file_id}")
async def delete_file(
    file_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a specific file"""
    try:
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        # Try to delete from file_metadata table
        try:
            success = await db.delete_item('file_metadata', {'file_id': file_id})
            if success:
                return {"success": True, "message": "File deleted successfully"}
        except Exception as e:
            logger.warning(f"File not found in metadata table: {e}")
        
        # Also remove from embedded policy files
        all_policies = await db.scan_table('policies')
        for policy in all_policies:
            policy_updated = False
            for area in policy.get("policy_areas", []):
                for individual_policy in area.get("policies", []):
                    if individual_policy.get("policyFile") and individual_policy["policyFile"].get("file_id") == file_id:
                        individual_policy["policyFile"] = None
                        policy_updated = True
            
            if policy_updated:
                await db.update_item('policies', {'policy_id': policy['policy_id']}, {'policy_areas': policy['policy_areas']})
                return {"success": True, "message": "File deleted from policy"}
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/all-files")
async def get_all_files(
    admin_user: dict = Depends(get_admin_user)
):
    """Get all files in the system"""
    try:
        from config.dynamodb import get_dynamodb
        db = await get_dynamodb()
        
        all_files = []
        
        # Get files from file_metadata table
        try:
            file_metadata_items = await db.scan_table('file_metadata')
            for file_meta in file_metadata_items:
                all_files.append({
                    "file_id": file_meta.get("file_id"),
                    "name": file_meta.get("filename"),
                    "type": file_meta.get("content_type"),
                    "size": file_meta.get("file_size"),
                    "upload_date": file_meta.get("created_at"),
                    "policy_id": file_meta.get("policy_id"),
                    "source": "metadata_table"
                })
        except Exception as e:
            logger.warning(f"Could not fetch file metadata: {e}")
        
        # Get files embedded in policies
        all_policies = await db.scan_table('policies')
        for policy in all_policies:
            for area in policy.get("policy_areas", []):
                for individual_policy in area.get("policies", []):
                    if individual_policy.get("policyFile"):
                        file_info = individual_policy["policyFile"]
                        if isinstance(file_info, dict):
                            all_files.append({
                                "file_id": file_info.get("file_id", str(uuid.uuid4())),
                                "name": file_info.get("name", "Unknown File"),
                                "type": file_info.get("type", "application/octet-stream"),
                                "size": file_info.get("size", 0),
                                "upload_date": file_info.get("upload_date", datetime.utcnow().isoformat()),
                                "policy_id": policy.get("policy_id"),
                                "policy_area": area.get("area_name"),
                                "policy_name": individual_policy.get("policyName"),
                                "source": "embedded_in_policy"
                            })
        
        return {
            "success": True,
            "files": all_files,
            "total_files": len(all_files),
            "summary": {
                "metadata_table": len([f for f in all_files if f["source"] == "metadata_table"]),
                "embedded_in_policies": len([f for f in all_files if f["source"] == "embedded_in_policy"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get all files: {str(e)}")
