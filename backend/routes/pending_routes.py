from fastapi import APIRouter, Form, HTTPException, UploadFile, Body, File, Query
from fastapi.responses import FileResponse
import os
import shutil
from typing import Optional, List
from database import pending_collection, approved_collection
from models import POLICY_TYPES
from utils import generate_policy_data_csv

router = APIRouter(prefix="/api", tags=["pending_submissions"])

@router.post("/submit-policy")
async def submit_policy(
    country: str = Form(...),
    policy_1_file: Optional[UploadFile] = File(None), policy_1_text: Optional[str] = Form(None),
    policy_2_file: Optional[UploadFile] = File(None), policy_2_text: Optional[str] = Form(None),
    policy_3_file: Optional[UploadFile] = File(None), policy_3_text: Optional[str] = Form(None),
    policy_4_file: Optional[UploadFile] = File(None), policy_4_text: Optional[str] = Form(None),
    policy_5_file: Optional[UploadFile] = File(None), policy_5_text: Optional[str] = Form(None),
    policy_6_file: Optional[UploadFile] = File(None), policy_6_text: Optional[str] = Form(None),
    policy_7_file: Optional[UploadFile] = File(None), policy_7_text: Optional[str] = Form(None),
    policy_8_file: Optional[UploadFile] = File(None), policy_8_text: Optional[str] = Form(None),
    policy_9_file: Optional[UploadFile] = File(None), policy_9_text: Optional[str] = Form(None),
    policy_10_file: Optional[UploadFile] = File(None), policy_10_text: Optional[str] = Form(None),
):
    """Submit policy data for a country with up to 10 policies"""
    # Save uploaded files or text inputs
    policies = []
    
    file_text_pairs = [
        (policy_1_file, policy_1_text), (policy_2_file, policy_2_text),
        (policy_3_file, policy_3_text), (policy_4_file, policy_4_text),
        (policy_5_file, policy_5_text), (policy_6_file, policy_6_text),
        (policy_7_file, policy_7_text), (policy_8_file, policy_8_text),
        (policy_9_file, policy_9_text), (policy_10_file, policy_10_text),
    ]
    
    for i, (file, text) in enumerate(file_text_pairs):
        policy_data = {
            "file": None, 
            "text": None, 
            "status": "pending",
            "type": POLICY_TYPES[i] if i < len(POLICY_TYPES) else f"Policy {i+1}",
            "year": "N/A",
            "description": "",
            "metrics": []
        }
        
        if file and file.filename:
            # Create a sanitized filename to prevent directory traversal
            safe_filename = f"{country}_policy_{i + 1}_{os.path.basename(file.filename)}"
            file_path = f"temp_policies/{safe_filename}"
            
            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            policy_data["file"] = file_path
        
        if text:
            policy_data["text"] = text
        
        policies.append(policy_data)

    # Check if this country already exists in pending collection
    existing_submission = pending_collection.find_one({"country": country})
    if existing_submission:
        # Update existing submission
        pending_collection.update_one(
            {"country": country},
            {"$set": {"policies": policies}}
        )
    else:
        # Store new submission in MongoDB
        pending_submission = {"country": country, "policies": policies}
        pending_collection.insert_one(pending_submission)
    
    return {"message": "Submission received and pending approval"}


@router.get("/pending-submissions")
def get_pending_submissions(page: int = Query(0), per_page: int = Query(5)):
    """Get a paginated list of pending policy submissions"""
    # Calculate skip amount
    skip = page * per_page
    
    # Count total documents for pagination info
    total_docs = pending_collection.count_documents({})
    total_pages = (total_docs + per_page - 1) // per_page  # Ceiling division
    
    # Fetch pending submissions from MongoDB with pagination
    cursor = pending_collection.find({}, {"_id": 0}).skip(skip).limit(per_page)
    submissions = list(cursor)
    
    return {
        "submissions": submissions,
        "pagination": {
            "current_page": page,
            "total_pages": max(1, total_pages),  # Ensure at least 1 page even if no results
            "total_count": total_docs,
            "per_page": per_page
        }
    }


@router.post("/approve-policy")
def approve_policy(payload: dict = Body(...)):
    """Approve a specific policy from a country's submission"""
    country = payload.get("country")
    policy_index = payload.get("policyIndex")
    
    if country is None or policy_index is None:
        raise HTTPException(status_code=400, detail="Country and policyIndex are required")
    
    # Convert policy_index to integer if it's not already
    policy_index = int(policy_index)
    
    # Find the pending submission
    submission = pending_collection.find_one({"country": country})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check if policy index is valid
    if policy_index < 0 or policy_index >= len(submission["policies"]):
        raise HTTPException(status_code=400, detail="Invalid policy index")
    
    # Get the specific policy
    policy = submission["policies"][policy_index]
    
    # Check if there's anything to approve
    if not policy["file"] and not policy["text"]:
        raise HTTPException(status_code=400, detail="No policy content to approve")
    
    # Move file to approved directory if present
    if policy["file"]:
        temp_path = policy["file"]
        filename = os.path.basename(temp_path)
        
        # Create approved_policies directory if it doesn't exist
        os.makedirs("approved_policies", exist_ok=True)
        
        approved_path = f"approved_policies/{filename}"
        
        if os.path.exists(temp_path):
            # Copy instead of move, so we keep the original
            try:
                shutil.copy(temp_path, approved_path)
                policy["file"] = approved_path
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error copying file: {str(e)}")
    
    # Mark this policy as approved
    policy["status"] = "approved"
    
    # Update the policy in the submission
    submission["policies"][policy_index] = policy
    
    # Update in MongoDB
    try:
        pending_collection.update_one(
            {"country": country},
            {"$set": {"policies": submission["policies"]}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB update error: {str(e)}")
    
    # Check if we need to create or update in approved collection
    existing_approved = approved_collection.find_one({"country": country})
    
    if existing_approved:
        # If country exists in approved, update that specific policy
        existing_approved["policies"][policy_index] = policy
        approved_collection.update_one(
            {"country": country},
            {"$set": {"policies": existing_approved["policies"]}}
        )
    else:
        # Otherwise, create a new entry with just this policy approved
        new_approved = {
            "country": country,
            "policies": [{"file": None, "text": None, "status": "pending", "type": t, "year": "N/A", "description": "", "metrics": []} 
                        for i, t in enumerate(POLICY_TYPES)]
        }
        new_approved["policies"][policy_index] = policy
        approved_collection.insert_one(new_approved)
    
    # Update the CSV file
    generate_policy_data_csv()
    
    return {"message": f"Policy {policy_index} for {country} approved"}


@router.post("/decline-policy")
def decline_policy(payload: dict = Body(...)):
    """Decline a specific policy from a country's submission"""
    country = payload.get("country")
    policy_index = payload.get("policyIndex")
    
    if country is None or policy_index is None:
        raise HTTPException(status_code=400, detail="Country and policyIndex are required")
    
    # Convert policy_index to integer if it's not already
    policy_index = int(policy_index)
    
    # Find the pending submission
    submission = pending_collection.find_one({"country": country})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check if policy index is valid
    if policy_index < 0 or policy_index >= len(submission["policies"]):
        raise HTTPException(status_code=400, detail="Invalid policy index")
    
    # Get the specific policy
    policy = submission["policies"][policy_index]
    
    # Delete file if present
    if policy["file"] and os.path.exists(policy["file"]):
        os.remove(policy["file"])
    
    # Reset this policy
    policy = {
        "file": None, 
        "text": None, 
        "status": "declined",
        "type": POLICY_TYPES[policy_index] if policy_index < len(POLICY_TYPES) else f"Policy {policy_index+1}",
        "year": "N/A",
        "description": "",
        "metrics": []
    }
    submission["policies"][policy_index] = policy
    
    # Update in MongoDB
    pending_collection.update_one(
        {"country": country},
        {"$set": {"policies": submission["policies"]}}
    )
    
    return {"message": f"Policy {policy_index} for {country} declined"}


@router.post("/approve-submission")
def approve_submission(payload: dict = Body(...)):
    """Approve an entire country submission, moving all policies to approved status"""
    country = payload.get("country")
    if not country:
        raise HTTPException(status_code=400, detail="Country is required")

    # Find the pending submission
    submission = pending_collection.find_one({"country": country})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Move files from temp to approved directory if needed
    policies = submission["policies"]
    for i, policy in enumerate(policies):
        if policy["file"]:
            temp_path = policy["file"]
            # Extract filename from path
            filename = os.path.basename(temp_path)
            approved_path = f"approved_policies/{filename}"
            
            # Move the file
            if os.path.exists(temp_path):
                shutil.move(temp_path, approved_path)
                policies[i]["file"] = approved_path
                
        # Mark this policy as approved if it has content
        if policy["file"] or policy["text"]:
            policies[i]["status"] = "approved"
    
    # Update the submission with new file paths
    submission["policies"] = policies
    
    # Move submission to approved collection
    approved_collection.insert_one(submission)
    pending_collection.delete_one({"country": country})

    # Update the CSV file
    generate_policy_data_csv()
    return {"message": f"Submission for {country} approved and added to the database"}


@router.post("/remove-country")
def remove_country(payload: dict = Body(...)):
    """Remove a country from the pending submissions list"""
    country = payload.get("country")
    
    if country is None:
        raise HTTPException(status_code=400, detail="Country is required")
    
    # Find and delete the country from pending collection
    result = pending_collection.delete_one({"country": country})
    
    if result.deleted_count == 0:
        # Country not found in pending collection
        raise HTTPException(status_code=404, detail="Country not found in pending submissions")
    
    return {"message": f"Country {country} removed from pending submissions"}


@router.get("/rejected-submissions")
def get_rejected_submissions(page: int = Query(0), per_page: int = Query(5)):
    """Get a paginated list of rejected policy submissions"""
    # Calculate skip amount
    skip = page * per_page
    
    # Query for submissions with at least one declined policy
    query = {"policies": {"$elemMatch": {"status": "declined"}}}
    
    # Count total documents for pagination info
    total_docs = pending_collection.count_documents(query)
    total_pages = (total_docs + per_page - 1) // per_page  # Ceiling division
    
    # Fetch rejected submissions from MongoDB with pagination
    cursor = pending_collection.find(query, {"_id": 0}).skip(skip).limit(per_page)
    submissions = list(cursor)
    
    return {
        "submissions": submissions,
        "pagination": {
            "current_page": page,
            "total_pages": max(1, total_pages),
            "total_count": total_docs,
            "per_page": per_page
        }
    }