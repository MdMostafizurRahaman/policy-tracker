"""
DynamoDB Policy management service.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
import uuid
from config.dynamodb import get_dynamodb
from config.data_constants import POLICY_AREAS
from utils.helpers import convert_objectid, calculate_policy_score, calculate_completeness_score

logger = logging.getLogger(__name__)

class PolicyService:
    def __init__(self):
        pass
    
    async def _get_db(self):
        """Get DynamoDB client"""
        return await get_dynamodb()
    
    async def submit_policy(self, submission_data: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new policy for review"""
        try:
            db = await self._get_db()
            logger.info(f"Enhanced submission received from user {user['email']}")
            
            # Validate user owns this submission
            if submission_data["user_id"] != user["user_id"]:
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
                "policy_id": str(uuid.uuid4()),
                "user_id": submission_data["user_id"],
                "user_email": submission_data["user_email"],
                "country": submission_data["country"],
                "submission_type": submission_data.get("submission_type", "form"),
                "policy_areas": filtered_policy_areas,
                "total_policies": total_policies,
                "status": "pending_review",
                "admin_notes": "",
                "score": 0,
                "completeness_score": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Calculate scores
            submission_dict["score"] = calculate_policy_score(submission_dict)
            submission_dict["completeness_score"] = calculate_completeness_score(submission_dict)
            
            # Save to policies table
            success = await db.insert_item('policies', submission_dict)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save submission")
            
            logger.info(f"✅ Submission saved with ID: {submission_dict['policy_id']}")
            
            return {
                "message": "Policy submission successful",
                "submission_id": submission_dict['policy_id'],
                "status": "pending_review",
                "total_policies": total_policies,
                "score": submission_dict["score"],
                "completeness_score": submission_dict["completeness_score"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Policy submission error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

    async def submit_enhanced_form(self, submission_data: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Submit enhanced form - alias for submit_policy for backward compatibility"""
        return await self.submit_policy(submission_data, user)

    async def get_user_submissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all submissions for a user"""
        try:
            db = await self._get_db()
            
            # Scan policies table for user submissions
            all_policies = await db.scan_table('policies')
            user_policies = [p for p in all_policies if p.get('user_id') == user_id]
            
            # Sort by created_at desc
            user_policies.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return user_policies
            
        except Exception as e:
            logger.error(f"Error getting user submissions: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get user submissions")

    async def get_submission_by_id(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get submission by ID"""
        try:
            db = await self._get_db()
            
            # Get policy by ID
            policy = await db.get_item('policies', {'policy_id': submission_id})
            return policy
            
        except Exception as e:
            logger.error(f"Error getting submission: {str(e)}")
            return None

    async def update_policy_status(self, status_update: Dict[str, Any], admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Update policy status (admin only)"""
        try:
            db = await self._get_db()
            submission_id = status_update["submission_id"]
            new_status = status_update["status"]
            admin_notes = status_update.get("admin_notes", "")
            
            # Get existing policy
            policy = await db.get_item('policies', {'policy_id': submission_id})
            if not policy:
                raise HTTPException(status_code=404, detail="Submission not found")
            
            # Update policy
            update_data = {
                "status": new_status,
                "admin_notes": admin_notes,
                "reviewed_by": admin_user["email"],
                "reviewed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # If approved, mark for map visibility
            if new_status == "approved":
                update_data["visible_on_map"] = True
                update_data["approved_at"] = datetime.utcnow().isoformat()
                
                # Create individual policy entries for map visualization
                await self._create_map_policy_entries(policy, admin_user)
            else:
                update_data["visible_on_map"] = False
            
            success = await db.update_item('policies', {'policy_id': submission_id}, update_data)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update policy status")
            
            logger.info(f"Policy {submission_id} status updated to {new_status} by {admin_user['email']}")
            
            return {
                "message": "Policy status updated successfully",
                "submission_id": submission_id,
                "new_status": new_status,
                "visible_on_map": new_status == "approved"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating policy status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update policy status")

    async def _create_map_policy_entries(self, policy: Dict[str, Any], admin_user: Dict[str, Any]):
        """Create individual policy entries for map visualization"""
        try:
            db = await self._get_db()
            
            # Create entries for each policy in each area
            for area in policy.get("policy_areas", []):
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
                        "approved_by": admin_user["email"],
                        "approved_at": datetime.utcnow().isoformat(),
                        "created_at": datetime.utcnow().isoformat(),
                        "user_id": policy["user_id"],
                        "user_email": policy["user_email"]
                    }
                    
                    # Save to map_policies table
                    await db.insert_item('map_policies', map_policy_entry)
            
            logger.info(f"Created map policy entries for submission {policy['policy_id']}")
            
        except Exception as e:
            logger.error(f"Error creating map policy entries: {str(e)}")
            # Don't raise exception as this is supplementary functionality
            
    async def get_approved_policies_for_map(self, country: str = None) -> List[Dict[str, Any]]:
        """Get approved policies for map visualization"""
        try:
            db = await self._get_db()
            
            # Get all approved map policies
            all_map_policies = await db.scan_table('map_policies')
            
            # Filter by country if specified
            if country:
                filtered_policies = [
                    p for p in all_map_policies 
                    if p.get('country', '').lower() == country.lower() 
                    and p.get('visible_on_map', False)
                ]
            else:
                filtered_policies = [
                    p for p in all_map_policies 
                    if p.get('visible_on_map', False)
                ]
            
            # Sort by approved date (newest first)
            filtered_policies.sort(
                key=lambda x: x.get('approved_at', ''), 
                reverse=True
            )
            
            return filtered_policies
            
        except Exception as e:
            logger.error(f"Error getting approved policies for map: {str(e)}")
            return []

    async def get_country_policies(self, country_name: str) -> List[Dict[str, Any]]:
        """Get policies for a specific country"""
        try:
            db = await self._get_db()
            
            # Get all approved policies for country
            all_policies = await db.scan_table('policies')
            country_policies = [
                p for p in all_policies 
                if p.get('country', '').lower() == country_name.lower() 
                and p.get('status') == 'approved'
            ]
            
            # Sort by created_at desc
            country_policies.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return country_policies
            
        except Exception as e:
            logger.error(f"Error getting country policies: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get country policies")

    async def search_policies(self, query: str, country: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search policies by query"""
        try:
            db = await self._get_db()
            
            # Get all approved policies
            all_policies = await db.scan_table('policies')
            approved_policies = [p for p in all_policies if p.get('status') == 'approved']
            
            # Filter by country if specified
            if country:
                approved_policies = [p for p in approved_policies if p.get('country', '').lower() == country.lower()]
            
            # Simple text search
            query_lower = query.lower()
            matching_policies = []
            
            for policy in approved_policies:
                # Search in policy areas and policy names
                policy_text = f"{policy.get('country', '')} ".lower()
                for area in policy.get('policy_areas', []):
                    policy_text += f"{area.get('area_name', '')} ".lower()
                    for pol in area.get('policies', []):
                        policy_text += f"{pol.get('policyName', '')} {pol.get('description', '')} ".lower()
                
                if query_lower in policy_text:
                    matching_policies.append(policy)
            
            # Limit results
            return matching_policies[:limit]
            
        except Exception as e:
            logger.error(f"Error searching policies: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to search policies")

    async def get_policy_statistics(self) -> Dict[str, Any]:
        """Get policy statistics"""
        try:
            db = await self._get_db()
            
            # Get all policies
            all_policies = await db.scan_table('policies')
            
            # Calculate statistics
            total_policies = len(all_policies)
            approved_policies = len([p for p in all_policies if p.get('status') == 'approved'])
            pending_policies = len([p for p in all_policies if p.get('status') == 'pending_review'])
            rejected_policies = len([p for p in all_policies if p.get('status') == 'rejected'])
            
            # Count by country
            countries = {}
            for policy in all_policies:
                country = policy.get('country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
            
            return {
                "total_policies": total_policies,
                "approved_policies": approved_policies,
                "pending_policies": pending_policies,
                "rejected_policies": rejected_policies,
                "countries_covered": len(countries),
                "policies_by_country": countries,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting policy statistics: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get policy statistics")

# Global instance
policy_service = PolicyService()
