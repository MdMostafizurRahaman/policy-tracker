"""
Admin Service for DynamoDB
Business logic for admin operations using DynamoDB
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from config.dynamodb import get_dynamodb
from models.user_dynamodb import User
from models.admin_dynamodb import AdminData, SystemConfig, UserStats, AuditLog
from config.settings import settings

logger = logging.getLogger(__name__)

class AdminService:
    """Admin service for administrative operations with DynamoDB"""
    
    def __init__(self):
        self.dynamodb = None

    async def _ensure_connection(self):
        """Ensure DynamoDB connection is available"""
        if self.dynamodb is None:
            try:
                self.dynamodb = await get_dynamodb()
                return self.dynamodb is not None
            except Exception as e:
                logger.warning(f"DynamoDB not available: {str(e)}")
                return False
        return True

    async def initialize_super_admin(self, email: str, password: str) -> Dict[str, Any]:
        """Initialize super admin user"""
        try:
            # Check if DynamoDB is available
            if not await self._ensure_connection():
                logger.warning("DynamoDB not available - skipping super admin initialization")
                return {"status": "warning", "message": "DynamoDB not available"}

            # Check if super admin already exists
            existing_admin = await User.find_by_email(email)
            
            if existing_admin:
                logger.info("Super admin already exists")
                return {"status": "success", "message": "Super admin already exists"}
            
            # Create super admin user
            admin_user = await User.create_user(
                email=email,
                password=password,
                name="Super Administrator",
                role="super_admin"
            )
            
            if admin_user:
                # Log admin creation
                await AuditLog.log_action(
                    user_id=admin_user.user_id,
                    action="create_super_admin",
                    details={"email": email, "created_at": datetime.utcnow().isoformat()}
                )
                
                logger.info(f"Super admin created successfully: {email}")
                return {"status": "success", "message": "Super admin created successfully"}
            else:
                logger.error("Failed to create super admin")
                return {"status": "error", "message": "Failed to create super admin"}
                
        except Exception as e:
            logger.error(f"Error initializing super admin: {str(e)}")
            return {"status": "error", "message": f"Failed to initialize admin: {str(e)}"}

    async def get_all_users(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get all users with pagination"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            # Get all users (DynamoDB doesn't have built-in pagination like MongoDB)
            all_users = await User.get_all_users()
            
            # Manual pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_users = all_users[start_idx:end_idx]
            
            # Convert to response format
            users_data = []
            for user in paginated_users:
                user_dict = user.to_dict()
                user_dict.pop('password', None)  # Remove password from response
                users_data.append(user_dict)
            
            return {
                "status": "success",
                "users": users_data,
                "total": len(all_users),
                "page": page,
                "limit": limit,
                "total_pages": (len(all_users) + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return {"status": "error", "message": "Failed to fetch users"}

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            user = await User.find_by_id(user_id)
            
            if not user:
                return {"status": "error", "message": "User not found"}
            
            user_dict = user.to_dict()
            user_dict.pop('password', None)  # Remove password from response
            
            return {"status": "success", "user": user_dict}
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return {"status": "error", "message": "Failed to fetch user"}

    async def update_user_status(self, user_id: str, is_active: bool, admin_user_id: str) -> Dict[str, Any]:
        """Update user active status"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            user = await User.find_by_id(user_id)
            
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Update user status
            success = await user.update({"is_active": is_active})
            
            if success:
                # Log admin action
                await AuditLog.log_action(
                    user_id=admin_user_id,
                    action="update_user_status",
                    details={
                        "target_user_id": user_id,
                        "new_status": is_active,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                status_text = "activated" if is_active else "deactivated"
                return {"status": "success", "message": f"User {status_text} successfully"}
            else:
                return {"status": "error", "message": "Failed to update user status"}
                
        except Exception as e:
            logger.error(f"Error updating user status: {str(e)}")
            return {"status": "error", "message": "Failed to update user status"}

    async def delete_user(self, user_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Delete user (soft delete)"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            user = await User.find_by_id(user_id)
            
            if not user:
                return {"status": "error", "message": "User not found"}
            
            # Soft delete user
            success = await user.update({"is_active": False, "deleted_at": datetime.utcnow().isoformat()})
            
            if success:
                # Log admin action
                await AuditLog.log_action(
                    user_id=admin_user_id,
                    action="delete_user",
                    details={
                        "target_user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {"status": "success", "message": "User deleted successfully"}
            else:
                return {"status": "error", "message": "Failed to delete user"}
                
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return {"status": "error", "message": "Failed to delete user"}

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            # Get all users
            all_users = await User.get_all_users()
            
            # Calculate stats
            total_users = len(all_users)
            active_users = len([u for u in all_users if u.is_active])
            verified_users = len([u for u in all_users if u.is_email_verified])
            admin_users = len([u for u in all_users if u.role in ['admin', 'super_admin']])
            
            # Get recent registrations (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            recent_users = len([
                u for u in all_users 
                if u.created_at and u.created_at > thirty_days_ago
            ])
            
            return {
                "status": "success",
                "stats": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "verified_users": verified_users,
                    "admin_users": admin_users,
                    "recent_registrations": recent_users,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            return {"status": "error", "message": "Failed to fetch system statistics"}

    async def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            configs = await SystemConfig.get_all_configs()
            
            return {
                "status": "success",
                "config": configs
            }
            
        except Exception as e:
            logger.error(f"Error getting system config: {str(e)}")
            return {"status": "error", "message": "Failed to fetch system configuration"}

    async def update_system_config(self, config_key: str, config_value: Any, admin_user_id: str) -> Dict[str, Any]:
        """Update system configuration"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            success = await SystemConfig.set_config(config_key, config_value, admin_user_id)
            
            if success:
                # Log admin action
                await AuditLog.log_action(
                    user_id=admin_user_id,
                    action="update_config",
                    details={
                        "config_key": config_key,
                        "config_value": config_value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {"status": "success", "message": "Configuration updated successfully"}
            else:
                return {"status": "error", "message": "Failed to update configuration"}
                
        except Exception as e:
            logger.error(f"Error updating system config: {str(e)}")
            return {"status": "error", "message": "Failed to update configuration"}

    async def get_audit_logs(self, page: int = 1, limit: int = 50, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get audit logs with pagination"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            # Get audit logs
            all_logs = await AuditLog.get_audit_logs(user_id=user_id, limit=limit * 2)  # Get more than needed for pagination
            
            # Manual pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_logs = all_logs[start_idx:end_idx]
            
            return {
                "status": "success",
                "logs": paginated_logs,
                "page": page,
                "limit": limit,
                "total": len(all_logs)
            }
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return {"status": "error", "message": "Failed to fetch audit logs"}

    async def promote_user_to_admin(self, user_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Promote user to admin role"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            user = await User.find_by_id(user_id)
            
            if not user:
                return {"status": "error", "message": "User not found"}
            
            if user.role == 'super_admin':
                return {"status": "error", "message": "Cannot modify super admin"}
            
            # Update user role
            success = await user.update({"role": "admin"})
            
            if success:
                # Log admin action
                await AuditLog.log_action(
                    user_id=admin_user_id,
                    action="promote_to_admin",
                    details={
                        "target_user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {"status": "success", "message": "User promoted to admin successfully"}
            else:
                return {"status": "error", "message": "Failed to promote user"}
                
        except Exception as e:
            logger.error(f"Error promoting user: {str(e)}")
            return {"status": "error", "message": "Failed to promote user"}

    async def demote_admin_to_user(self, user_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Demote admin to regular user"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available"}

            user = await User.find_by_id(user_id)
            
            if not user:
                return {"status": "error", "message": "User not found"}
            
            if user.role == 'super_admin':
                return {"status": "error", "message": "Cannot demote super admin"}
            
            # Update user role
            success = await user.update({"role": "user"})
            
            if success:
                # Log admin action
                await AuditLog.log_action(
                    user_id=admin_user_id,
                    action="demote_from_admin",
                    details={
                        "target_user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {"status": "success", "message": "Admin demoted to user successfully"}
            else:
                return {"status": "error", "message": "Failed to demote admin"}
                
        except Exception as e:
            logger.error(f"Error demoting admin: {str(e)}")
            return {"status": "error", "message": "Failed to demote admin"}
    
    async def get_submissions(self, page: int = 1, limit: int = 10, status: str = "all") -> Dict[str, Any]:
        """Get policy submissions for admin review"""
        try:
            if not await self._ensure_connection():
                return {"status": "error", "message": "Database not available", "data": []}
            
            # Get all policies directly from DynamoDB
            all_policies = await self.dynamodb.scan_table('policies')
            
            # Filter by status if specified
            if status != "all":
                all_policies = [p for p in all_policies if p.get('status') == status]
            
            # Sort by created_at (newest first)
            all_policies.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Manual pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_policies = all_policies[start_idx:end_idx]
            
            # Convert to admin submission format
            submissions = []
            for policy in paginated_policies:
                # Extract policy count from policy_areas
                policy_count = 0
                policy_areas = policy.get('policy_areas', [])
                for area in policy_areas:
                    policy_count += len(area.get('policies', []))
                
                submission = {
                    "policy_id": policy.get('policy_id'),
                    "submission_id": policy.get('policy_id'),  # Alias for compatibility
                    "user_id": policy.get('user_id'),
                    "user_email": policy.get('user_email'),
                    "country": policy.get('country'),
                    "submission_type": policy.get('submission_type', 'form'),
                    "status": policy.get('status', 'pending_review'),
                    "created_at": policy.get('created_at'),
                    "updated_at": policy.get('updated_at'),
                    "policy_areas": policy_areas,
                    "total_policies": policy.get('total_policies', policy_count),
                    "score": policy.get('score', 0),
                    "completeness_score": policy.get('completeness_score', 0),
                    "admin_notes": policy.get('admin_notes', ''),
                    "reviewed_by": policy.get('reviewed_by', ''),
                    "reviewed_at": policy.get('reviewed_at', ''),
                    "file_metadata": policy.get('file_metadata', {})
                }
                submissions.append(submission)
            
            logger.info(f"Retrieved {len(submissions)} submissions out of {len(all_policies)} total")
            
            return {
                "status": "success",
                "data": submissions,  # Changed from 'submissions' to 'data' for consistency
                "total": len(all_policies),
                "page": page,
                "limit": limit,
                "filtered_by": status,
                "total_pages": (len(all_policies) + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Error getting submissions: {str(e)}")
            return {"status": "error", "message": f"Failed to get submissions: {str(e)}", "data": []}
    async def get_statistics(self) -> Dict[str, Any]:
        """Get admin statistics"""
        try:
            return await self.get_system_stats()
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {"status": "error", "message": f"Failed to get statistics: {str(e)}"}

    async def approve_policy(self, submission_id: str, area_id: str, policy_index: int, admin_notes: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a policy and make it visible on the map"""
        try:
            if not await self._ensure_connection():
                raise Exception("Database connection not available")
            
            # Get the submission
            submission = await self.dynamodb.get_item('policies', {'policy_id': submission_id})
            if not submission:
                raise Exception(f"Submission {submission_id} not found")
            
            # Find the specific policy to approve
            policy_areas = submission.get('policy_areas', [])
            area_found = False
            for area in policy_areas:
                if area.get('area_id') == area_id:
                    if policy_index < len(area.get('policies', [])):
                        # Update policy status to approved
                        area['policies'][policy_index]['status'] = 'approved'
                        area['policies'][policy_index]['admin_notes'] = admin_notes
                        area['policies'][policy_index]['approved_at'] = datetime.utcnow().isoformat()
                        area['policies'][policy_index]['approved_by'] = admin_user.get('email')
                        area['policies'][policy_index]['map_visible'] = True
                        area_found = True
                        break
            
            if not area_found:
                raise Exception(f"Policy not found at area_id: {area_id}, policy_index: {policy_index}")
            
            # Update submission in database
            submission['updated_at'] = datetime.utcnow().isoformat()
            await self.dynamodb.update_item('policies', {'policy_id': submission_id}, submission)
            
            logger.info(f"Policy approved: {submission_id} - {area_id}[{policy_index}] by {admin_user.get('email')}")
            
            return {
                "success": True,
                "message": "Policy approved successfully",
                "policy_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index,
                "status": "approved"
            }
            
        except Exception as e:
            logger.error(f"Error approving policy: {str(e)}")
            raise Exception(f"Failed to approve policy: {str(e)}")

    async def reject_policy(self, submission_id: str, area_id: str, policy_index: int, admin_notes: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a policy and remove it from map visibility"""
        try:
            if not await self._ensure_connection():
                raise Exception("Database connection not available")
            
            # Get the submission
            submission = await self.dynamodb.get_item('policies', {'policy_id': submission_id})
            if not submission:
                raise Exception(f"Submission {submission_id} not found")
            
            # Find the specific policy to reject
            policy_areas = submission.get('policy_areas', [])
            area_found = False
            for area in policy_areas:
                if area.get('area_id') == area_id:
                    if policy_index < len(area.get('policies', [])):
                        # Update policy status to rejected
                        area['policies'][policy_index]['status'] = 'rejected'
                        area['policies'][policy_index]['admin_notes'] = admin_notes
                        area['policies'][policy_index]['rejected_at'] = datetime.utcnow().isoformat()
                        area['policies'][policy_index]['rejected_by'] = admin_user.get('email')
                        area['policies'][policy_index]['map_visible'] = False
                        area_found = True
                        break
            
            if not area_found:
                raise Exception(f"Policy not found at area_id: {area_id}, policy_index: {policy_index}")
            
            # Update submission in database
            submission['updated_at'] = datetime.utcnow().isoformat()
            await self.dynamodb.update_item('policies', {'policy_id': submission_id}, submission)
            
            logger.info(f"Policy rejected: {submission_id} - {area_id}[{policy_index}] by {admin_user.get('email')}")
            
            return {
                "success": True,
                "message": "Policy rejected successfully",
                "policy_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index,
                "status": "rejected"
            }
            
        except Exception as e:
            logger.error(f"Error rejecting policy: {str(e)}")
            raise Exception(f"Failed to reject policy: {str(e)}")

    async def commit_policy_to_master(self, submission_id: str, area_id: str, policy_index: int, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Commit an approved policy to the master database"""
        try:
            if not await self._ensure_connection():
                raise Exception("Database connection not available")
            
            # Get the submission
            submission = await self.dynamodb.get_item('policies', {'policy_id': submission_id})
            if not submission:
                raise Exception(f"Submission {submission_id} not found")
            
            # Find the specific policy to commit
            policy_areas = submission.get('policy_areas', [])
            policy_to_commit = None
            for area in policy_areas:
                if area.get('area_id') == area_id:
                    if policy_index < len(area.get('policies', [])):
                        policy = area['policies'][policy_index]
                        if policy.get('status') == 'approved':
                            policy_to_commit = policy.copy()
                            policy_to_commit['master_id'] = f"master_{submission_id}_{area_id}_{policy_index}"
                            policy_to_commit['committed_at'] = datetime.utcnow().isoformat()
                            policy_to_commit['committed_by'] = admin_user.get('email')
                            policy_to_commit['source_submission_id'] = submission_id
                            break
            
            if not policy_to_commit:
                raise Exception("Policy not found or not approved")
            
            # Save to master policies table (we can use the same table with a different status)
            master_policy = {
                "policy_id": policy_to_commit['master_id'],
                "user_id": submission.get('user_id'),
                "user_email": submission.get('user_email'),
                "country": submission.get('country'),
                "policy_areas": [{
                    "area_id": area_id,
                    "area_name": area.get('area_name'),
                    "policies": [policy_to_commit]
                }],
                "status": "master",
                "master_status": "active",
                "created_at": policy_to_commit['committed_at'],
                "updated_at": policy_to_commit['committed_at']
            }
            
            await self.dynamodb.insert_item('policies', master_policy)
            
            logger.info(f"Policy committed to master: {policy_to_commit['master_id']} by {admin_user.get('email')}")
            
            return {
                "success": True,
                "message": "Policy committed to master successfully",
                "master_id": policy_to_commit['master_id'],
                "policy_id": submission_id,
                "area_id": area_id,
                "policy_index": policy_index
            }
            
        except Exception as e:
            logger.error(f"Error committing policy to master: {str(e)}")
            raise Exception(f"Failed to commit policy to master: {str(e)}")

    async def delete_policy_completely(self, policy_id: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Completely delete a policy from database and map"""
        try:
            if not await self._ensure_connection():
                raise Exception("Database connection not available")
            
            # Delete from policies table
            deleted = await self.dynamodb.delete_item('policies', {'policy_id': policy_id})
            
            if deleted:
                logger.info(f"Policy completely deleted: {policy_id} by {admin_user.get('email')}")
                return {
                    "success": True,
                    "message": "Policy deleted completely",
                    "policy_id": policy_id
                }
            else:
                raise Exception(f"Policy {policy_id} not found")
            
        except Exception as e:
            logger.error(f"Error deleting policy completely: {str(e)}")
            raise Exception(f"Failed to delete policy completely: {str(e)}")

    async def get_approved_policies(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get all approved policies for map visualization"""
        try:
            if not await self._ensure_connection():
                raise Exception("Database connection not available")
            
            # Get all policies from database
            all_policies = await self.dynamodb.scan_table('policies')
            
            # Filter for approved policies that are map visible
            approved_policies = []
            for policy in all_policies:
                policy_areas = policy.get('policy_areas', [])
                for area in policy_areas:
                    for p in area.get('policies', []):
                        if p.get('status') == 'approved' and p.get('map_visible', False):
                            approved_policy = {
                                "policy_id": policy.get('policy_id'),
                                "country": policy.get('country'),
                                "area_id": area.get('area_id'),
                                "area_name": area.get('area_name'),
                                "policy_name": p.get('policyName'),
                                "policy_description": p.get('policyDescription'),
                                "approved_at": p.get('approved_at'),
                                "approved_by": p.get('approved_by'),
                                "map_visible": p.get('map_visible', False)
                            }
                            approved_policies.append(approved_policy)
            
            # Paginate results
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_policies = approved_policies[start_idx:end_idx]
            
            return {
                "success": True,
                "policies": paginated_policies,
                "total": len(approved_policies),
                "page": page,
                "limit": limit,
                "total_pages": (len(approved_policies) + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"Error getting approved policies: {str(e)}")
            raise Exception(f"Failed to get approved policies: {str(e)}")

    async def get_policy_files(self, policy_id: str) -> Dict[str, Any]:
        """Get all files associated with a policy"""
        try:
            if not await self._ensure_connection():
                raise Exception("Database connection not available")
            
            # Get all file metadata for this policy
            all_files = await self.dynamodb.scan_table('file_metadata')
            policy_files = [f for f in all_files if f.get('policy_id') == policy_id]
            
            return {
                "success": True,
                "policy_id": policy_id,
                "files": policy_files,
                "total_files": len(policy_files)
            }
            
        except Exception as e:
            logger.error(f"Error getting policy files: {str(e)}")
            raise Exception(f"Failed to get policy files: {str(e)}")

    async def upload_policy_file(self, policy_id: str, file_data: Dict[str, Any], admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file for a specific policy"""
        try:
            if not await self._ensure_connection():
                raise Exception("Database connection not available")
            
            # Create file metadata entry
            file_metadata = {
                "file_id": file_data.get('file_id'),
                "policy_id": policy_id,
                "filename": file_data.get('filename'),
                "file_type": file_data.get('file_type'),
                "file_size": file_data.get('file_size'),
                "s3_url": file_data.get('s3_url'),
                "uploaded_by": admin_user.get('email'),
                "uploaded_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            await self.dynamodb.insert_item('file_metadata', file_metadata)
            
            logger.info(f"File uploaded for policy {policy_id}: {file_data.get('filename')} by {admin_user.get('email')}")
            
            return {
                "success": True,
                "message": "File uploaded successfully",
                "policy_id": policy_id,
                "file_id": file_data.get('file_id'),
                "filename": file_data.get('filename')
            }
            
        except Exception as e:
            logger.error(f"Error uploading policy file: {str(e)}")
            raise Exception(f"Failed to upload policy file: {str(e)}")

# Create singleton instance
admin_service = AdminService()
