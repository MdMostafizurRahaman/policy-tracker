"""
Policy Controller
Handles HTTP requests for policy operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional
import logging

from middleware.auth import get_current_user, get_admin_user
# Temporarily disabled MongoDB policy service
# from services.policy_service import policy_service
from models.policy import EnhancedSubmission, PolicyStatusUpdate, PolicyResponse
from utils.helpers import convert_objectid
from utils.file_handler import save_file_to_s3, get_file_from_s3, get_file_url, get_presigned_url, delete_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Policies"])


@router.post("/submit-enhanced-form")
async def submit_enhanced_form(
    submission: EnhancedSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Submit enhanced policy form"""
    try:
        return await policy_service.submit_enhanced_form(submission.dict(), current_user)
    except Exception as e:
        logger.error(f"Policy submission error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update-enhanced-policy-status")
async def update_enhanced_policy_status(
    status_update: PolicyStatusUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update policy status (admin only) - DEPRECATED: Use /admin/update-policy-status instead"""
    try:
        return await policy_service.update_policy_status(status_update, admin_user)
    except Exception as e:
        logger.error(f"Policy status update error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/public/country-policies/{country_name}")
async def get_country_policies(country_name: str):
    """Get policies for a specific country"""
    try:
        return await policy_service.get_country_policies(country_name)
    except Exception as e:
        logger.error(f"Get country policies error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/countries")
async def get_countries():
    """Get list of countries"""
    try:
        from config.constants import COUNTRIES
        return {"countries": COUNTRIES}
    except Exception as e:
        logger.error(f"Get countries error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy-areas")
async def get_policy_areas():
    """Get list of policy areas"""
    try:
        from config.constants import POLICY_AREAS
        return {"policy_areas": POLICY_AREAS}
    except Exception as e:
        logger.error(f"Get policy areas error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-policy-file")
async def upload_policy_file(
    file: UploadFile = File(...),
    policy_area: str = Form(...),
    country: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload policy file to AWS S3"""
    try:
        # Validate file type
        allowed_types = [
            'application/pdf', 
            'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file.content_type} not allowed. Allowed types: PDF, DOC, DOCX, TXT, CSV, XLS, XLSX"
            )
        
        # Validate file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Prepare metadata
        metadata = {
            "policy_area": policy_area,
            "country": country,
            "description": description,
            "uploaded_by": current_user.get("email"),
            "user_id": str(current_user.get("_id")),
            "upload_type": "policy_document"
        }
        
        # Upload to S3
        result = await save_file_to_s3(file, metadata)
        
        logger.info(f"Policy file uploaded by {current_user.get('email')}: {file.filename}")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.get("/policy-file/{file_id}")
async def get_policy_file_info(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get policy file information and URL"""
    try:
        # Get file URL (CDN preferred)
        file_url = await get_file_url(file_id=file_id, use_cdn=True)
        
        return {
            "success": True,
            "file_url": file_url,
            "file_id": file_id
        }
        
    except Exception as e:
        logger.error(f"Get file info error: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")


@router.get("/policy-file/{file_id}/download")
async def download_policy_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get presigned URL for secure file download"""
    try:
        # Generate presigned URL (valid for 1 hour)
        presigned_url = await get_presigned_url(file_id=file_id, expiration=3600)
        
        return {
            "success": True,
            "download_url": presigned_url,
            "expires_in": 3600
        }
        
    except Exception as e:
        logger.error(f"Generate download URL error: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")


@router.delete("/policy-file/{file_id}")
async def delete_policy_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete policy file (user can only delete their own files unless admin)"""
    try:
        # Check if user is admin or file owner
        # This should be implemented with proper authorization
        
        success = await delete_file(file_id=file_id)
        
        if success:
            logger.info(f"Policy file deleted by {current_user.get('email')}: {file_id}")
            return {"success": True, "message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        
    except Exception as e:
        logger.error(f"Delete file error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@router.get("/files/{filename}")
async def serve_local_file(filename: str):
    """Serve locally stored files when S3 is unavailable"""
    import os
    from fastapi.responses import FileResponse
    
    file_path = os.path.join("uploads", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename
    )
