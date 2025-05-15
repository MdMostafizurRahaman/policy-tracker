from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import List
from models import SubmissionRemovalRequest
from database import pending_collection, approved_collection
import os
import shutil
from pathlib import Path

router = APIRouter(
    prefix="/api",
    tags=["utilities"]
)

# Function to ensure required directories exist
def ensure_directories():
    os.makedirs("temp_policies", exist_ok=True)
    os.makedirs("approved_policies", exist_ok=True)

# Route to get policy file
@router.get("/policy-file/{filename}")
async def get_policy_file(filename: str):
    # Check temp policies directory first
    temp_path = os.path.join("temp_policies", filename)
    if os.path.exists(temp_path):
        return FileResponse(temp_path)
    
    # Check approved policies directory
    approved_path = os.path.join("approved_policies", filename)
    if os.path.exists(approved_path):
        return FileResponse(approved_path)
    
    # File not found
    raise HTTPException(status_code=404, detail="Policy file not found")

# Route to remove a submission
@router.post("/remove-submission")
async def remove_submission(request: SubmissionRemovalRequest, background_tasks: BackgroundTasks):
    try:
        # Find the submission
        submission = pending_collection.find_one({"country": request.country})
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Get policy file paths to remove
        file_paths = []
        for policy in submission.get("policyInitiatives", []):
            if policy.get("policyFile"):
                file_path = os.path.join("temp_policies", policy["policyFile"])
                if os.path.exists(file_path):
                    file_paths.append(file_path)
        
        # Remove the submission
        result = pending_collection.delete_one({"country": request.country})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="Submission removal failed")
        
        # Remove policy files in background
        for file_path in file_paths:
            background_tasks.add_task(os.remove, file_path)
        
        return JSONResponse(
            content={"success": True, "message": "Submission removed successfully"},
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Route to get statistics
@router.get("/statistics")
async def get_statistics():
    try:
        # Get total submissions
        pending_count = pending_collection.count_documents({})
        approved_count = approved_collection.count_documents({})
        
        # Get policy statistics
        pending_policies = 0
        approved_policies = 0
        declined_policies = 0
        
        # Count policies by status in pending submissions
        cursor = pending_collection.find({}, {"policyInitiatives": 1})
        for doc in cursor:
            for policy in doc.get("policyInitiatives", []):
                if policy.get("status") == "pending":
                    pending_policies += 1
                elif policy.get("status") == "approved":
                    approved_policies += 1
                elif policy.get("status") == "declined":
                    declined_policies += 1
        
        # Count policies in approved submissions
        cursor = approved_collection.find({}, {"policyInitiatives": 1})
        for doc in cursor:
            approved_policies += len(doc.get("policyInitiatives", []))
        
        # Get policy area distribution
        policy_areas = {}
        cursor = pending_collection.find({}, {"policyInitiatives": 1})
        for doc in cursor:
            for policy in doc.get("policyInitiatives", []):
                area = policy.get("policyArea")
                if area:
                    policy_areas[area] = policy_areas.get(area, 0) + 1
        
        cursor = approved_collection.find({}, {"policyInitiatives": 1})
        for doc in cursor:
            for policy in doc.get("policyInitiatives", []):
                area = policy.get("policyArea")
                if area:
                    policy_areas[area] = policy_areas.get(area, 0) + 1
        
        return {
            "total_countries": pending_count + approved_count,
            "pending_submissions": pending_count,
            "approved_submissions": approved_count,
            "policy_stats": {
                "pending": pending_policies,
                "approved": approved_policies,
                "declined": declined_policies,
                "total": pending_policies + approved_policies + declined_policies
            },
            "policy_areas": policy_areas
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")