"""
Policy Service
Business logic for policy management, submissions, and approval
"""
from datetime import datetime
from fastapi import HTTPException
from config.database import (
    get_temp_submissions_collection, 
    get_master_policies_collection,
    get_admin_actions_collection
)
from models.policy import EnhancedSubmission, PolicyStatusUpdate, POLICY_AREAS
from utils.converters import convert_objectid
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class PolicyService:
    """Policy management service"""
    
    def __init__(self):
        self.temp_submissions_collection = get_temp_submissions_collection()
        self.master_policies_collection = get_master_policies_collection()
        self.admin_actions_collection = get_admin_actions_collection()
    
    async def submit_enhanced_form(self, submission: EnhancedSubmission, user_id: str):
        """Submit enhanced policy form"""
        try:
            logger.info(f"Enhanced submission received from user {submission.user_email}")
            
            # Validate user owns this submission
            if submission.user_id != user_id:
                raise HTTPException(status_code=403, detail="Unauthorized submission")
            
            # Filter out empty policy areas and policies
            filtered_policy_areas = []
            total_policies = 0
            
            for area in submission.policyAreas:
                non_empty_policies = [
                    policy for policy in area.policies 
                    if policy.policyName and policy.policyName.strip()
                ]
                if non_empty_policies:
                    area_dict = {
                        "area_id": area.area_id,
                        "area_name": area.area_name,
                        "policies": [policy.dict() for policy in non_empty_policies]
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
                "user_id": submission.user_id,
                "user_email": submission.user_email,
                "user_name": submission.user_name,
                "country": submission.country,
                "policyAreas": filtered_policy_areas,
                "submission_status": "pending",
                "total_policies": total_policies,
                "total_areas": len(filtered_policy_areas),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert into temporary collection
            result = await self.temp_submissions_collection.insert_one(submission_dict)
            
            if result.inserted_id:
                logger.info(
                    f"Enhanced submission successful: {total_policies} policies in "
                    f"{len(filtered_policy_areas)} areas from {submission.user_email}"
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
    
    async def update_policy_status(self, status_update: PolicyStatusUpdate, admin_user: dict):
        """Update policy status with automatic master DB movement"""
        try:
            submission_id = status_update.submission_id
            area_id = status_update.area_id
            policy_index = status_update.policy_index
            new_status = status_update.status
            admin_notes = status_update.admin_notes
            
            # Find the submission
            submission = await self.temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            
            # Find the policy area and validate policy exists
            area_found = False
            policy_areas = submission.get("policyAreas", [])
            
            for i, area in enumerate(policy_areas):
                if area["area_id"] == area_id:
                    if policy_index >= len(area["policies"]):
                        raise HTTPException(status_code=404, detail="Policy index out of range")
                    
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
            await self.temp_submissions_collection.update_one(
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
            await self.admin_actions_collection.insert_one(admin_log)
            
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
    
    async def get_public_master_policies(self, limit: int = 1000, country: str = None, area: str = None):
        """Get public master policies with filtering"""
        try:
            # Build filter
            master_filter = {"master_status": "active"}
            
            if country:
                master_filter["country"] = country
            if area:
                master_filter["policyArea"] = area
            
            # Get policies from master collection
            master_policies = []
            async for doc in self.master_policies_collection.find(master_filter).limit(limit).sort("moved_to_master_at", -1):
                master_policies.append(convert_objectid(doc))
            
            # Get statistics
            stats = await self._get_master_policy_statistics()
            
            return {
                "success": True,
                "policies": master_policies,
                "total_count": len(master_policies),
                "statistics": stats
            }
        
        except Exception as e:
            logger.error(f"Error getting master policies: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve policies: {str(e)}")
    
    async def _move_policy_to_master(self, submission: dict, area_id: str, policy_index: int, admin_user: dict):
        """Internal function to move approved policy to master database"""
        try:
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
            existing_master = await self.master_policies_collection.find_one({
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
                "policy_score": self._calculate_policy_score(policy),
                "completeness_score": self._calculate_completeness_score(policy)
            }
            
            # Insert into master collection
            result = await self.master_policies_collection.insert_one(master_policy)
            
            if result.inserted_id:
                logger.info(f"Policy moved to master DB: {policy.get('policyName', 'Unnamed')} from {submission['country']}")
        
        except Exception as e:
            logger.error(f"Error moving policy to master: {str(e)}")
    
    def _calculate_policy_score(self, policy: dict) -> int:
        """Calculate policy completeness score (0-100)"""
        score = 0
        
        # Basic info (30 points)
        if policy.get("policyName"):
            score += 10
        if policy.get("policyId"):
            score += 5
        if policy.get("policyDescription"):
            score += 15
        
        # Implementation details (25 points)
        impl = policy.get("implementation", {})
        if impl.get("yearlyBudget"):
            score += 10
        if impl.get("deploymentYear"):
            score += 5
        if impl.get("budgetCurrency"):
            score += 5
        if impl.get("privateSecFunding") is not None:
            score += 5
        
        # Evaluation (20 points)
        eval_data = policy.get("evaluation", {})
        if eval_data.get("isEvaluated"):
            score += 10
            if eval_data.get("evaluationType"):
                score += 5
            if eval_data.get("riskAssessment"):
                score += 5
        
        # Participation (15 points)
        part = policy.get("participation", {})
        if part.get("hasConsultation"):
            score += 10
            if part.get("consultationStartDate"):
                score += 3
            if part.get("commentsPublic"):
                score += 2
        
        # Alignment (10 points)
        align = policy.get("alignment", {})
        if align.get("aiPrinciples"):
            score += 5
        if align.get("humanRightsAlignment"):
            score += 3
        if align.get("internationalCooperation"):
            score += 2
        
        return min(score, 100)
    
    def _calculate_completeness_score(self, policy: dict) -> str:
        """Calculate policy completeness level"""
        score = self._calculate_policy_score(policy)
        
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "basic"
    
    async def _update_submission_status(self, submission_id: str):
        """Update submission status based on policy statuses"""
        try:
            submission = await self.temp_submissions_collection.find_one({"_id": ObjectId(submission_id)})
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
                    statuses = [p.get("status", "pending") for p in all_policies]
                    
                    if all(s == "approved" for s in statuses):
                        new_status = "approved"
                    elif all(s == "rejected" for s in statuses):
                        new_status = "rejected"
                    elif any(s == "under_review" for s in statuses):
                        new_status = "under_review"
                    elif any(s == "needs_revision" for s in statuses):
                        new_status = "needs_revision"
                    else:
                        new_status = "pending"
            
            await self.temp_submissions_collection.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {
                    "submission_status": new_status, 
                    "updated_at": datetime.utcnow()
                }}
            )
        except Exception as e:
            logger.error(f"Error updating submission status: {e}")
    
    async def _get_master_policy_statistics(self):
        """Get statistics for master policies"""
        try:
            # Count by country
            countries_pipeline = [
                {"$match": {"master_status": "active"}},
                {"$group": {"_id": "$country", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            countries = []
            async for doc in self.master_policies_collection.aggregate(countries_pipeline):
                countries.append({"country": doc["_id"], "count": doc["count"]})
            
            # Count by policy area
            areas_pipeline = [
                {"$match": {"master_status": "active"}},
                {"$group": {"_id": "$policyArea", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            areas = []
            async for doc in self.master_policies_collection.aggregate(areas_pipeline):
                areas.append({"area": doc["_id"], "count": doc["count"]})
            
            # Total count
            total_count = await self.master_policies_collection.count_documents({"master_status": "active"})
            
            return {
                "total_policies": total_count,
                "countries": countries,
                "policy_areas": areas
            }
        
        except Exception as e:
            logger.error(f"Error getting policy statistics: {e}")
            return {
                "total_policies": 0,
                "countries": [],
                "policy_areas": []
            }

# Global policy service instance - will be initialized lazily
policy_service = None

def get_policy_service():
    """Get or create policy service instance"""
    global policy_service
    if policy_service is None:
        policy_service = PolicyService()
    return policy_service
