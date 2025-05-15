from fastapi import APIRouter, Body, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from models import CountrySubmission, Policy, PaginationInfo, SubmissionsResponse
from database import pending_collection, approved_collection
import os
import json
from datetime import datetime
from bson import ObjectId
import pymongo

router = APIRouter(
    prefix="/api",
    tags=["pending-submissions"]
)

# Custom JSON encoder to handle ObjectId and datetime
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Route to submit a new policy
@router.post("/submit-policy")
async def submit_policy(submission: CountrySubmission = Body(...)):
    # Prepare the document for insertion
    current_time = datetime.utcnow()
    
    # Add timestamps
    submission_dict = submission.dict()
    submission_dict["createdAt"] = current_time
    submission_dict["updatedAt"] = current_time
    
    # Process each policy to add timestamps and status
    for policy in submission_dict["policyInitiatives"]:
        policy["createdAt"] = current_time
        policy["updatedAt"] = current_time
        policy["status"] = "pending"
        
        # Generate a policy ID if not provided
        if not policy.get("policyId"):
            policy["policyId"] = f"{submission_dict['country']}-{ObjectId()}"
    
    try:
        # Check if a submission already exists for this country
        existing = pending_collection.find_one({"country": submission_dict["country"]})
        
        if existing:
            # Update existing document
            result = pending_collection.update_one(
                {"country": submission_dict["country"]},
                {"$set": {
                    "policyInitiatives": submission_dict["policyInitiatives"],
                    "updatedAt": current_time
                }}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Update failed")
            
            return JSONResponse(
                content={"success": True, "message": "Policy submission updated successfully"},
                status_code=200
            )
        else:
            # Insert new document
            result = pending_collection.insert_one(submission_dict)
            
            if not result.inserted_id:
                raise HTTPException(status_code=400, detail="Submission failed")
            
            return JSONResponse(
                content={"success": True, "message": "Policy submission successful", "id": str(result.inserted_id)},
                status_code=201
            )
            
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A submission for this country already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Route to upload policy file
@router.post("/upload-policy-file")
async def upload_policy_file(
    background_tasks: BackgroundTasks,
    country: str = Form(...),
    policyIndex: int = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Create directory if it doesn't exist
        os.makedirs("temp_policies", exist_ok=True)
        
        # Generate a unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"{country.replace(' ', '_')}_{policyIndex}_{timestamp}_{file.filename}"
        file_path = os.path.join("temp_policies", filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update the policy record with the file path
        result = pending_collection.update_one(
            {"country": country},
            {"$set": {
                f"policyInitiatives.{policyIndex}.policyFile": filename,
                f"policyInitiatives.{policyIndex}.updatedAt": datetime.utcnow()
            }}
        )
        
        if result.modified_count == 0:
            # Delete the file if update failed
            background_tasks.add_task(os.remove, file_path)
            raise HTTPException(status_code=404, detail="Country or policy not found")
        
        return JSONResponse(
            content={"success": True, "filename": filename},
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# Get pending submissions with pagination
@router.get("/pending-submissions", response_model=SubmissionsResponse)
async def get_pending_submissions(
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
    total_count = pending_collection.count_documents(query_filter)
    
    # Get submissions for current page
    cursor = pending_collection.find(query_filter).skip(skip).limit(limit).sort("updatedAt", -1)
    
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

# Get single country submission
@router.get("/pending-submission/{country}")
async def get_pending_submission(country: str):
    submission = pending_collection.find_one({"country": country})
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Convert ObjectId to string
    submission["_id"] = str(submission["_id"])
    
    return submission