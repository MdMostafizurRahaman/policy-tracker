from fastapi import APIRouter, Body, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from models import CountrySubmission, PolicyApprovalRequest, PolicyDeclineRequest, SubmissionRemovalRequest
from database import pending_collection, approved_collection
import os
import json
from datetime import datetime
from bson import ObjectId

router = APIRouter(
    prefix="/api",
    tags=["approved-policies"]
)

# Route to approve a policy
@router.post("/approve-policy")
async def approve_policy(request: PolicyApprovalRequest = Body(...)):
    try:
        # Find the pending submission
        submission = pending_collection.find_one({"country": request.country})
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Check if policy index is valid
        if request.policyIndex < 0 or request.policyIndex >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=400, detail="Invalid policy index")
        
        # Update policy status to approved
        current_time = datetime.utcnow()
        policy = submission["policyInitiatives"][request.policyIndex]
        policy["status"] = "approved"
        policy["updatedAt"] = current_time
        
        # Update policy text if provided
        if request.text:
            policy["policyDescription"] = request.text
        
        # Update pending collection
        result = pending_collection.update_one(
            {"country": request.country},
            {"$set": {
                f"policyInitiatives.{request.policyIndex}": policy,
                "updatedAt": current_time
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Policy approval failed")
        
        # Check if approved collection already has this country
        existing = approved_collection.find_one({"country": request.country})
        
        if existing:
            # Update existing approved policies
            approved_collection.update_one(
                {"country": request.country},
                {"$push": {"policyInitiatives": policy}, "$set": {"updatedAt": current_time}}
            )
        else:
            # Create new approved document
            approved_collection.insert_one({
                "country": request.country,
                "policyInitiatives": [policy],
                "createdAt": current_time,
                "updatedAt": current_time
            })
        
        return JSONResponse(
            content={"success": True, "message": "Policy approved successfully"},
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Route to decline a policy
@router.post("/decline-policy")
async def decline_policy(request: PolicyDeclineRequest = Body(...)):
    try:
        # Find the pending submission
        submission = pending_collection.find_one({"country": request.country})
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Check if policy index is valid
        if request.policyIndex < 0 or request.policyIndex >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=400, detail="Invalid policy index")
        
        # Update policy status to declined
        current_time = datetime.utcnow()
        policy = submission["policyInitiatives"][request.policyIndex]
        policy["status"] = "declined"
        policy["updatedAt"] = current_time
        
        # Update pending collection
        result = pending_collection.update_one(
            {"country": request.country},
            {"$set": {
                f"policyInitiatives.{request.policyIndex}": policy,
                "updatedAt": current_time
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Policy decline failed")
        
        return JSONResponse(
            content={"success": True, "message": "Policy declined successfully"},
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get approved submissions with pagination
@router.get("/approved-policies")
async def get_approved_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    # Calculate skip value for pagination
    skip = (page - 1) * limit
    
    # Build query filter
    query_filter = {}
    if search:
        # Case-insensitive search for country or policy names
        query_filter["$or"] = [
            {"country": {"$regex": search, "$options": "i"}},
            {"policyInitiatives.policyName": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count for pagination
    total_count = approved_collection.count_documents(query_filter)
    
    # Get submissions for current page
    cursor = approved_collection.find(query_filter).skip(skip).limit(limit).sort("updatedAt", -1)
    
    # Convert to list and handle MongoDB-specific types
    submissions = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        submissions.append(doc)
    
    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit
    
    # Return paginated response
    return {
        "submissions": submissions,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "per_page": limit
        }
    }

# Get single approved country submission
@router.get("/approved-policy/{country}")
async def get_approved_policy(country: str):
    submission = approved_collection.find_one({"country": country})
    
    if not submission:
        raise HTTPException(status_code=404, detail="Approved policy not found")
    
    # Convert ObjectId to string
    submission["_id"] = str(submission["_id"])
    
    return submission