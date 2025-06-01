from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
import mimetypes
import os

from ..models.policy_models import (
    FormSubmission,
    PolicyStatusUpdate,
    PolicyUpdate
)
from ..database.helpers import convert_objectid, pydantic_to_dict
from ..services.file_service import save_file_to_db, validate_file
from ..services.policy_service import update_submission_status, move_policy_to_master
from ..database.crud import (
    insert_submission,
    get_submission,
    get_pending_submissions,
    update_policy_status
)

router = APIRouter(prefix="/api", tags=["policies"])

@router.post("/upload-policy-file")
async def upload_policy_file(
    country: str = Form(...),
    policy_index: int = Form(...),
    submission_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        validate_file(file)
        
        metadata = {
            "country": country,
            "policy_index": policy_index,
            "submission_id": submission_id,
            "original_filename": file.filename
        }
        
        file_id = await save_file_to_db(db.files, file, metadata)
        
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

@router.post("/submit-form")
async def submit_form(
    submission: FormSubmission,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        non_empty_policies = [
            policy for policy in submission.policyInitiatives 
            if policy.policyName and policy.policyName.strip()
        ]
        
        if not non_empty_policies:
            raise HTTPException(status_code=400, detail="At least one policy must be provided")
        
        submission_dict = pydantic_to_dict(submission)
        submission_dict["policyInitiatives"] = [pydantic_to_dict(policy) for policy in non_empty_policies]
        submission_dict["submission_status"] = "pending"
        
        result = await insert_submission(db.temp_policies, submission_dict)
        
        if result:
            return {
                "success": True, 
                "message": "Form submitted successfully and is pending admin review", 
                "submission_id": result,
                "policies_count": len(non_empty_policies)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert data into database")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Form submission failed: {str(e)}")

@router.get("/admin/pending-submissions")
async def get_pending_submissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        skip = (page - 1) * limit
        submissions = await get_pending_submissions(db.temp_policies, skip, limit)
        submissions = [convert_objectid(doc) for doc in submissions]
        
        total_count = await db.temp_policies.count_documents(
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

@router.put("/admin/update-policy-status")
async def update_policy_status(
    status_update: PolicyStatusUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        updated = await update_policy_status(
            db.temp_policies,
            status_update.submission_id,
            status_update.policy_index,
            status_update.status,
            status_update.admin_notes
        )
        
        if updated:
            admin_log = {
                "action": f"status_update_{status_update.status}",
                "submission_id": status_update.submission_id,
                "policy_index": status_update.policy_index,
                "admin_notes": status_update.admin_notes,
                "timestamp": datetime.utcnow()
            }
            await db.admin_actions.insert_one(admin_log)
            
            await update_submission_status(db.temp_policies, status_update.submission_id)
            
            return {"success": True, "message": f"Policy status updated to {status_update.status}"}
        else:
            raise HTTPException(status_code=404, detail="Submission or policy not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status update failed: {str(e)}")

@router.post("/admin/move-to-master")
async def move_policy_to_master_endpoint(
    move_request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await move_policy_to_master(
        db.temp_policies,
        db.master_policies,
        db.admin_actions,
        move_request["submission_id"],
        move_request["policy_index"]
    )