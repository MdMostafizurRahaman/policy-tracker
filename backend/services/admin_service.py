"""
Admin Service
Business logic for admin operations
"""
from datetime import datetime
from fastapi import HTTPException
from config.database import (
    get_users_collection,
    get_temp_submissions_collection,
    get_master_policies_collection,
    get_admin_actions_collection
)
from utils.security import hash_password
from utils.converters import convert_objectid
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class AdminService:
    """Admin service for administrative operations"""
    
    def __init__(self):
        self.users_collection = get_users_collection()
        self.temp_submissions_collection = get_temp_submissions_collection()
        self.master_policies_collection = get_master_policies_collection()
        self.admin_actions_collection = get_admin_actions_collection()
    
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
                logger.info("Super admin already exists")
                return False
        
        except Exception as e:
            logger.error(f"Error initializing super admin: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize admin: {str(e)}")
    
    async def fix_visibility_issues(self, admin_user: dict):
        """Fix visibility issues in master policies"""
        try:
            # Remove any visibility fields that might be causing issues
            result = await self.master_policies_collection.update_many(
                {},
                {"$unset": {"visibility": "", "is_public": "", "is_visible": ""}}
            )
            
            # Log admin action
            admin_log = {
                "action": "fix_visibility",
                "admin_id": str(admin_user["_id"]),
                "admin_email": admin_user["email"],
                "affected_count": result.modified_count,
                "timestamp": datetime.utcnow()
            }
            await self.admin_actions_collection.insert_one(admin_log)
            
            return {
                "success": True,
                "message": f"Fixed visibility for {result.modified_count} policies"
            }
        
        except Exception as e:
            logger.error(f"Error fixing visibility: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fix visibility: {str(e)}")
    
    async def migrate_old_data(self, admin_user: dict):
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
            
            # Log admin action
            admin_log = {
                "action": "migrate_old_data",
                "admin_id": str(admin_user["_id"]),
                "admin_email": admin_user["email"],
                "migrated_count": update_count,
                "timestamp": datetime.utcnow()
            }
            await self.admin_actions_collection.insert_one(admin_log)
            
            return {
                "success": True,
                "message": f"Migrated {update_count} old policies"
            }
        
        except Exception as e:
            logger.error(f"Error migrating data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to migrate data: {str(e)}")
    
    async def repair_historical_data(self, admin_user: dict):
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
            
            # Log admin action
            admin_log = {
                "action": "repair_historical_data",
                "admin_id": str(admin_user["_id"]),
                "admin_email": admin_user["email"],
                "repaired_count": repair_count,
                "timestamp": datetime.utcnow()
            }
            await self.admin_actions_collection.insert_one(admin_log)
            
            return {
                "success": True,
                "message": f"Repaired {repair_count} historical records"
            }
        
        except Exception as e:
            logger.error(f"Error repairing data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to repair data: {str(e)}")

# Create a global admin service instance
admin_service = AdminService()
