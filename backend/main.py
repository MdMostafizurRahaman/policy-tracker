from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime
import os
import motor.motor_asyncio
import shutil
import uuid
from bson import ObjectId
from dotenv import load_dotenv
import mimetypes
import io
import json

# Load environment variables
load_dotenv()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(title="AI Policy Database API with Admin Workflow", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","https://policy-tracker1.onrender.com"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.ai_policy_database

# Collections
temp_policies_collection = db.temp_policies  # For pending submissions
master_policies_collection = db.master_policies  # For approved policies
admin_actions_collection = db.admin_actions  # For tracking admin actions
files_collection = db.files  # For file storage

# Pydantic Models
class PolicyFile(BaseModel):
    name: str
    file_id: Optional[str] = None
    size: int
    type: str
    upload_date: Optional[datetime] = None

class Implementation(BaseModel):
    yearlyBudget: str = ""
    budgetCurrency: str = "USD"
    privateSecFunding: bool = False
    deploymentYear: int = Field(default_factory=lambda: datetime.now().year)

class Evaluation(BaseModel):
    isEvaluated: bool = False
    evaluationType: str = "internal"
    riskAssessment: bool = False
    transparencyScore: int = 0
    explainabilityScore: int = 0
    accountabilityScore: int = 0

class Participation(BaseModel):
    hasConsultation: bool = False
    consultationStartDate: str = ""
    consultationEndDate: str = ""
    commentsPublic: bool = False
    stakeholderScore: int = 0

class Alignment(BaseModel):
    aiPrinciples: List[str] = []
    humanRightsAlignment: bool = False
    environmentalConsiderations: bool = False
    internationalCooperation: bool = False

class PolicyInitiative(BaseModel):
    policyName: str
    policyId: str = ""
    policyArea: str = ""
    targetGroups: List[str] = []
    policyDescription: str = ""
    policyFile: Optional[PolicyFile] = None
    policyLink: str = ""
    implementation: Implementation
    evaluation: Evaluation
    participation: Participation
    alignment: Alignment
    status: str = "pending"  # pending, approved, rejected, needs_revision
    admin_notes: str = ""

    @validator('policyName')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Policy name must not be empty')
        return v

class FormSubmission(BaseModel):
    country: str
    policyInitiatives: List[PolicyInitiative]
    submission_status: str = "pending"

    @validator('country')
    def country_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Country name must not be empty')
        return v

class AdminAction(BaseModel):
    action: str  # approve, reject, modify, delete
    policy_id: str
    submission_id: str
    admin_notes: str = ""
    modified_data: Optional[Dict] = None

class PolicyStatusUpdate(BaseModel):
    submission_id: str
    policy_index: int
    status: str
    admin_notes: str = ""

class PolicyUpdate(BaseModel):
    submission_id: str
    policy_index: int
    updated_policy: PolicyInitiative

# Helper function to convert ObjectId to string
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

# Helper function to convert Pydantic models to dict for MongoDB storage
def pydantic_to_dict(obj):
    """Convert Pydantic models and other objects to MongoDB-compatible dict"""
    if hasattr(obj, 'dict'):  # Pydantic model
        return obj.dict()
    elif isinstance(obj, dict):
        return {key: pydantic_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [pydantic_to_dict(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj
    else:
        return obj

# Helper function to save file to database
async def save_file_to_db(file: UploadFile, metadata: Dict = None) -> str:
    """Save file to database and return file ID"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Reset file pointer for potential reuse
        await file.seek(0)
        
        # Prepare file document
        file_doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_data": file_content,
            "size": len(file_content),
            "upload_date": datetime.utcnow(),
            **(metadata or {})
        }
        
        # Save to database
        result = await files_collection.insert_one(file_doc)
        return str(result.inserted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

# Helper function to get file from database
async def get_file_from_db(file_id: str):
    """Retrieve file from database"""
    try:
        file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        return file_doc
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI Policy Database API with Admin Workflow is running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    try:
        # Test database connection
        await db.command("ping")
        return {"status": "healthy", "database": "connected", "timestamp": datetime.utcnow()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.post("/api/upload-policy-file")
async def upload_policy_file(
    country: str = Form(...),
    policy_index: int = Form(...),
    submission_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload individual policy file"""
    try:
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
        
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail="File type not supported. Please upload PDF, DOC, DOCX, or TXT files.")
        
        # Prepare metadata
        metadata = {
            "country": country,
            "policy_index": policy_index,
            "submission_id": submission_id,
            "original_filename": file.filename
        }
        
        # Save file to database
        file_id = await save_file_to_db(file, metadata)
        
        return {
            "success": True, 
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size or 0,
            "content_type": file.content_type,
            "message": "File uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/api/submit-form")
async def submit_form(submission: FormSubmission):
    """Submit form data to temporary database for admin review"""
    try:
        # Filter out empty policies
        non_empty_policies = [
            policy for policy in submission.policyInitiatives 
            if policy.policyName and policy.policyName.strip()
        ]
        
        if not non_empty_policies:
            raise HTTPException(status_code=400, detail="At least one policy must be provided")
        
        # Convert Pydantic models to dict for MongoDB storage
        submission_dict = pydantic_to_dict(submission)
        submission_dict["policyInitiatives"] = [pydantic_to_dict(policy) for policy in non_empty_policies]
        submission_dict["created_at"] = datetime.utcnow()
        submission_dict["updated_at"] = datetime.utcnow()
        submission_dict["submission_status"] = "pending"
        
        # Insert into temporary collection
        result = await temp_policies_collection.insert_one(submission_dict)
        
        if result.inserted_id:
            return {
                "success": True, 
                "message": "Form submitted successfully and is pending admin review", 
                "submission_id": str(result.inserted_id),
                "policies_count": len(non_empty_policies)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert data into database")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Form submission failed: {str(e)}")

@app.get("/api/admin/pending-submissions")
async def get_pending_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Get all pending submissions for admin review"""
    try:
        skip = (page - 1) * limit
        
        # Get pending submissions
        cursor = temp_policies_collection.find(
            {"submission_status": {"$in": ["pending", "partially_approved"]}}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        submissions = []
        async for doc in cursor:
            doc = convert_objectid(doc)
            submissions.append(doc)
        
        # Get total count
        total_count = await temp_policies_collection.count_documents(
            {"submission_status": {"$in": ["pending", "partially_approved"]}}
        )
        
        return {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching submissions: {str(e)}")

@app.get("/api/admin/submissions")
async def get_all_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    """Get all submissions with optional status filter"""
    try:
        skip = (page - 1) * limit
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["submission_status"] = status
        
        # Get submissions
        cursor = temp_policies_collection.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit)
        
        submissions = []
        async for doc in cursor:
            doc = convert_objectid(doc)
            submissions.append(doc)
        
        # Get total count
        total_count = await temp_policies_collection.count_documents(filter_dict)
        
        return {
            "submissions": submissions,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching submissions: {str(e)}")

@app.get("/api/admin/submission/{submission_id}")
async def get_submission_details(submission_id: str):
    """Get detailed view of a specific submission"""
    try:
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        submission = convert_objectid(submission)
        return submission
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching submission: {str(e)}")

@app.put("/api/admin/update-policy-status")
async def update_policy_status(status_update: PolicyStatusUpdate):
    """Update the status of a specific policy"""
    try:
        submission_id = status_update.submission_id
        policy_index = status_update.policy_index
        new_status = status_update.status
        admin_notes = status_update.admin_notes
        
        # Find the submission
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Validate policy index
        if policy_index >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=404, detail="Policy not found in submission")
        
        # Update policy status
        update_dict = {
            f"policyInitiatives.{policy_index}.status": new_status,
            f"policyInitiatives.{policy_index}.admin_notes": admin_notes,
            "updated_at": datetime.utcnow()
        }
        
        await temp_policies_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": update_dict}
        )
        
        # Log admin action
        admin_log = {
            "action": f"status_update_{new_status}",
            "submission_id": submission_id,
            "policy_index": policy_index,
            "admin_notes": admin_notes,
            "timestamp": datetime.utcnow()
        }
        await admin_actions_collection.insert_one(admin_log)
        
        # Update overall submission status
        await update_submission_status(submission_id)
        
        return {"success": True, "message": f"Policy status updated to {new_status}"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")

@app.post("/api/admin/move-to-master")
async def move_policy_to_master(move_request: dict):
    """Move approved policy to master database"""
    try:
        submission_id = move_request["submission_id"]
        policy_index = move_request["policy_index"]
        
        # Find the submission
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Get the policy
        if policy_index >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=404, detail="Policy not found")
        
        policy = submission["policyInitiatives"][policy_index]
        
        # Only move if approved
        if policy.get("status") != "approved":
            raise HTTPException(status_code=400, detail="Only approved policies can be moved to master database")
        
        # Prepare policy for master DB
        master_policy = {
            **policy,
            "country": submission["country"],
            "original_submission_id": submission_id,
            "moved_to_master_at": datetime.utcnow(),
            "master_status": "active"
        }
        
        # Insert into master collection
        result = await master_policies_collection.insert_one(master_policy)
        
        if result.inserted_id:
            # Log the action
            admin_log = {
                "action": "moved_to_master",
                "submission_id": submission_id,
                "policy_index": policy_index,
                "master_policy_id": str(result.inserted_id),
                "timestamp": datetime.utcnow()
            }
            await admin_actions_collection.insert_one(admin_log)
            
            return {"success": True, "message": "Policy moved to master database", "master_id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Failed to move policy to master database")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move to master failed: {str(e)}")

@app.put("/api/admin/edit-policy")
async def edit_policy(policy_update: PolicyUpdate):
    """Edit a policy in the temporary database"""
    try:
        submission_id = policy_update.submission_id
        policy_index = policy_update.policy_index
        updated_policy = pydantic_to_dict(policy_update.updated_policy)
        
        # Find the submission
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Validate policy index
        if policy_index >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=404, detail="Policy not found in submission")
        
        # Update the policy
        update_dict = {}
        for key, value in updated_policy.items():
            update_dict[f"policyInitiatives.{policy_index}.{key}"] = value
        
        update_dict["updated_at"] = datetime.utcnow()
        
        await temp_policies_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": update_dict}
        )
        
        # Log admin action
        admin_log = {
            "action": "policy_edited",
            "submission_id": submission_id,
            "policy_index": policy_index,
            "updated_fields": list(updated_policy.keys()),
            "timestamp": datetime.utcnow()
        }
        await admin_actions_collection.insert_one(admin_log)
        
        return {"success": True, "message": "Policy updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy edit failed: {str(e)}")

@app.delete("/api/admin/delete-policy")
async def delete_policy(delete_request: dict):
    """Delete a policy from a submission"""
    try:
        submission_id = delete_request["submission_id"]
        policy_index = delete_request["policy_index"]
        
        # Find the submission
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Validate policy index
        if policy_index >= len(submission["policyInitiatives"]):
            raise HTTPException(status_code=404, detail="Policy not found in submission")
        
        # Remove the policy
        policies = submission["policyInitiatives"]
        deleted_policy = policies.pop(policy_index)
        
        # Update the submission
        await temp_policies_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {
                "policyInitiatives": policies,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Delete associated file if exists
        if deleted_policy.get("policyFile") and deleted_policy["policyFile"].get("file_id"):
            await files_collection.delete_one({"_id": ObjectId(deleted_policy["policyFile"]["file_id"])})
        
        # Log admin action
        admin_log = {
            "action": "policy_deleted",
            "submission_id": submission_id,
            "policy_index": policy_index,
            "deleted_policy_name": deleted_policy.get("policyName", "Unknown"),
            "timestamp": datetime.utcnow()
        }
        await admin_actions_collection.insert_one(admin_log)
        
        # Update submission status
        await update_submission_status(submission_id)
        
        return {"success": True, "message": "Policy deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy deletion failed: {str(e)}")

async def update_submission_status(submission_id: str):
    """Update the overall status of a submission based on policy statuses"""
    try:
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            return
        
        if not submission.get("policyInitiatives"):
            new_status = "empty"
        else:
            policy_statuses = [p.get("status", "pending") for p in submission["policyInitiatives"]]
            
            if all(status == "approved" for status in policy_statuses):
                new_status = "fully_approved"
            elif all(status in ["approved", "rejected"] for status in policy_statuses):
                new_status = "fully_processed"
            elif any(status == "approved" for status in policy_statuses):
                new_status = "partially_approved"
            else:
                new_status = "pending"
        
        await temp_policies_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {"submission_status": new_status, "updated_at": datetime.utcnow()}}
        )
    except Exception as e:
        print(f"Error updating submission status: {e}")

@app.get("/api/admin/master-policies")
async def get_master_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    country: Optional[str] = Query(None),
    policy_area: Optional[str] = Query(None)
):
    """Get approved policies from master database"""
    try:
        skip = (page - 1) * limit
        
        # Build filter
        filter_dict = {"master_status": {"$ne": "deleted"}}
        if country:
            filter_dict["country"] = {"$regex": country, "$options": "i"}
        if policy_area:
            filter_dict["policyArea"] = policy_area
        
        # Get policies
        cursor = master_policies_collection.find(filter_dict).sort("moved_to_master_at", -1).skip(skip).limit(limit)
        
        policies = []
        async for doc in cursor:
            doc = convert_objectid(doc)
            policies.append(doc)
        
        # Get total count
        total_count = await master_policies_collection.count_documents(filter_dict)
        
        return {
            "policies": policies,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching master policies: {str(e)}")

@app.get("/api/file/{file_id}")
async def download_file(file_id: str):
    """Download file from database"""
    try:
        file_doc = await get_file_from_db(file_id)
        
        # Determine content type
        content_type = file_doc.get("content_type") or mimetypes.guess_type(file_doc["filename"])[0] or "application/octet-stream"
        
        # Create file stream
        file_data = file_doc["file_data"]
        
        def iterfile():
            yield file_data
        
        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={file_doc['filename']}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

@app.get("/api/admin/statistics")
async def get_admin_statistics():
    """Get statistics for admin dashboard"""
    try:
        stats = {
            "pending_submissions": await temp_policies_collection.count_documents({"submission_status": "pending"}),
            "partially_approved": await temp_policies_collection.count_documents({"submission_status": "partially_approved"}),
            "fully_approved": await temp_policies_collection.count_documents({"submission_status": "fully_approved"}),
            "total_approved_policies": await master_policies_collection.count_documents({"master_status": {"$ne": "deleted"}}),
            "total_temp_policies": await temp_policies_collection.count_documents({}),
            "recent_actions": []
        }
        
        # Get recent admin actions
        cursor = admin_actions_collection.find().sort("timestamp", -1).limit(10)
        async for action in cursor:
            action = convert_objectid(action)
            stats["recent_actions"].append(action)
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@app.delete("/api/admin/master-policy/{policy_id}")
async def delete_master_policy(policy_id: str):
    """Delete a policy from master database"""
    try:
        result = await master_policies_collection.update_one(
            {"_id": ObjectId(policy_id)},
            {"$set": {"master_status": "deleted", "deleted_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 1:
            # Log admin action
            admin_log = {
                "action": "master_policy_deleted",
                "master_policy_id": policy_id,
                "timestamp": datetime.utcnow()
            }
            await admin_actions_collection.insert_one(admin_log)
            
            return {"success": True, "message": "Policy deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Policy not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting policy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    