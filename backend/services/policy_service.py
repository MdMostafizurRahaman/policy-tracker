"""
Policy management service.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from bson import ObjectId
from core.database import get_collections
from core.constants import POLICY_AREAS
from utils.helpers import convert_objectid, calculate_policy_score, calculate_completeness_score

logger = logging.getLogger(__name__)

class PolicyService:
    def __init__(self):
        pass
    
    def _get_collections(self):
        """Get collections dynamically"""
        return get_collections()
    
    async def submit_policy(self, submission_data: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new policy for review"""
        try:
            collections = self._get_collections()
            logger.info(f"Enhanced submission received from user {user['email']}")
            
            # Validate user owns this submission
            if submission_data["user_id"] != str(user["_id"]):
                raise HTTPException(status_code=403, detail="Unauthorized submission")
            
            # Filter out empty policy areas and policies
            filtered_policy_areas = []
            total_policies = 0
            
            for area in submission_data["policyAreas"]:
                non_empty_policies = [
                    policy for policy in area["policies"] 
                    if policy.get("policyName") and policy["policyName"].strip()
                ]
                if non_empty_policies:
                    area_dict = {
                        "area_id": area["area_id"],
                        "area_name": area["area_name"],
                        "policies": non_empty_policies
                    }
                    filtered_policy_areas.append(area_dict)
                    total_policies += len(non_empty_policies)
            
            if not filtered_policy_areas:
                raise HTTPException(
                    status_code=400, 
                    detail="At least one policy with a name must be provided"
                )
            
            # Prepare submission document
            submission_dict = {
                "user_id": submission_data["user_id"],
                "user_email": submission_data["user_email"],
                "user_name": submission_data["user_name"],
                "country": submission_data["country"],
                "policyAreas": filtered_policy_areas,
                "submission_status": "pending",
                "total_policies": total_policies,
                "total_areas": len(filtered_policy_areas),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert into temporary collection
            result = await collections["temp_submissions"].insert_one(submission_dict)
            
            if result.inserted_id:
                logger.info(
                    f"Enhanced submission successful: {total_policies} policies in "
                    f"{len(filtered_policy_areas)} areas from {submission_data['user_email']}"
                )
                
                return {
                    "success": True, 
                    "message": "Enhanced submission successful and is pending admin review", 
                    "submission_id": str(result.inserted_id),
                    "total_policies": total_policies,
                    "policy_areas_count": len(filtered_policy_areas)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to save submission")
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Enhanced submission error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")
    
    async def update_policy_status(self, update_data: Dict[str, Any], admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Update policy status (admin only)"""
        try:
            collections = get_collections()
            submission_id = update_data["submission_id"]
            area_id = update_data["area_id"]
            policy_index = update_data["policy_index"]
            new_status = update_data["status"]
            admin_notes = update_data.get("admin_notes", "")
            
            # Find the submission
            submission = await collections["temp_submissions"].find_one({"_id": ObjectId(submission_id)})
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            
            # Find the policy area and validate policy exists
            area_found = False
            policy_areas = submission.get("policyAreas", [])
            
            for i, area in enumerate(policy_areas):
                if area["area_id"] == area_id:
                    if policy_index >= len(area["policies"]):
                        raise HTTPException(status_code=404, detail="Policy not found")
                    
                    # Update policy status
                    policy_areas[i]["policies"][policy_index]["status"] = new_status
                    policy_areas[i]["policies"][policy_index]["admin_notes"] = admin_notes
                    policy_areas[i]["policies"][policy_index]["reviewed_at"] = datetime.utcnow()
                    policy_areas[i]["policies"][policy_index]["reviewed_by"] = admin_user["email"]
                    area_found = True
                    break
            
            if not area_found:
                raise HTTPException(status_code=404, detail="Policy area not found")
            
            # Update submission
            await collections["temp_submissions"].update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {
                    "policyAreas": policy_areas,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Log admin action
            admin_log = {
                "action": f"status_update_{new_status}",
                "submission_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index,
                "admin_id": str(admin_user["_id"]),
                "admin_email": admin_user["email"],
                "admin_notes": admin_notes,
                "timestamp": datetime.utcnow()
            }
            await collections["admin_actions"].insert_one(admin_log)
            
            # If approved, move to master DB immediately
            if new_status == 'approved':
                await self._move_policy_to_master(submission, area_id, policy_index, admin_user)
            
            # Update overall submission status
            await self._update_submission_status(submission_id)
            
            logger.info(f"Policy status updated to {new_status} by {admin_user['email']}")
            return {"success": True, "message": f"Policy status updated to {new_status}"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Policy status update error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")
    
    async def _move_policy_to_master(self, submission: dict, area_id: str, policy_index: int, admin_user: dict):
        """Move approved policy to master database"""
        try:
            collections = get_collections()
            
            # Get the policy
            policy = None
            for area in submission.get("policyAreas", []):
                if area["area_id"] == area_id:
                    if policy_index < len(area["policies"]):
                        policy = area["policies"][policy_index]
                        break
            
            if not policy:
                return
            
            # Check if already moved to master
            existing_master = await collections["master_policies"].find_one({
                "original_submission_id": str(submission["_id"]),
                "policyArea": area_id,
                "policy_index": policy_index,
                "master_status": "active"
            })
            
            if existing_master:
                return  # Already in master DB
            
            # Get area info for enhanced data
            area_info = next((area for area in POLICY_AREAS if area["id"] == area_id), None)
            
            # Prepare policy for master DB with enhanced metadata
            master_policy = {
                **policy,
                "country": submission["country"],
                "policyArea": area_id,
                "area_name": area_info["name"] if area_info else area_id,
                "area_icon": area_info["icon"] if area_info else "📄",
                "area_color": area_info["color"] if area_info else "from-gray-500 to-gray-600",
                "user_id": submission["user_id"],
                "user_email": submission.get("user_email", ""),
                "user_name": submission.get("user_name", ""),
                "original_submission_id": str(submission["_id"]),
                "policy_index": policy_index,
                "moved_to_master_at": datetime.utcnow(),
                "approved_by": str(admin_user["_id"]),
                "approved_by_email": admin_user["email"],
                "master_status": "active",
                "policy_score": calculate_policy_score(policy),
                "completeness_score": calculate_completeness_score(policy)
            }
            
            # Insert into master collection
            result = await collections["master_policies"].insert_one(master_policy)
            
            if result.inserted_id:
                logger.info(f"Policy moved to master DB: {policy.get('policyName', 'Unnamed')} from {submission['country']}")
        
        except Exception as e:
            logger.error(f"Error moving policy to master: {str(e)}")
    
    async def _update_submission_status(self, submission_id: str):
        """Update overall submission status based on individual policies"""
        try:
            collections = get_collections()
            submission = await collections["temp_submissions"].find_one({"_id": ObjectId(submission_id)})
            if not submission:
                return
            
            policy_areas = submission.get("policyAreas", [])
            if not policy_areas:
                new_status = "empty"
            else:
                all_policies = []
                for area in policy_areas:
                    all_policies.extend(area.get("policies", []))
                
                if not all_policies:
                    new_status = "empty"
                else:
                    policy_statuses = [p.get("status", "pending") for p in all_policies]
                    
                    approved_count = sum(1 for status in policy_statuses if status == "approved")
                    total_count = len(policy_statuses)
                    
                    if approved_count == total_count:
                        new_status = "approved"
                    elif approved_count > 0:
                        new_status = "partially_approved"
                    elif any(status == "rejected" for status in policy_statuses):
                        new_status = "rejected"
                    else:
                        new_status = "pending"
            
            await collections["temp_submissions"].update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {
                    "submission_status": new_status, 
                    "updated_at": datetime.utcnow()
                }}
            )
        except Exception as e:
            logger.error(f"Error updating submission status: {e}")
    
    async def get_public_policies(self, limit: int = 1000, country: str = None, area: str = None) -> List[Dict[str, Any]]:
        """Get public policies for the map"""
        try:
            collections = get_collections()
            
            # Filter for active master policies
            master_filter = {"master_status": "active"}
            
            if country:
                master_filter["country"] = country
            if area:
                master_filter["policyArea"] = area
            
            # Get policies from master collection
            master_policies = []
            async for doc in collections["master_policies"].find(master_filter).limit(limit).sort("moved_to_master_at", -1):
                policy_data = convert_objectid(doc)
                master_policies.append(policy_data)
            
            # Also check temp_submissions for approved policies that might not be migrated yet
            temp_filter = {}
            if country:
                temp_filter["country"] = country
            
            temp_policies = []
            async for submission in collections["temp_submissions"].find(temp_filter):
                for policy_area in submission.get("policyAreas", []):
                    if area and policy_area["area_id"] != area:
                        continue
                    
                    area_info = next((a for a in POLICY_AREAS if a["id"] == policy_area["area_id"]), None)
                    
                    for policy in policy_area.get("policies", []):
                        if policy.get("status") == "approved":
                            # Check if not already in master
                            exists_in_master = any(
                                mp.get("original_submission_id") == str(submission["_id"]) and 
                                mp.get("policyArea") == policy_area["area_id"] and
                                mp.get("policyName") == policy.get("policyName")
                                for mp in master_policies
                            )
                            
                            if not exists_in_master:
                                policy_data = {
                                    **convert_objectid(policy),
                                    "id": f"temp_{submission['_id']}_{policy_area['area_id']}_{policy.get('policyName', '')}",
                                    "country": submission["country"],
                                    "policyArea": policy_area["area_id"],
                                    "area_name": area_info["name"] if area_info else policy_area["area_id"],
                                    "area_icon": area_info["icon"] if area_info else "📄",
                                    "area_color": area_info["color"] if area_info else "from-gray-500 to-gray-600",
                                    "policy_score": calculate_policy_score(policy),
                                    "completeness_score": calculate_completeness_score(policy),
                                    "created_at": submission.get("created_at", datetime.utcnow())
                                }
                                temp_policies.append(policy_data)
            
            # Combine and deduplicate
            all_policies = master_policies + temp_policies
            
            # Simple deduplication by policy name and country
            seen = set()
            unique_policies = []
            for policy in all_policies:
                key = f"{policy.get('policyName', '')}-{policy.get('country', '')}-{policy.get('policyArea', '')}"
                if key not in seen:
                    seen.add(key)
                    unique_policies.append(policy)
            
            return unique_policies[:limit]
        
        except Exception as e:
            logger.error(f"Error getting public policies: {str(e)}")
            return []

# Global policy service instance
policy_service = PolicyService()
