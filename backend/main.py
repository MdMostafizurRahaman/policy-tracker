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

# Load environment variables
load_dotenv()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(title="AI Policy Database API with Admin Workflow")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGO_URI")
if not MONGODB_URL:
    raise ValueError("MONGO_URI environment variable is not set")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.ai_policy_database

# Collections
temp_policies_collection = db.temp_policies  # For pending submissions
master_policies_collection = db.master_policies  # For approved policies
admin_actions_collection = db.admin_actions  # For tracking admin actions
files_collection = db.files  # For file storage (replacing GridFS)

# Pydantic Models
class PolicyFile(BaseModel):
    name: str
    file_id: Optional[str] = None  # File document ID
    size: int
    type: str
    upload_date: Optional[datetime] = None

class Implementation(BaseModel):
    yearlyBudget: str = ""
    budgetCurrency: str = "USD"
    privateSecFunding: bool = False
    deploymentYear: int = Field(...)

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
    status: str = "pending"  # pending, approved, rejected
    admin_notes: str = ""

    @validator('policyName')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Policy name must not be empty')
        return v

class FormSubmission(BaseModel):
    country: str
    policyInitiatives: List[PolicyInitiative]
    submission_status: str = "pending"  # pending, partially_approved, fully_approved, rejected

    @validator('country')
    def country_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Country name must not be empty')
        return v

class AdminAction(BaseModel):
    action: str  # approve, reject, modify, delete
    policy_id: str
    submission_id: str
    admin_notes: str = ""
    modified_data: Optional[Dict] = None

# Helper function to save file to database
async def save_file_to_db(file: UploadFile, metadata: Dict = None) -> str:
    """Save file to database and return file ID"""
    try:
        # Read file content
        file_content = await file.read()
        
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

@app.post("/api/upload-policy-file")
async def upload_policy_file(
    country: str = Form(...),
    policy_index: int = Form(...),
    submission_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload individual policy file"""
    try:
        # Prepare metadata
        metadata = {
            "country": country,
            "policy_index": policy_index,
            "submission_id": submission_id
        }
        
        # Save file to database
        file_id = await save_file_to_db(file, metadata)
        
        return {
            "success": True, 
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/api/submit-form")
async def submit_form(submission: FormSubmission):
    """Submit form data to temporary database for admin review"""
    try:
        # Add timestamps and initial status
        submission_dict = submission.dict()
        submission_dict["created_at"] = datetime.utcnow()
        submission_dict["updated_at"] = datetime.utcnow()
        submission_dict["submission_status"] = "pending"
        
        # Insert into temporary collection
        result = await temp_policies_collection.insert_one(submission_dict)
        
        if result.inserted_id:
            return {
                "success": True, 
                "message": "Form submitted successfully and is pending admin review", 
                "submission_id": str(result.inserted_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert data into database")
    
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
            doc["_id"] = str(doc["_id"])
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

@app.get("/api/admin/submission/{submission_id}")
async def get_submission_details(submission_id: str):
    """Get detailed view of a specific submission"""
    try:
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        submission["_id"] = str(submission["_id"])
        return submission
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching submission: {str(e)}")

@app.post("/api/admin/action")
async def admin_action(action_data: AdminAction):
    """Perform admin action on a policy"""
    try:
        submission_id = action_data.submission_id
        policy_index = None
        
        # Find the submission
        submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Find policy index by policy_id or name
        for i, policy in enumerate(submission["policyInitiatives"]):
            if str(i) == action_data.policy_id or policy.get("policyName") == action_data.policy_id:
                policy_index = i
                break
        
        if policy_index is None:
            raise HTTPException(status_code=404, detail="Policy not found in submission")
        
        # Perform the action
        if action_data.action == "approve":
            # Move policy to master database
            policy_data = submission["policyInitiatives"][policy_index].copy()
            policy_data["status"] = "approved"
            policy_data["admin_notes"] = action_data.admin_notes
            policy_data["approved_at"] = datetime.utcnow()
            policy_data["country"] = submission["country"]
            policy_data["original_submission_id"] = submission_id
            
            await master_policies_collection.insert_one(policy_data)
            
            # Update policy status in temp collection
            await temp_policies_collection.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {f"policyInitiatives.{policy_index}.status": "approved"}}
            )
            
        elif action_data.action == "reject":
            # Mark policy as rejected
            await temp_policies_collection.update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {
                    f"policyInitiatives.{policy_index}.status": "rejected",
                    f"policyInitiatives.{policy_index}.admin_notes": action_data.admin_notes
                }}
            )
            
        elif action_data.action == "modify":
            # Apply modifications
            if action_data.modified_data:
                update_dict = {}
                for key, value in action_data.modified_data.items():
                    update_dict[f"policyInitiatives.{policy_index}.{key}"] = value
                
                update_dict[f"policyInitiatives.{policy_index}.admin_notes"] = action_data.admin_notes
                update_dict[f"policyInitiatives.{policy_index}.status"] = "modified"
                
                await temp_policies_collection.update_one(
                    {"_id": ObjectId(submission_id)},
                    {"$set": update_dict}
                )
            
        elif action_data.action == "delete":
            # Remove policy from submission
            await temp_policies_collection.update_one(
                {"_id": ObjectId(submission_id)},
                {"$unset": {f"policyInitiatives.{policy_index}": 1}}
            )
            
            # Clean up the array
            await temp_policies_collection.update_one(
                {"_id": ObjectId(submission_id)},
                {"$pull": {"policyInitiatives": None}}
            )
        
        # Log admin action
        admin_log = {
            "action": action_data.action,
            "submission_id": submission_id,
            "policy_id": action_data.policy_id,
            "admin_notes": action_data.admin_notes,
            "timestamp": datetime.utcnow(),
            "modified_data": action_data.modified_data
        }
        await admin_actions_collection.insert_one(admin_log)
        
        # Update submission status
        updated_submission = await temp_policies_collection.find_one({"_id": ObjectId(submission_id)})
        policy_statuses = [p.get("status", "pending") for p in updated_submission["policyInitiatives"] if p]
        
        if all(status in ["approved", "rejected"] for status in policy_statuses):
            new_status = "fully_processed"
        elif any(status == "approved" for status in policy_statuses):
            new_status = "partially_approved"
        else:
            new_status = "pending"
        
        await temp_policies_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {"submission_status": new_status, "updated_at": datetime.utcnow()}}
        )
        
        return {"success": True, "message": f"Action '{action_data.action}' completed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin action failed: {str(e)}")

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
        filter_dict = {}
        if country:
            filter_dict["country"] = {"$regex": country, "$options": "i"}
        if policy_area:
            filter_dict["policyArea"] = policy_area
        
        # Get policies
        cursor = master_policies_collection.find(filter_dict).sort("approved_at", -1).skip(skip).limit(limit)
        
        policies = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
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
        file_stream = io.BytesIO(file_data)
        
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
            "total_approved_policies": await master_policies_collection.count_documents({}),
            "recent_actions": []
        }
        
        # Get recent admin actions
        cursor = admin_actions_collection.find().sort("timestamp", -1).limit(10)
        async for action in cursor:
            action["_id"] = str(action["_id"])
            stats["recent_actions"].append(action)
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@app.delete("/api/admin/master-policy/{policy_id}")
async def delete_master_policy(policy_id: str):
    """Delete a policy from master database"""
    try:
        result = await master_policies_collection.delete_one({"_id": ObjectId(policy_id)})
        
        if result.deleted_count == 1:
            return {"success": True, "message": "Policy deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Policy not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting policy: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI Policy Database API with Admin Workflow is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)