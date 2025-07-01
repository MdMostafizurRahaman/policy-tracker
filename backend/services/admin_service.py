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

    async def get_submissions(self, limit: int = 50) -> Dict[str, Any]:
        """Get all submissions for admin review"""
        try:
            submissions = []
            async for submission in self.temp_submissions_collection.find({}).limit(limit).sort("created_at", -1):
                submissions.append(convert_objectid(submission))
            
            return {
                "success": True,
                "submissions": submissions,
                "total_count": len(submissions)
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


# Create a global admin service instance
admin_service = AdminService()
