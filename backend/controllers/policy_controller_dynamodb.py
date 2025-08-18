"""
DynamoDB-based Policy controller.
"""
import logging
import os
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from middleware.auth import get_current_user, get_admin_user
from services.policy_service_dynamodb import policy_service
from services.aws_service import aws_service
from models.file_metadata_dynamodb import FileMetadata
from models.policy import EnhancedSubmission

logger = logging.getLogger(__name__)

router = APIRouter()

class PolicySubmission(BaseModel):
    user_id: str
    user_email: str
    country: str
    policyAreas: List[Dict[str, Any]]
    submission_type: str = "form"

class PolicyStatusUpdate(BaseModel):
    submission_id: str
    status: str = Field(..., pattern="^(pending_review|approved|rejected|needs_revision)$")
    admin_notes: str = ""

@router.post("/submit")
async def submit_policy(
    submission: PolicySubmission,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit a new policy for review"""
    try:
        logger.info(f"Policy submission request from user: {current_user['email']}")
        
        submission_data = submission.dict()
        result = await policy_service.submit_policy(submission_data, current_user)
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy submission error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit policy"
        )

@router.post("/submit-enhanced-form")
async def submit_enhanced_form(
    submission: EnhancedSubmission,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit enhanced policy form"""
    try:
        logger.info(f"Enhanced policy submission request from user: {current_user['email']}")
        
        submission_data = submission.dict()
        result = await policy_service.submit_enhanced_form(submission_data, current_user)
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced policy submission error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit enhanced policy"
        )

@router.get("/user-submissions")
async def get_user_submissions(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all submissions for the current user"""
    try:
        logger.info(f"Getting submissions for user: {current_user['email']}")
        
        submissions = await policy_service.get_user_submissions(current_user['user_id'])
        
        return {
            "success": True,
            "data": submissions,
            "count": len(submissions)
        }
        
    except Exception as e:
        logger.error(f"Error getting user submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user submissions"
        )

@router.get("/submission/{submission_id}")
async def get_submission(
    submission_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific submission by ID"""
    try:
        logger.info(f"Getting submission {submission_id} for user: {current_user['email']}")
        
        submission = await policy_service.get_submission_by_id(submission_id)
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Check if user owns this submission or is admin
        if submission['user_id'] != current_user['user_id'] and current_user.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "success": True,
            "data": submission
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get submission"
        )

@router.put("/admin/update-status")
async def update_policy_status(
    status_update: PolicyStatusUpdate,
    current_admin: Dict[str, Any] = Depends(get_admin_user)
):
    """Update policy status (admin only)"""
    try:
        logger.info(f"Status update request from admin: {current_admin['email']}")
        
        result = await policy_service.update_policy_status(status_update.dict(), current_admin)
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating policy status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update policy status"
        )

@router.get("/country/{country_name}")
async def get_country_policies(country_name: str):
    """Get policies for a specific country"""
    try:
        logger.info(f"Getting policies for country: {country_name}")
        
        policies = await policy_service.get_country_policies(country_name)
        
        return {
            "success": True,
            "data": policies,
            "count": len(policies),
            "country": country_name
        }
        
    except Exception as e:
        logger.error(f"Error getting country policies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get country policies"
        )

@router.get("/search")
async def search_policies(
    q: str,
    country: str = None,
    limit: int = 20
):
    """Search policies by query"""
    try:
        logger.info(f"Searching policies with query: {q}")
        
        if not q or len(q.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters"
            )
        
        policies = await policy_service.search_policies(q.strip(), country, min(limit, 100))
        
        return {
            "success": True,
            "data": policies,
            "count": len(policies),
            "query": q,
            "country": country
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching policies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search policies"
        )


@router.get("/all")
async def get_all_policies():
    """Get all policies (any status) for frontend summary cards/charts"""
    try:
        logger.info("Getting all policies for frontend summary/charts")
        policies = await policy_service.get_all_policies()
        return {
            "success": True,
            "data": policies,
            "count": len(policies)
        }
    except Exception as e:
        logger.error(f"Error getting all policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get all policies: {str(e)}")

@router.get("/map-visualization")
async def get_map_visualization():
    """Get country-wise policy counts for color-coded map visualization"""
    try:
        logger.info("Getting map visualization data")
        
        # Get all approved policies
        policies = await policy_service.get_approved_policies_for_map()
        
        # Group by country and count
        country_counts = {}
        for policy in policies:
            country = policy.get('country', 'Unknown')
            if country not in country_counts:
                country_counts[country] = {
                    'country': country,
                    'policy_count': 0,
                    'policies': []
                }
            country_counts[country]['policy_count'] += 1
            country_counts[country]['policies'].append({
                'policy_name': policy.get('policy_name', ''),
                'policy_area': policy.get('policy_area', ''),
                'approved_at': policy.get('approved_at', '')
            })
        
        # Add color coding based on policy counts
        for country_data in country_counts.values():
            count = country_data['policy_count']
            if 1 <= count <= 3:
                country_data['color'] = 'green'
                country_data['level'] = 'low'
            elif 4 <= count <= 7:
                country_data['color'] = 'yellow'
                country_data['level'] = 'medium'
            elif 8 <= count <= 10:
                country_data['color'] = 'red'
                country_data['level'] = 'high'
            else:
                country_data['color'] = 'blue'  # For counts > 10
                country_data['level'] = 'very_high'
        
        return {
            "success": True,
            "countries": list(country_counts.values()),
            "total_countries": len(country_counts),
            "total_policies": len(policies)
        }
        
    except Exception as e:
        logger.error(f"Error getting approved policies for map: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get approved policies for map"
        )


@router.get("/statistics")
async def get_policy_statistics():
    """Get policy statistics"""
    try:
        logger.info("Getting policy statistics")
        
        stats = await policy_service.get_policy_statistics()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting policy statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get policy statistics"
        )


@router.post("/upload-policy-file")
async def upload_policy_file(
    file: UploadFile = File(...),
    policy_area: str = Form(...),
    country: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload policy file to AWS S3 and perform AI analysis"""
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
            "user_id": str(current_user.get("user_id", current_user.get("_id"))),
            "upload_type": "policy_document"
        }
        
        # Upload to S3
        result = await aws_service.upload_file(file, metadata)
        logger.info(f"Policy file uploaded to S3 by {current_user.get('email')}: {file.filename}")
        
        # Perform AI analysis if it's a text-based document
        ai_analysis_data = None
        if file.content_type in ['application/pdf', 'application/msword', 
                                'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                'text/plain']:
            try:
                # Get file content for analysis
                file_content = await file.read()
                await file.seek(0)  # Reset file pointer
                
                # Import AI service and analyze
                from services.ai_analysis_service import ai_analysis_service
                text_content = ai_analysis_service.extract_text_from_file(file_content, file.filename)
                
                if text_content.strip():
                    ai_analysis_data = ai_analysis_service.analyze_policy_document(text_content)
                    logger.info(f"AI analysis completed for file: {file.filename}")
                
            except Exception as ai_error:
                logger.warning(f"AI analysis failed for {file.filename}: {str(ai_error)}")
                # Continue with upload even if AI analysis fails
        
        # Save file metadata to DynamoDB with AI analysis
        file_metadata = FileMetadata(
            file_id=result.get('file_id'),
            user_id=current_user.get('user_id', current_user.get('_id')),
            filename=result.get('filename', file.filename),
            original_filename=file.filename,
            file_size=result.get('size'),
            file_type=file.content_type,
            mime_type=file.content_type,
            s3_bucket=aws_service.bucket_name,
            s3_key=result.get('s3_key'),
            s3_url=result.get('file_url'),
            upload_status='completed',
            metadata=metadata,
            ai_analysis=ai_analysis_data or {}
        )
        await file_metadata.save()
        
        response_data = {
            "success": True,
            "message": "File uploaded successfully",
            "file_data": result
        }
        
        # Include AI analysis data if available
        if ai_analysis_data:
            response_data["ai_analysis"] = ai_analysis_data
            response_data["message"] = "File uploaded and analyzed successfully"
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.post("/submit-with-file")
async def submit_policy_with_file(
    file: UploadFile = File(...),
    policy_area: str = Form(...),
    country: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Submit policy with file upload and AI analysis for admin approval"""
    try:
        # First upload the file and get AI analysis
        file_upload_result = await upload_policy_file(
            file=file,
            policy_area=policy_area,
            country=country,
            description=description,
            current_user=current_user
        )
        
        # Extract AI analysis data
        ai_analysis_data = file_upload_result.get("ai_analysis", {})
        file_data = file_upload_result.get("file_data", {})
        
        # Create policy submission with AI-extracted data
        policy_submission_data = {
            "user_id": current_user.get('user_id', current_user.get('_id')),
            "user_email": current_user.get('email'),
            "country": country,
            "submission_type": "file_upload",
            "file_metadata": {
                "file_id": file_data.get('file_id'),
                "filename": file.filename,
                "s3_key": file_data.get('s3_key'),
                "file_url": file_data.get('file_url')
            },
            "policyAreas": [{
                "area_id": policy_area.lower().replace(" ", "_"),
                "area_name": policy_area,
                "policies": [{
                    "policyName": ai_analysis_data.get('policyName', file.filename),
                    "policyId": ai_analysis_data.get('policyId', f"{policy_area}-{file.filename}"),
                    "policyDescription": ai_analysis_data.get('policyDescription', description or ''),
                    "targetGroups": ai_analysis_data.get('targetGroups', []),
                    "policyLink": ai_analysis_data.get('policyLink', ''),
                    "implementation": ai_analysis_data.get('implementation', {}),
                    "evaluation": ai_analysis_data.get('evaluation', {}),
                    "participation": ai_analysis_data.get('participation', {}),
                    "alignment": ai_analysis_data.get('alignment', {}),
                    "ai_extracted": True,
                    "source_file": file.filename
                }]
            }]
        }
        
        # Submit policy for approval
        submission_result = await policy_service.submit_policy(policy_submission_data, current_user)
        
        return {
            "success": True,
            "message": "Policy submitted successfully for admin approval",
            "submission_data": submission_result,
            "file_data": file_data,
            "ai_analysis": ai_analysis_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy submission with file error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting policy: {str(e)}")


@router.get("/policy-file/{file_id}")
async def get_policy_file_info(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get policy file information and URL"""
    try:
        # Get file URL using AWS service
        if aws_service.cloudfront_domain:
            file_url = aws_service._generate_cdn_url(file_id)
        else:
            file_url = aws_service._generate_file_url(file_id)
        
        return {
            "success": True,
            "file_url": file_url,
            "file_id": file_id
        }
        
    except Exception as e:
        logger.error(f"Get file info error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")


# Export router

# Endpoint to get full country list
@router.get("/countries")
async def get_countries():
    """Return full country list from constants"""
    try:
        from config.data_constants import COUNTRIES
        return {"success": True, "countries": COUNTRIES, "count": len(COUNTRIES)}
    except Exception as e:
        logger.error(f"Error getting countries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get countries: {str(e)}")

# Endpoint to get full policy area list
@router.get("/policy-areas")
async def get_policy_areas():
    """Return full policy area list from constants"""
    try:
        from config.data_constants import POLICY_AREAS
        return {"success": True, "policy_areas": POLICY_AREAS, "count": len(POLICY_AREAS)}
    except Exception as e:
        logger.error(f"Error getting policy areas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get policy areas: {str(e)}")

policy_router = router
