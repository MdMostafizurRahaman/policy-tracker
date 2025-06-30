"""
Policy management routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from models.policy import (
    PolicyCreate, PolicyUpdate, PolicyResponse, PolicyApproval, PolicySearch
)
from routers.auth import get_current_user
from models.user import UserResponse
from config.database import get_database
from config.settings import POLICY_AREAS, COUNTRIES
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import json
import io
import csv
from pathlib import Path
import uuid
import shutil
import os

router = APIRouter()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def convert_objectid(obj):
    """Convert ObjectId to string recursively"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

def get_policies_collection():
    """Get policies collection"""
    db = get_database()
    return db.temp_submissions

def get_master_policies_collection():
    """Get master policies collection"""
    db = get_database()
    return db.master_policies

def get_files_collection():
    """Get files collection"""
    db = get_database()
    return db.files

@router.post("/submit", response_model=dict)
async def submit_policy(
    policy_data: PolicyCreate,
    current_user: UserResponse = Depends(get_current_user),
    policies_collection = Depends(get_policies_collection)
):
    """Submit new policy for review"""
    try:
        policy_doc = {
            **policy_data.dict(),
            "status": "pending",
            "submittedBy": current_user.id,
            "submittedAt": datetime.utcnow(),
            "approvedBy": None,
            "approvedAt": None
        }
        
        result = await policies_collection.insert_one(policy_doc)
        
        return {
            "message": "Policy submitted successfully",
            "policy_id": str(result.inserted_id)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit policy"
        )

@router.get("/search", response_model=List[PolicyResponse])
async def search_policies(
    query: Optional[str] = None,
    country: Optional[str] = None,
    policy_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    policies_collection = Depends(get_policies_collection),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Search policies"""
    try:
        # Build search filter
        search_filter = {}
        
        if query:
            search_filter["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$elemMatch": {"$regex": query, "$options": "i"}}},
                {"keyPoints": {"$elemMatch": {"$regex": query, "$options": "i"}}}
            ]
        
        if country:
            search_filter["country"] = {"$regex": country, "$options": "i"}
        
        if policy_type:
            search_filter["policyType"] = policy_type
        
        # Search in both collections
        temp_filter = {**search_filter, "status": "approved"}
        
        temp_results = await policies_collection.find(temp_filter).skip(offset).limit(limit).to_list(length=limit)
        master_results = await master_policies_collection.find(search_filter).skip(offset).limit(limit).to_list(length=limit)
        
        # Combine and format results
        all_results = temp_results + master_results
        
        policies = []
        for policy in all_results[:limit]:
            policies.append(PolicyResponse(
                id=str(policy["_id"]),
                title=policy["title"],
                description=policy["description"],
                country=policy["country"],
                policyType=policy["policyType"],
                source=policy.get("source"),
                url=policy.get("url"),
                dateImplemented=policy.get("dateImplemented"),
                tags=policy.get("tags", []),
                keyPoints=policy.get("keyPoints", []),
                status=policy.get("status", "approved"),
                submittedBy=policy.get("submittedBy"),
                submittedAt=policy.get("submittedAt", policy.get("created_at")),
                approvedBy=policy.get("approvedBy"),
                approvedAt=policy.get("approvedAt")
            ))
        
        return policies
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    policies_collection = Depends(get_policies_collection),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Get policy by ID"""
    try:
        # Try temp submissions first
        policy = await policies_collection.find_one({"_id": ObjectId(policy_id)})
        
        # If not found, try master policies
        if not policy:
            policy = await master_policies_collection.find_one({"_id": ObjectId(policy_id)})
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        return PolicyResponse(
            id=str(policy["_id"]),
            title=policy["title"],
            description=policy["description"],
            country=policy["country"],
            policyType=policy["policyType"],
            source=policy.get("source"),
            url=policy.get("url"),
            dateImplemented=policy.get("dateImplemented"),
            tags=policy.get("tags", []),
            keyPoints=policy.get("keyPoints", []),
            status=policy.get("status", "approved"),
            submittedBy=policy.get("submittedBy"),
            submittedAt=policy.get("submittedAt", policy.get("created_at")),
            approvedBy=policy.get("approvedBy"),
            approvedAt=policy.get("approvedAt")
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid policy ID"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get policy"
        )

@router.get("/countries/list")
async def get_countries_with_policies(
    policies_collection = Depends(get_policies_collection),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Get list of countries with policies"""
    try:
        # Get unique countries from both collections
        temp_countries = await policies_collection.distinct("country", {"status": "approved"})
        master_countries = await master_policies_collection.distinct("country")
        
        all_countries = list(set(temp_countries + master_countries))
        all_countries.sort()
        
        return {"countries": all_countries}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get countries"
        )

@router.post("/submit-with-file")
async def submit_policy_with_file(
    title: str = Form(...),
    description: str = Form(...),
    country: str = Form(...),
    policyType: str = Form(...),
    source: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    keyPoints: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: UserResponse = Depends(get_current_user),
    policies_collection = Depends(get_policies_collection)
):
    """Submit policy with optional file upload"""
    try:
        # Parse tags and key points
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        key_points_list = []
        if keyPoints:
            key_points_list = [point.strip() for point in keyPoints.split('\n') if point.strip()]
        
        # Handle file upload
        file_path = None
        if file and file.filename:
            # Generate unique filename
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        policy_doc = {
            "title": title,
            "description": description,
            "country": country,
            "policyType": policyType,
            "source": source,
            "url": url,
            "tags": tags_list,
            "keyPoints": key_points_list,
            "status": "pending",
            "submittedBy": current_user.id,
            "submittedAt": datetime.utcnow(),
            "filePath": str(file_path) if file_path else None,
            "fileName": file.filename if file else None,
            "approvedBy": None,
            "approvedAt": None
        }
        
        result = await policies_collection.insert_one(policy_doc)
        
        return {
            "message": "Policy submitted successfully",
            "policy_id": str(result.inserted_id),
            "file_uploaded": file_path is not None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit policy: {str(e)}"
        )

@router.post("/submit-enhanced-form")
async def submit_enhanced_form(
    submission_data: dict,
    current_user: UserResponse = Depends(get_current_user),
    policies_collection = Depends(get_policies_collection)
):
    """Enhanced policy submission with better validation"""
    try:
        # Validate user owns this submission
        if submission_data.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Unauthorized submission")
        
        # Filter out empty policy areas and policies
        filtered_policy_areas = []
        total_policies = 0
        
        for area in submission_data.get("policyAreas", []):
            non_empty_policies = [
                policy for policy in area.get("policies", [])
                if policy.get("policyName") and policy.get("policyName").strip()
            ]
            if non_empty_policies:
                area_dict = {
                    "area_id": area.get("area_id"),
                    "area_name": area.get("area_name"),
                    "policies": non_empty_policies
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
            "user_id": submission_data.get("user_id"),
            "user_email": submission_data.get("user_email"),
            "user_name": submission_data.get("user_name"),
            "country": submission_data.get("country"),
            "policyAreas": filtered_policy_areas,
            "submission_status": "pending",
            "total_policies": total_policies,
            "total_areas": len(filtered_policy_areas),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into temporary collection
        result = await policies_collection.insert_one(submission_dict)
        
        if result.inserted_id:
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
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

# File upload support
async def save_file_to_db(file: UploadFile, metadata: dict = None) -> str:
    """Save uploaded file to database"""
    try:
        file_content = await file.read()
        await file.seek(0)
        
        file_doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_data": file_content,
            "size": len(file_content),
            "upload_date": datetime.utcnow(),
            **(metadata or {})
        }
        
        files_collection = get_files_collection()
        result = await files_collection.insert_one(file_doc)
        return str(result.inserted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a file for policy submission"""
    try:
        # Validate file size
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large")
        
        # Reset file pointer
        await file.seek(0)
        
        # Save file to database
        file_id = await save_file_to_db(file, {"uploaded_by": str(current_user.id)})
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# Public policies endpoint
@router.get("/public")
async def get_public_master_policies(
    limit: int = Query(1000, ge=1, le=1000),
    country: str = None,
    area: str = None,
    master_policies_collection = Depends(get_master_policies_collection),
    temp_policies_collection = Depends(get_policies_collection)
):
    """Enhanced public endpoint - shows ALL approved policies with better deduplication"""
    try:
        # FIXED: Remove ALL visibility filters - just get active master policies
        master_filter = {"master_status": "active"}
        
        if country:
            master_filter["country"] = country
        if area:
            master_filter["policyArea"] = area
        
        # Get policies from master collection with ALL fields
        master_policies = []
        async for doc in master_policies_collection.find(master_filter).limit(limit).sort("moved_to_master_at", -1):
            policy_dict = convert_objectid(doc)
            # Ensure consistent field names for frontend compatibility
            policy_dict["name"] = policy_dict.get("policyName", "Unnamed Policy")
            policy_dict["area_id"] = policy_dict.get("policyArea")
            master_policies.append(policy_dict)
        
        # ALSO check temp_submissions for approved policies that might not be migrated yet
        temp_filter = {}
        if country:
            temp_filter["country"] = country
        
        temp_policies = []
        async for submission in temp_policies_collection.find(temp_filter):
            country_name = submission.get("country")
            if country and country_name != country:
                continue
                
            # Handle different data formats
            if "policyAreas" in submission:
                policy_areas = submission["policyAreas"]
                
                if isinstance(policy_areas, list):
                    # New format: list of {area_id, area_name, policies}
                    for area_data in policy_areas:
                        area_id = area_data.get("area_id")
                        if not area or (area and area_id == area):
                            policies = area_data.get("policies", [])
                            for policy_index, policy in enumerate(policies):
                                if policy.get("status") == "approved":
                                    # Check if already in master
                                    exists = await master_policies_collection.find_one({
                                        "original_submission_id": str(submission["_id"]),
                                        "policyArea": area_id,
                                        "policy_index": policy_index
                                    })
                                    if not exists:
                                        area_info = next((a for a in POLICY_AREAS if a["id"] == area_id), None)
                                        temp_policy = {
                                            **convert_objectid(policy),
                                            "country": country_name,
                                            "policyArea": area_id,
                                            "area_name": area_info["name"] if area_info else area_id,
                                            "area_icon": area_info["icon"] if area_info else "📄",
                                            "name": policy.get("policyName", "Unnamed Policy"),
                                            "area_id": area_id,
                                            "master_status": "active"
                                        }
                                        temp_policies.append(temp_policy)
        
        # Combine both sources
        all_policies = master_policies + temp_policies
        
        # FIXED: Use MongoDB _id as the primary deduplication key (most reliable)
        unique_policies = []
        seen_ids = set()
        
        for policy in all_policies:
            # Use the MongoDB _id as the primary key (most reliable)
            policy_id = str(policy.get('_id', ''))
            
            if policy_id and policy_id not in seen_ids:
                seen_ids.add(policy_id)
                unique_policies.append(policy)
            elif not policy_id:
                # For policies without _id, use a fallback key
                fallback_key = f"{policy.get('country', '')}-{policy.get('policyArea', '')}-{policy.get('policyName', policy.get('name', ''))}-{policy.get('moved_to_master_at', '')}"
                if fallback_key not in seen_ids:
                    seen_ids.add(fallback_key)
                    unique_policies.append(policy)
        
        # Apply limit
        final_policies = unique_policies[:limit]
        
        return {
            "success": True,
            "policies": final_policies,
            "total_count": len(final_policies),
            "sources": {
                "master_db": len(master_policies),
                "temp_approved": len(temp_policies),
                "total_unique": len(final_policies),
                "duplicates_removed": len(all_policies) - len(final_policies),
                "deduplication_method": "mongodb_id_primary"
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "policies": [],
            "total_count": 0,
            "error": str(e)
        }

# Country-specific policies endpoint
@router.get("/public/country/{country_name}")
async def get_country_policies_detailed(
    country_name: str,
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Get detailed policies for a specific country with proper grouping"""
    try:
        filter_dict = {
            "master_status": "active",
            "country": country_name
        }
        
        # Get all policies for the country
        policies_cursor = master_policies_collection.find(filter_dict).sort("moved_to_master_at", -1)
        policies = []
        
        async for doc in policies_cursor:
            policy_dict = convert_objectid(doc)
            # Ensure compatibility with frontend
            policy_dict["name"] = policy_dict.get("policyName", "Unnamed Policy")
            policy_dict["policy_name"] = policy_dict.get("policyName", "Unnamed Policy") 
            policy_dict["type"] = policy_dict.get("area_name", policy_dict.get("policyArea", "Unknown"))
            policy_dict["year"] = policy_dict.get("implementation", {}).get("deploymentYear", "TBD")
            policies.append(policy_dict)
        
        # Group by policy area
        policies_by_area = {}
        for policy in policies:
            area_id = policy.get("policyArea", "unknown")
            area_name = policy.get("area_name", area_id)
            
            if area_id not in policies_by_area:
                policies_by_area[area_id] = {
                    "area_id": area_id,
                    "area_name": area_name,
                    "area_icon": policy.get("area_icon", "📄"),
                    "policies": []
                }
            policies_by_area[area_id]["policies"].append(policy)
        
        return {
            "success": True,
            "country": country_name,
            "total_policies": len(policies),
            "policy_areas": list(policies_by_area.values())
        }
    
    except Exception as e:
        return {
            "success": False,
            "country": country_name, 
            "total_policies": 0,
            "policy_areas": [],
            "error": str(e)
        }

# CSV Export endpoint
@router.get("/export/csv")
async def export_policies_csv(
    current_user: UserResponse = Depends(get_current_user),
    master_policies_collection = Depends(get_master_policies_collection)
):
    """Export policies to CSV format"""
    try:
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            "Country", "Policy Name", "Policy Area", "Description", "Year", 
            "Status", "Implementation Budget", "Evaluation", "Participation"
        ]
        writer.writerow(headers)
        
        # Write policy data
        async for policy in master_policies_collection.find({"master_status": "active"}):
            row = [
                policy.get("country", ""),
                policy.get("policyName", ""),
                policy.get("area_name", policy.get("policyArea", "")),
                policy.get("policyDescription", "")[:200],  # Limit description length
                policy.get("implementation", {}).get("deploymentYear", ""),
                policy.get("status", ""),
                policy.get("implementation", {}).get("yearlyBudget", ""),
                "Yes" if policy.get("evaluation", {}).get("isEvaluated") else "No",
                "Yes" if policy.get("participation", {}).get("hasConsultation") else "No"
            ]
            writer.writerow(row)
        
        output.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ai_policies.csv"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Utility endpoints
@router.get("/countries")
async def get_countries():
    """Get list of all available countries"""
    return {"countries": COUNTRIES, "total": len(COUNTRIES)}

@router.get("/policy-areas")
async def get_policy_areas():
    """Get list of all policy areas with enhanced metadata"""
    return {"policy_areas": POLICY_AREAS, "total": len(POLICY_AREAS)}
