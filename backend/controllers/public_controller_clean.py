"""
Clean Public Controller with DynamoDB integration
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, FileResponse
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
                'parent_submission_id': policy.get('parent_submission_id', ''),
                # Add policy_id for file access - use parent_submission_id as policy_id
                'policy_id': policy.get('parent_submission_id', '') or policy.get('map_policy_id', ''),
                'policyId': policy.get('parent_submission_id', '') or policy.get('map_policy_id', '')
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

@router.get("/files/{file_identifier:path}")
async def serve_public_file(file_identifier: str):
    """Serve files for approved policies - supports both S3 keys and local paths"""
    try:
        import os
        import urllib.parse
        
        # URL decode the file identifier
        decoded_identifier = urllib.parse.unquote(file_identifier)
        logger.info(f"🔍 File request - Original: {file_identifier[:100]}")
        logger.info(f"🔍 File request - Decoded: {decoded_identifier[:100]}")
        
        # Security: Basic path validation
        if ".." in decoded_identifier:
            raise HTTPException(status_code=400, detail="Invalid file identifier")
        
        dynamodb = await get_dynamodb()
        
        # Check if file exists in metadata by various identifiers
        file_metadata_items = await dynamodb.scan_table('file_metadata')
        logger.info(f"📊 Scanning {len(file_metadata_items)} files in metadata")
        
        # Find the file in metadata or policy structure
        file_metadata = None
        
        # Method 1: Search in file_metadata table with better matching
        for f in file_metadata_items:
            file_id = f.get('file_id', '')
            s3_key = f.get('s3_key', '')
            filename = f.get('filename', '')
            
            # Enhanced matching logic - check exact matches and partial matches
            if (file_id == decoded_identifier or 
                s3_key == decoded_identifier or 
                filename == decoded_identifier or
                decoded_identifier == file_id or
                decoded_identifier == s3_key or
                (s3_key and decoded_identifier in s3_key and len(decoded_identifier) > 10) or
                (s3_key and s3_key.endswith(decoded_identifier.split('/')[-1]) and len(decoded_identifier) > 20)):
                
                # Only use files that are completed
                if f.get('upload_status') == 'completed' and s3_key:
                    file_metadata = f
                    logger.info(f"✅ Found file in metadata: {filename} (s3_key: {s3_key})")
                    break
        
        # Method 2: Search in approved policies for direct S3 keys  
        if not file_metadata:
            logger.info(f"🔍 File not found in metadata, searching in approved policies...")
            policies = await dynamodb.scan_table('policies')
            logger.info(f"📊 Checking {len(policies)} policies")
            
            for policy in policies:
                if policy.get('status') != 'approved':
                    continue
                    
                for area in policy.get("policy_areas", []):
                    for individual_policy in area.get("policies", []):
                        policy_file = individual_policy.get("policyFile")
                        if policy_file and isinstance(policy_file, dict):
                            s3_key = policy_file.get("s3_key") or policy_file.get("file_id")
                            filename = policy_file.get("name", "")
                            
                            # Enhanced matching logic
                            if s3_key and (
                                s3_key == decoded_identifier or 
                                decoded_identifier == s3_key or
                                (decoded_identifier in s3_key and len(decoded_identifier) > 10) or
                                (filename and decoded_identifier.endswith(filename)) or
                                (s3_key.endswith(decoded_identifier.split('/')[-1]) and len(decoded_identifier) > 20)
                            ):
                                # Create metadata-like structure from policy file
                                file_metadata = {
                                    'filename': filename,
                                    'upload_status': 'completed',
                                    's3_key': s3_key,
                                    's3_url': policy_file.get("file_url") or policy_file.get("cdn_url"),
                                    'mime_type': policy_file.get("type"),
                                    'file_size': policy_file.get("size"),
                                    'is_deleted': False
                                }
                                logger.info(f"✅ Found file in approved policy: {filename} (s3_key: {s3_key})")
                                break
                    if file_metadata:
                        break
                if file_metadata:
                    break
        
        if not file_metadata:
            logger.warning(f"⚠️ File not found: {decoded_identifier}")
            logger.info(f"🔍 Tried to match against file_id, s3_key, filename patterns")
            
            # Log some sample S3 keys for debugging
            sample_s3_keys = []
            for f in file_metadata_items[:5]:
                sample_s3_keys.append(f.get('s3_key', 'NO_S3_KEY'))
            logger.info(f"🔍 Sample S3 keys in metadata: {sample_s3_keys}")
            
            raise HTTPException(status_code=404, detail="File not found in metadata")
        
        logger.info(f"📁 Found file: {file_metadata.get('filename')} (Status: {file_metadata.get('upload_status')})")
        
        # For testing: Allow access to completed files regardless of policy association
        # In production, you might want to enforce policy approval checks
        if file_metadata.get('upload_status') != 'completed':
            raise HTTPException(status_code=403, detail="File not ready for access")
        
        # Check if file is marked as deleted
        if file_metadata.get('is_deleted', False):
            raise HTTPException(status_code=404, detail="File has been deleted")
        
        # Try to serve from S3 with presigned URL
        s3_key = file_metadata.get('s3_key')
        if s3_key:
            try:
                from services.aws_service import aws_service
                if aws_service:
                    logger.info(f"🔑 Generating presigned URL for S3 key: {s3_key}")
                    presigned_url = await aws_service.get_presigned_url(s3_key, expiration=3600)  # 1 hour expiration
                    logger.info(f"🔗 Generated presigned URL, redirecting")
                    return RedirectResponse(url=presigned_url, status_code=302)
                else:
                    logger.warning(f"⚠️ AWS service not available")
            except Exception as e:
                logger.warning(f"⚠️ Failed to generate presigned URL: {e}")
                # Fall through to local file serving

        # Fallback: Try S3 direct URL (legacy)
        s3_url = file_metadata.get('s3_url')
        if s3_url:
            logger.info(f"📤 Redirecting to S3: {file_metadata.get('filename')}")
            return RedirectResponse(url=s3_url, status_code=302)
        
        # Fallback to local file serving (for any local files)
        filename = file_metadata.get('filename') or file_metadata.get('original_filename')
        if filename:
            # Try different possible local paths
            possible_paths = [
                os.path.join("uploads", filename),
                os.path.join("uploads", file_identifier),
                filename if os.path.exists(filename) else None
            ]
            
            for full_path in possible_paths:
                if full_path and os.path.exists(full_path):
                    logger.info(f"📂 Serving local file: {filename}")
                    return FileResponse(
                        path=full_path,
                        media_type=file_metadata.get('mime_type', 'application/octet-stream'),
                        filename=filename
                    )
        
        # No valid file source found
        raise HTTPException(status_code=404, detail="File content not accessible")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {file_identifier}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve file")

@router.get("/policy/{policy_id}/files")
async def get_public_policy_files(policy_id: str):
    """Get all files for an approved policy (public access)"""
    try:
        logger.info(f"🔍 PUBLIC: Fetching files for policy_id: {policy_id}")
        dynamodb = await get_dynamodb()
        
        # First check if the policy exists and is approved
        policy = await dynamodb.get_item('policies', {'policy_id': policy_id})
        logger.info(f"📝 Policy found in main table: {policy is not None}")
        
        if not policy:
            # Try to find by parent_submission_id in map_policies
            logger.info(f"🔄 Policy not found in main table, checking map_policies...")
            map_policies = await dynamodb.scan_table('map_policies')
            
            map_policy = None
            for mp in map_policies:
                if mp.get('parent_submission_id') == policy_id or mp.get('map_policy_id') == policy_id:
                    map_policy = mp
                    logger.info(f"✅ Found matching map policy: {mp.get('map_policy_id')}")
                    break
            
            if map_policy and map_policy.get('status') == 'approved':
                logger.info(f"✅ Found approved map policy, using parent_submission_id: {map_policy.get('parent_submission_id')}")
                original_policy_id = map_policy.get('parent_submission_id')
                if original_policy_id:
                    policy = await dynamodb.get_item('policies', {'policy_id': original_policy_id})
                    if not policy:
                        logger.warning(f"⚠️ Parent policy {original_policy_id} not found")
                        # Still return success but with no files
                        return {
                            "success": True,
                            "files": [],
                            "total_files": 0,
                            "policy_id": policy_id,
                            "message": "Original policy not found"
                        }
                else:
                    logger.warning(f"⚠️ Map policy has no parent_submission_id")
                    return {
                        "success": True,
                        "files": [],
                        "total_files": 0,
                        "policy_id": policy_id,
                        "message": "Map policy has no parent reference"
                    }
            else:
                logger.warning(f"⚠️ Policy {policy_id} not found or not approved")
                return {
                    "success": True,
                    "files": [],
                    "total_files": 0,
                    "policy_id": policy_id,
                    "message": "Policy not found or not approved yet"
                }
        
        # Check if policy is approved
        policy_status = policy.get('status')
        if policy_status != 'approved':
            logger.warning(f"⚠️ Policy {policy_id} not approved: status = {policy_status}")
            return {
                "success": True,
                "files": [],
                "total_files": 0,
                "policy_id": policy_id,
                "message": "Policy not approved for public access yet"
            }
        
        logger.info(f"✅ Policy {policy_id} is approved, fetching files...")
        
        # Collect files from approved policy
        all_files = []
        
        # Get files embedded in policy structure
        for area in policy.get("policy_areas", []):
            for individual_policy in area.get("policies", []):
                # Check for uploaded files
                policy_file = individual_policy.get("policyFile")
                if policy_file and isinstance(policy_file, dict):
                    s3_key = policy_file.get("s3_key") or policy_file.get("file_id")
                    if s3_key:
                        file_info = {
                            "file_id": s3_key,
                            "name": policy_file.get("name", "Unknown File"),
                            "type": policy_file.get("type", "application/octet-stream"),
                            "size": int(policy_file.get("size", 0)),
                            "upload_date": policy_file.get("upload_date", ""),
                            "policy_area": area.get("area_name", "Unknown Area"),
                            "policy_name": individual_policy.get("policyName", "Unnamed Policy"),
                            "file_path": s3_key,
                            "s3_key": s3_key,
                            "s3_url": policy_file.get("file_url") or policy_file.get("cdn_url"),
                            "source": "policy_embedded"
                        }
                        all_files.append(file_info)
                        logger.info(f"📎 Found file: {file_info['name']} (s3_key: {s3_key})")
        
        logger.info(f"📎 Total files found: {len(all_files)}")
        
        return {
            "success": True,
            "files": all_files,
            "total_files": len(all_files),
            "policy_id": policy_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting public policy files: {e}")
        raise HTTPException(status_code=500, detail="Failed to get policy files")

@router.get("/debug/test-policy-files/{policy_id}")
async def debug_test_policy_files(policy_id: str):
    """Debug endpoint to test policy file access without auth"""
    try:
        logger.info(f"🧪 DEBUG: Testing policy files for {policy_id}")
        
        # Just return a simple response to verify the endpoint works
        return {
            "success": True,
            "message": f"Public endpoint is working for policy {policy_id}",
            "endpoint": f"/api/public/policy/{policy_id}/files",
            "debug": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/debug/policies")
async def debug_policies():
    """Debug endpoint to see what policies exist"""
    try:
        dynamodb = await get_dynamodb()
        
        # Check main policies table
        all_policies = await dynamodb.scan_table('policies')
        main_policy_ids = [p.get('policy_id', 'NO_ID') for p in all_policies]
        
        # Check map policies table
        map_policies = await dynamodb.scan_table('map_policies')
        map_policy_data = [(mp.get('map_policy_id', 'NO_MAP_ID'), mp.get('parent_submission_id', 'NO_PARENT_ID'), mp.get('status', 'NO_STATUS')) for mp in map_policies]
        
        # Check file metadata
        file_metadata = await dynamodb.scan_table('file_metadata')
        file_policy_ids = [f.get('policy_id', 'NO_ID') for f in file_metadata]
        
        return {
            "success": True,
            "main_policies_count": len(all_policies),
            "main_policy_ids": main_policy_ids[:10],  # First 10 only
            "map_policies_count": len(map_policies),
            "map_policy_data": map_policy_data[:10],  # First 10 only
            "file_metadata_count": len(file_metadata),
            "file_policy_ids": list(set(file_policy_ids))[:10]  # First 10 unique only
        }
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/debug/search-file/{search_term}")
async def debug_search_file(search_term: str):
    """Debug endpoint to search for files containing a specific term"""
    try:
        dynamodb = await get_dynamodb()
        
        # Search in file metadata
        file_metadata_items = await dynamodb.scan_table('file_metadata')
        matching_metadata = []
        for f in file_metadata_items:
            file_id = f.get('file_id', '')
            s3_key = f.get('s3_key', '')
            filename = f.get('filename', '')
            
            if (search_term.lower() in file_id.lower() or 
                search_term.lower() in s3_key.lower() or 
                search_term.lower() in filename.lower()):
                matching_metadata.append({
                    'file_id': file_id,
                    's3_key': s3_key,
                    'filename': filename,
                    'policy_id': f.get('policy_id'),
                    'upload_status': f.get('upload_status')
                })
        
        # Search in approved policies
        policies = await dynamodb.scan_table('policies')
        matching_policy_files = []
        for policy in policies:
            if policy.get('status') != 'approved':
                continue
                
            for area in policy.get("policy_areas", []):
                for individual_policy in area.get("policies", []):
                    policy_file = individual_policy.get("policyFile")
                    if policy_file and isinstance(policy_file, dict):
                        s3_key = policy_file.get("s3_key", "") or policy_file.get("file_id", "")
                        filename = policy_file.get("name", "")
                        
                        if (search_term.lower() in s3_key.lower() or 
                            search_term.lower() in filename.lower()):
                            matching_policy_files.append({
                                'policy_id': policy.get('policy_id'),
                                's3_key': s3_key,
                                'filename': filename,
                                'file_url': policy_file.get("file_url"),
                                'cdn_url': policy_file.get("cdn_url")
                            })
        
        return {
            "success": True,
            "search_term": search_term,
            "metadata_matches": matching_metadata,
            "policy_file_matches": matching_policy_files
        }
        
    except Exception as e:
        logger.error(f"Debug search file error: {e}")
        return {"success": False, "error": str(e)}
