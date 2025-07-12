"""
Admin Service
Business logic for admin operations
"""
from datetime import datetime
from typing import Dict, Any, List
from bson import ObjectId
import logging

from config.database import database
from config.constants import POLICY_AREAS, COUNTRIES
from utils.helpers import convert_objectid
from utils.security import hash_password

logger = logging.getLogger(__name__)


class AdminService:
    """Admin service for administrative operations"""
    
    def __init__(self):
        self._db = None
        self._users_collection = None
        self._temp_submissions_collection = None
        self._master_policies_collection = None
        self._admin_actions_collection = None

    @property
    def db(self):
        if self._db is None:
            self._db = database.db
        return self._db

    @property
    def users_collection(self):
        if self._users_collection is None:
            self._users_collection = self.db.users
        return self._users_collection

    @property
    def temp_submissions_collection(self):
        if self._temp_submissions_collection is None:
            self._temp_submissions_collection = self.db.temp_submissions
        return self._temp_submissions_collection

    @property
    def master_policies_collection(self):
        if self._master_policies_collection is None:
            self._master_policies_collection = self.db.master_policies
        return self._master_policies_collection

    @property
    def admin_actions_collection(self):
        if self._admin_actions_collection is None:
            self._admin_actions_collection = self.db.admin_actions
        return self._admin_actions_collection
    
    async def initialize_super_admin(self, email: str, password: str):
        """Initialize super admin account"""
        try:
            existing_admin = await self.users_collection.find_one({"email": email})
            
            if not existing_admin:
                admin_doc = {
                    "firstName": "Super",
                    "lastName": "Admin",
                    "email": email,
                    "password": hash_password(password),
                    "country": "Global",
                    "is_admin": True,
                    "is_super_admin": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await self.users_collection.insert_one(admin_doc)
                logger.info("Super admin created successfully")
                return True
            else:
                # Update existing admin to ensure super admin status
                await self.users_collection.update_one(
                    {"email": email},
                    {
                        "$set": {
                            "is_admin": True,
                            "is_super_admin": True,
                            "is_verified": True,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info("Super admin already exists and updated")
                return False
        
        except Exception as e:
            logger.error(f"Error initializing super admin: {e}")
            raise Exception(f"Failed to initialize admin: {str(e)}")

    async def get_submissions(self, page: int = 1, limit: int = 10, status: str = "all") -> Dict[str, Any]:
        """Get all submissions for admin review with pagination"""
        try:
            # Calculate skip for pagination
            skip = (page - 1) * limit
            
            # Build query filter
            query = {}
            if status != "all":
                query["submission_status"] = status
            
            # Get total count for pagination
            total_count = await self.temp_submissions_collection.count_documents(query)
            total_pages = (total_count + limit - 1) // limit  # Ceiling division
            
            # Get submissions with pagination
            submissions = []
            async for submission in self.temp_submissions_collection.find(query).skip(skip).limit(limit).sort("created_at", -1):
                submissions.append(convert_objectid(submission))
            
            return {
                "success": True,
                "submissions": submissions,
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "limit": limit
            }
        
        except Exception as e:
            logger.error(f"Error getting admin submissions: {str(e)}")
            raise Exception(f"Failed to get submissions: {str(e)}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get admin statistics"""
        try:
            # Count users
            total_users = await self.users_collection.count_documents({})
            verified_users = await self.users_collection.count_documents({"is_verified": True})
            admin_users = await self.users_collection.count_documents({"is_admin": True})
            
            # Count submissions
            total_submissions = await self.temp_submissions_collection.count_documents({})
            pending_submissions = await self.temp_submissions_collection.count_documents({
                "submission_status": "pending"
            })
            
            # Count master policies
            total_master_policies = await self.master_policies_collection.count_documents({
                "master_status": "active"
            })
            
            # Count policies by status
            approved_policies = 0
            rejected_policies = 0
            under_review_policies = 0
            
            async for submission in self.temp_submissions_collection.find({}):
                if "policyAreas" in submission:
                    for area in submission["policyAreas"]:
                        for policy in area.get("policies", []):
                            status = policy.get("status", "pending")
                            if status == "approved":
                                approved_policies += 1
                            elif status == "rejected":
                                rejected_policies += 1
                            elif status == "under_review":
                                under_review_policies += 1
            
            return {
                "success": True,
                "statistics": {
                    "users": {
                        "total": total_users,
                        "verified": verified_users,
                        "admin": admin_users
                    },
                    "submissions": {
                        "total": total_submissions,
                        "pending": pending_submissions
                    },
                    "policies": {
                        "master": total_master_policies,
                        "approved": approved_policies,
                        "rejected": rejected_policies,
                        "under_review": under_review_policies
                    }
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting admin statistics: {str(e)}")
            raise Exception(f"Failed to get statistics: {str(e)}")

    async def move_to_master(self, submission_id: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Move approved policies to master collection"""
        try:
            submission = await self.temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
            if not submission:
                raise Exception("Submission not found")
            
            moved_count = 0
            
            # Process each policy area
            for area in submission.get("policyAreas", []):
                area_info = next((a for a in POLICY_AREAS if a["id"] == area["area_id"]), None)
                
                for policy in area.get("policies", []):
                    if policy.get("status") == "approved":
                        # Create master policy document
                        master_policy = {
                            "policyName": policy.get("policyName", ""),
                            "policyDescription": policy.get("policyDescription", ""),
                            "country": submission.get("country", ""),
                            "policyArea": area.get("area_id", ""),
                            "area_name": area_info["name"] if area_info else area.get("area_name", ""),
                            "area_icon": area_info["icon"] if area_info else "📄",
                            "area_color": area_info["color"] if area_info else "from-gray-500 to-gray-600",
                            "targetGroups": policy.get("targetGroups", []),
                            "policyLink": policy.get("policyLink", ""),
                            "implementation": policy.get("implementation", {}),
                            "evaluation": policy.get("evaluation", {}),
                            "participation": policy.get("participation", {}),
                            "alignment": policy.get("alignment", {}),
                            "status": "Active",
                            "master_status": "active",
                            "original_submission_id": submission_id,
                            "submitted_by": submission.get("user_email", ""),
                            "moved_to_master_at": datetime.utcnow(),
                            "moved_by_admin": admin_user["email"],
                            "created_at": submission.get("created_at", datetime.utcnow()),
                            "updated_at": datetime.utcnow()
                        }
                        
                        await self.master_policies_collection.insert_one(master_policy)
                        moved_count += 1
            
            # Log admin action
            admin_log = {
                "action": "move_to_master",
                "admin_id": str(admin_user["_id"]),
                "admin_email": admin_user["email"],
                "submission_id": submission_id,
                "policies_moved": moved_count,
                "timestamp": datetime.utcnow()
            }
            await self.admin_actions_collection.insert_one(admin_log)
            
            return {
                "success": True,
                "message": f"Moved {moved_count} approved policies to master collection",
                "moved_count": moved_count
            }
        
        except Exception as e:
            logger.error(f"Error moving to master: {str(e)}")
            raise Exception(f"Failed to move to master: {str(e)}")

    async def fix_visibility(self) -> Dict[str, Any]:
        """Fix visibility issues in master policies"""
        try:
            # Remove any visibility fields that might be causing issues
            result = await self.master_policies_collection.update_many(
                {},
                {"$unset": {"visibility": "", "is_public": "", "is_visible": ""}}
            )
            
            return {
                "success": True,
                "message": f"Fixed visibility for {result.modified_count} policies",
                "fixed_count": result.modified_count
            }
        
        except Exception as e:
            logger.error(f"Error fixing visibility: {str(e)}")
            raise Exception(f"Failed to fix visibility: {str(e)}")

    async def migrate_old_data(self) -> Dict[str, Any]:
        """Migrate old data format to new format"""
        try:
            # Update old policies to include required fields
            update_count = 0
            
            async for policy in self.master_policies_collection.find({"master_status": {"$exists": False}}):
                updates = {
                    "master_status": "active",
                    "updated_at": datetime.utcnow()
                }
                
                # Add missing fields
                if "moved_to_master_at" not in policy:
                    updates["moved_to_master_at"] = policy.get("created_at", datetime.utcnow())
                
                if "area_icon" not in policy:
                    updates["area_icon"] = "📄"
                
                if "area_color" not in policy:
                    updates["area_color"] = "from-gray-500 to-gray-600"
                
                await self.master_policies_collection.update_one(
                    {"_id": policy["_id"]},
                    {"$set": updates}
                )
                update_count += 1
            
            return {
                "success": True,
                "message": f"Migrated {update_count} old policies",
                "migrated_count": update_count
            }
        
        except Exception as e:
            logger.error(f"Error migrating data: {str(e)}")
            raise Exception(f"Failed to migrate data: {str(e)}")

    async def repair_historical_data(self) -> Dict[str, Any]:
        """Repair historical data inconsistencies"""
        try:
            repair_count = 0
            
            # Fix policies without proper country field
            async for policy in self.master_policies_collection.find({"country": {"$in": [None, ""]}}):
                # Try to get country from original submission
                if policy.get("original_submission_id"):
                    submission = await self.temp_submissions_collection.find_one({
                        "_id": ObjectId(policy["original_submission_id"])
                    })
                    if submission and submission.get("country"):
                        await self.master_policies_collection.update_one(
                            {"_id": policy["_id"]},
                            {"$set": {"country": submission["country"]}}
                        )
                        repair_count += 1
                else:
                    # Set default country
                    await self.master_policies_collection.update_one(
                        {"_id": policy["_id"]},
                        {"$set": {"country": "Unknown"}}
                    )
                    repair_count += 1
            
            # Fix policies without policy area
            await self.master_policies_collection.update_many(
                {"policyArea": {"$in": [None, ""]}},
                {"$set": {"policyArea": "unknown"}}
            )
            
            return {
                "success": True,
                "message": f"Repaired {repair_count} historical records",
                "repaired_count": repair_count
            }
        
        except Exception as e:
            logger.error(f"Error repairing data: {str(e)}")
            raise Exception(f"Failed to repair data: {str(e)}")

    async def update_policy_status(self, submission_id: str, area_id: str, policy_index: int, status: str, admin_notes: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Update the status of a specific policy within a submission"""
        try:
            # Find the submission
            submission = await self.temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
            if not submission:
                raise Exception("Submission not found")
            
            # Find and update the policy in the policyAreas structure
            policy_areas = submission.get("policyAreas", [])
            area_found = False
            
            for i, area in enumerate(policy_areas):
                if area.get("area_id") == area_id:
                    if policy_index >= len(area.get("policies", [])):
                        raise Exception(f"Policy index {policy_index} out of range")
                    
                    # Update policy status
                    policy_areas[i]["policies"][policy_index]["status"] = status
                    policy_areas[i]["policies"][policy_index]["admin_notes"] = admin_notes
                    policy_areas[i]["policies"][policy_index]["updated_at"] = datetime.utcnow()
                    policy_areas[i]["policies"][policy_index]["reviewed_by"] = admin_user.get("email")
                    area_found = True
                    break
            
            if not area_found:
                raise Exception(f"Policy area '{area_id}' not found")
            
            # Update the submission with modified policy areas
            await self.temp_submissions_collection.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {"policyAreas": policy_areas, "updated_at": datetime.utcnow()}}
            )
            
            # Log admin action
            await self.admin_actions_collection.insert_one({
                "action": "update_policy_status",
                "admin_email": admin_user.get("email"),
                "submission_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index,
                "new_status": status,
                "admin_notes": admin_notes,
                "timestamp": datetime.utcnow()
            })
            
            # If approved, move to master collection
            if status == "approved":
                await self._move_policy_to_master(submission_id, area_id, policy_index, admin_user)
            # If rejected or deleted, remove from master collection if it exists there
            elif status in ["rejected", "deleted"]:
                await self._remove_policy_from_master_if_exists(submission_id, area_id, policy_index, admin_user)
            
            return {
                "success": True,
                "message": f"Policy status updated to {status}",
                "moved_to_master": status == "approved"
            }
            
        except Exception as e:
            logger.error(f"Error updating policy status: {str(e)}")
            raise Exception(f"Failed to update policy status: {str(e)}")

    async def _move_policy_to_master(self, submission_id: str, area_id: str, policy_index: int, admin_user: Dict[str, Any]):
        """Move a specific approved policy to master collection"""
        try:
            # Get the submission and specific policy
            submission = await self.temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
            if not submission:
                raise Exception(f"Submission not found: {submission_id}")
            
            # Check if the policyAreas structure exists (new format)
            if "policyAreas" not in submission:
                raise Exception(f"No policy areas found in submission: {submission_id}")
            
            # Find the policy area by area_id
            area_found = False
            policy = None
            
            for area in submission["policyAreas"]:
                if area.get("area_id") == area_id:
                    area_policies = area.get("policies", [])
                    if policy_index >= len(area_policies):
                        raise Exception(f"Policy index {policy_index} out of range for area '{area_id}' (has {len(area_policies)} policies)")
                    
                    policy = area_policies[policy_index]
                    area_found = True
                    break
            
            if not area_found:
                raise Exception(f"Policy area '{area_id}' not found in submission: {submission_id}")
                
            if not policy:
                raise Exception(f"Policy at index {policy_index} is empty or None")
            
            # Create master policy document
            master_policy = {
                "policyName": policy.get("policyName", ""),
                "policyId": policy.get("policyId", ""),
                "policyArea": area_id,
                "targetGroups": policy.get("targetGroups", []),
                "policyDescription": policy.get("policyDescription", ""),
                "policyFile": policy.get("policyFile", {}),
                "country": submission.get("country", ""),
                "email": submission.get("email", ""),
                "submittedAt": submission.get("submittedAt", datetime.utcnow()),
                "master_status": "active",
                "moved_to_master_at": datetime.utcnow(),
                "approved_by": admin_user.get("email"),
                "original_submission_id": submission_id,
                "original_area_id": area_id,
                "original_policy_index": policy_index
            }
            
            # Insert into master collection
            result = await self.master_policies_collection.insert_one(master_policy)
            
            # Log the action
            await self.admin_actions_collection.insert_one({
                "action": "move_to_master",
                "admin_email": admin_user.get("email"),
                "submission_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index,
                "master_policy_id": str(result.inserted_id),
                "timestamp": datetime.utcnow()
            })
            
            logger.info(f"Moved policy to master: {result.inserted_id}")
            
        except Exception as e:
            logger.error(f"Error moving policy to master: {str(e)}")
            raise Exception(f"Failed to move policy to master: {str(e)}")

    async def _remove_policy_from_master_if_exists(self, submission_id: str, area_id: str, policy_index: int, admin_user: Dict[str, Any]):
        """Remove a policy from master collection if it exists there (for rejected/deleted policies)"""
        try:
            # Find policies in master collection that match this submission and policy
            master_policy = await self.master_policies_collection.find_one({
                "submission_id": submission_id,
                "area_id": area_id, 
                "policy_index": policy_index,
                "master_status": "active"
            })
            
            if master_policy:
                # Mark as deleted in master collection
                await self.master_policies_collection.update_one(
                    {"_id": master_policy["_id"]},
                    {
                        "$set": {
                            "master_status": "deleted",
                            "deleted_at": datetime.utcnow(),
                            "deleted_by": admin_user.get("email"),
                            "deletion_reason": "Policy rejected/deleted in submission review"
                        }
                    }
                )
                
                # Log the removal action
                await self.admin_actions_collection.insert_one({
                    "action": "remove_from_master_on_rejection",
                    "admin_email": admin_user.get("email"),
                    "submission_id": submission_id,
                    "area_id": area_id,
                    "policy_index": policy_index,
                    "master_policy_id": str(master_policy["_id"]),
                    "timestamp": datetime.utcnow()
                })
                
                logger.info(f"Removed policy from master due to rejection: {master_policy['_id']}")
            
        except Exception as e:
            logger.error(f"Error removing policy from master: {str(e)}")
            # Don't raise exception here - this is a cleanup operation
            logger.warning(f"Failed to remove policy from master on rejection: {str(e)}")

    async def delete_master_policy(self, policy_id: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a policy from master collection (both DB and map)"""
        try:
            # Find the policy first
            policy = await self.master_policies_collection.find_one({"_id": ObjectId(policy_id)})
            if not policy:
                raise Exception("Policy not found")
            
            # Mark as deleted instead of hard delete (to maintain history)
            await self.master_policies_collection.update_one(
                {"_id": ObjectId(policy_id)},
                {
                    "$set": {
                        "master_status": "deleted",
                        "deleted_at": datetime.utcnow(),
                        "deleted_by": admin_user.get("email")
                    }
                }
            )
            
            # Log admin action
            await self.admin_actions_collection.insert_one({
                "action": "delete_master_policy",
                "admin_email": admin_user.get("email"),
                "policy_id": policy_id,
                "policy_name": policy.get("policyName", ""),
                "country": policy.get("country", ""),
                "policy_area": policy.get("policyArea", ""),
                "timestamp": datetime.utcnow()
            })
            
            return {
                "success": True,
                "message": "Policy deleted successfully",
                "policy_id": policy_id
            }
            
        except Exception as e:
            logger.error(f"Error deleting policy: {str(e)}")
            raise Exception(f"Failed to delete policy: {str(e)}")

    async def delete_submission_policy(self, submission_id: str, area_id: str, policy_index: int, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a specific policy from a submission"""
        try:
            # Find the submission
            submission = await self.temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
            if not submission:
                raise Exception("Submission not found")
            
            # Mark the policy as deleted
            status_path = f"policies.{area_id}.{policy_index}.status"
            deleted_path = f"policies.{area_id}.{policy_index}.deleted_at"
            deleted_by_path = f"policies.{area_id}.{policy_index}.deleted_by"
            
            await self.temp_submissions_collection.update_one(
                {"_id": ObjectId(submission_id)},
                {
                    "$set": {
                        status_path: "deleted",
                        deleted_path: datetime.utcnow(),
                        deleted_by_path: admin_user.get("email")
                    }
                }
            )
            
            # Log admin action
            await self.admin_actions_collection.insert_one({
                "action": "delete_submission_policy",
                "admin_email": admin_user.get("email"),
                "submission_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index,
                "timestamp": datetime.utcnow()
            })
            
            return {
                "success": True,
                "message": "Policy deleted from submission",
                "submission_id": submission_id
            }
            
        except Exception as e:
            logger.error(f"Error deleting submission policy: {str(e)}")
            raise Exception(f"Failed to delete submission policy: {str(e)}")


# Create a global admin service instance
admin_service = AdminService()
