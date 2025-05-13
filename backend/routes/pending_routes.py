# from fastapi import APIRouter, Form, HTTPException, UploadFile, Body, File, Query, Path, Depends
# from fastapi.responses import FileResponse
# import os
# import shutil
# from typing import Optional, List
# from datetime import datetime
# import logging
# from database import pending_collection, approved_collection
# from models import POLICY_TYPES, TARGET_GROUPS, AI_PRINCIPLES, Policy, PolicyUpdateRequest, PolicyApprovalRequest, PolicyDeclineRequest, SubmissionRemovalRequest
# from routes.utils_routes import generate_policy_data_csv
# import csv
# from models import (
#     SubmissionsResponse,
#     PolicyUpdateRequest,
#     PolicyApprovalRequest,
#     PolicyDeclineRequest,
#     SubmissionRemovalRequest
# )
# import math

# router = APIRouter(prefix="/api", tags=["pending_submissions"])

# # Configure logger
# logger = logging.getLogger("policy_tracker")
# logging.basicConfig(level=logging.INFO)
# router = APIRouter(prefix="/api", tags=["pending_submissions"])



# @router.post("/submit-policy")
# async def submit_policy(
#     country: str = Form(...),
#     policy_1_file: Optional[UploadFile] = File(None), policy_1_text: Optional[str] = Form(None),
#     policy_2_file: Optional[UploadFile] = File(None), policy_2_text: Optional[str] = Form(None),
#     policy_3_file: Optional[UploadFile] = File(None), policy_3_text: Optional[str] = Form(None),
#     policy_4_file: Optional[UploadFile] = File(None), policy_4_text: Optional[str] = Form(None),
#     policy_5_file: Optional[UploadFile] = File(None), policy_5_text: Optional[str] = Form(None),
#     policy_6_file: Optional[UploadFile] = File(None), policy_6_text: Optional[str] = Form(None),
#     policy_7_file: Optional[UploadFile] = File(None), policy_7_text: Optional[str] = Form(None),
#     policy_8_file: Optional[UploadFile] = File(None), policy_8_text: Optional[str] = Form(None),
#     policy_9_file: Optional[UploadFile] = File(None), policy_9_text: Optional[str] = Form(None),
#     policy_10_file: Optional[UploadFile] = File(None), policy_10_text: Optional[str] = Form(None),
# ):
#     try:
#         country = country.strip()
#         if not country:
#             raise HTTPException(status_code=400, detail="Country name is required")

#         file_text_pairs = [
#             (policy_1_file, policy_1_text), (policy_2_file, policy_2_text),
#             (policy_3_file, policy_3_text), (policy_4_file, policy_4_text),
#             (policy_5_file, policy_5_text), (policy_6_file, policy_6_text),
#             (policy_7_file, policy_7_text), (policy_8_file, policy_8_text),
#             (policy_9_file, policy_9_text), (policy_10_file, policy_10_text),
#         ]

#         if not any((f and f.filename) or (t and t.strip()) for f, t in file_text_pairs):
#             raise HTTPException(status_code=400, detail="At least one policy must be provided")

#         current_time = datetime.now()
#         policies = []

#         for i, (file, text) in enumerate(file_text_pairs):
#             if not file and (not text or not text.strip()):
#                 continue

#             policy_type = POLICY_TYPES[i] if i < len(POLICY_TYPES) else f"Policy {i+1}"

#             policy_data = {
#                 "policyName": f"{policy_type} Policy",
#                 "policyId": f"{country.lower().replace(' ', '_')}_{i+1}",
#                 "policyArea": policy_type,
#                 "targetGroups": [],
#                 "policyDescription": text.strip() if text else "",
#                 "policyFile": None,
#                 "policyLink": None,
#                 "implementation": {
#                     "yearlyBudget": None,
#                     "budgetCurrency": "USD",
#                     "privateSecFunding": False,
#                     "deploymentYear": None
#                 },
#                 "evaluation": {
#                     "isEvaluated": False,
#                     "evaluationType": "internal",
#                     "riskAssessment": False,
#                     "transparencyScore": 0,
#                     "explainabilityScore": 0,
#                     "accountabilityScore": 0
#                 },
#                 "participation": {
#                     "hasConsultation": False,
#                     "consultationStartDate": None,
#                     "consultationEndDate": None,
#                     "commentsPublic": False,
#                     "stakeholderScore": 0
#                 },
#                 "alignment": {
#                     "aiPrinciples": [],
#                     "humanRightsAlignment": False,
#                     "environmentalConsiderations": False,
#                     "internationalCooperation": False
#                 },
#                 "status": "pending",
#                 "isRead": False,
#                 "adminNotes": "",
#                 "createdAt": current_time.isoformat(),
#                 "updatedAt": current_time.isoformat()
#             }

#             # Handle file upload
#             if file and file.filename:
#                 try:
#                     filename = os.path.basename(file.filename)
#                     timestamp = int(current_time.timestamp())
#                     safe_filename = f"{country.lower().replace(' ', '_')}_policy_{i+1}_{timestamp}_{filename}"
#                     file_path = f"temp_policies/{safe_filename}"

#                     allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']
#                     file_ext = os.path.splitext(filename)[1].lower()

#                     if file_ext not in allowed_extensions:
#                         raise ValueError(f"Unsupported file type: {file_ext}")

#                     os.makedirs("temp_policies", exist_ok=True)
#                     with open(file_path, "wb") as buffer:
#                         shutil.copyfileobj(file.file, buffer)

#                     policy_data["policyFile"] = file_path
#                 except Exception as e:
#                     logger.error(f"Error saving file: {e}", exc_info=True)
#                     policy_data["policyFile"] = None

#             policies.append(policy_data)

#         existing = pending_collection.find_one({"country": country})
#         if existing:
#             pending_collection.update_one(
#                 {"country": country},
#                 {
#                     "$set": {
#                         "policyInitiatives": policies,
#                         "isRead": False,
#                         "updatedAt": current_time.isoformat()
#                     }
#                 }
#             )
#             return {"message": "Existing submission updated", "status": "success"}
#         else:
#             pending_collection.insert_one({
#                 "country": country,
#                 "policyInitiatives": policies,
#                 "isRead": False,
#                 "createdAt": current_time.isoformat(),
#                 "updatedAt": current_time.isoformat()
#             })
#             return {"message": "New submission received", "status": "success"}

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal server error")


# @router.get("/pending-submissions", response_model=SubmissionsResponse)
# async def get_pending_submissions(
#     page: int = Query(1, ge=1, description="Page number"),
#     limit: int = Query(10, ge=1, le=100, description="Items per page"),
#     sort_by: str = Query("updatedAt", description="Field to sort by"),
#     sort_order: int = Query(-1, description="Sort order: 1 for ascending, -1 for descending"),
#     read_status: Optional[bool] = Query(None, description="Filter by read status (True/False)")
# ):
#     """
#     Retrieve all pending policy submissions with pagination, sorting and filtering
#     """
#     try:
#         # Build filter query
#         filter_query = {}
#         if read_status is not None:
#             filter_query["isRead"] = read_status
            
#         # Calculate pagination values
#         skip = (page - 1) * limit
        
#         # Get total count for pagination info
#         total_count = pending_collection.count_documents(filter_query)
#         total_pages = math.ceil(total_count / limit)
        
#         # Fetch submissions with pagination and sorting
#         cursor = pending_collection.find(filter_query).sort(sort_by, sort_order).skip(skip).limit(limit)
        
#         # Convert cursor to list of dictionaries
#         submissions = []
#         for doc in cursor:
#             # Convert ObjectId to string for JSON serialization
#             doc["_id"] = str(doc["_id"])
            
#             # Add policy count for UI display
#             doc["policyCount"] = len(doc.get("policyInitiatives", []))
            
#             # Remove large policy text content for list view
#             if "policyInitiatives" in doc:
#                 for policy in doc["policyInitiatives"]:
#                     if "policyDescription" in policy:
#                         # Keep only a short preview
#                         desc = policy["policyDescription"]
#                         policy["policyDescription"] = desc[:100] + "..." if len(desc) > 100 else desc
            
#             submissions.append(doc)
        
#         # Create pagination info
#         pagination = {
#             "current_page": page,
#             "total_pages": total_pages,
#             "total_count": total_count,
#             "per_page": limit
#         }
        
#         return {"submissions": submissions, "pagination": pagination}
        
#     except Exception as e:
#         logger.error(f"Error fetching pending submissions: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to fetch pending submissions: {str(e)}")


# @router.post("/update-policy")
# async def update_policy(request: PolicyUpdateRequest = Body(...)):
#     """Update a policy's content and optionally status"""
#     country = request.country
#     policy_index = request.policyIndex
    
#     # Find the pending submission
#     submission = pending_collection.find_one({"country": country})
#     if not submission:
#         raise HTTPException(status_code=404, detail="Submission not found")
    
#     # Check if policy index is valid
#     if policy_index < 0 or policy_index >= len(submission.get("policyInitiatives", [])):
#         raise HTTPException(status_code=400, detail="Invalid policy index")
    
#     # Update policy description
#     submission["policyInitiatives"][policy_index]["policyDescription"] = request.text
#     submission["policyInitiatives"][policy_index]["updatedAt"] = datetime.now().isoformat()
    
#     # Update status if provided
#     if request.status:
#         submission["policyInitiatives"][policy_index]["status"] = request.status
    
#     # Update in MongoDB
#     pending_collection.update_one(
#         {"country": country},
#         {"$set": {"policyInitiatives": submission["policyInitiatives"]}}
#     )
    
#     return {"message": "Policy updated successfully"}

# @router.post("/add-admin-notes")
# async def add_admin_notes(
#     payload: dict = Body(...)
# ):
#     """Add or update admin notes for a policy"""
#     country = payload.get("country")
#     policy_index = int(payload.get("policyIndex"))
#     notes = payload.get("notes", "")
    
#     # Find the pending submission
#     submission = pending_collection.find_one({"country": country})
#     if not submission:
#         raise HTTPException(status_code=404, detail="Submission not found")
    
#     # Check if policy index is valid
#     if policy_index < 0 or policy_index >= len(submission.get("policyInitiatives", [])):
#         raise HTTPException(status_code=400, detail="Invalid policy index")
    
#     # Update admin notes
#     submission["policyInitiatives"][policy_index]["adminNotes"] = notes
#     submission["policyInitiatives"][policy_index]["updatedAt"] = datetime.now().isoformat()
    
#     # Update in MongoDB
#     pending_collection.update_one(
#         {"country": country},
#         {"$set": {"policyInitiatives": submission["policyInitiatives"]}}
#     )
    
#     return {"message": "Admin notes updated successfully"}

# @router.post("/approve-policy")
# def approve_policy(payload: dict = Body(...)):
#     """Approve a specific policy from a country's submission"""
#     country = payload.get("country")
#     policy_index = payload.get("policyIndex")
#     admin_notes = payload.get("adminNotes", "")
    
#     if country is None or policy_index is None:
#         raise HTTPException(status_code=400, detail="Country and policyIndex are required")
    
#     # Convert policy_index to integer if it's not already
#     policy_index = int(policy_index)
    
#     # Find the pending submission
#     submission = pending_collection.find_one({"country": country})
#     if not submission:
#         raise HTTPException(status_code=404, detail="Submission not found")
    
#     # Check if policy index is valid
#     if policy_index < 0 or policy_index >= len(submission.get("policyInitiatives", [])):
#         raise HTTPException(status_code=400, detail="Invalid policy index")
    
#     # Get the specific policy
#     policy = submission["policyInitiatives"][policy_index]
    
#     # Check if there's anything to approve
#     if not policy.get("policyFile") and not policy.get("policyDescription"):
#         raise HTTPException(status_code=400, detail="No policy content to approve")
    
#     # Move file to approved directory if present
#     if policy.get("policyFile"):
#         temp_path = policy["policyFile"]
#         filename = os.path.basename(temp_path)
        
#         # Create approved_policies directory if it doesn't exist
#         os.makedirs("approved_policies", exist_ok=True)
        
#         approved_path = f"approved_policies/{filename}"
        
#         if os.path.exists(temp_path):
#             # Copy instead of move, so we keep the original
#             try:
#                 shutil.copy(temp_path, approved_path)
#                 policy["policyFile"] = approved_path
#             except Exception as e:
#                 raise HTTPException(status_code=500, detail=f"Error copying file: {str(e)}")
    
#     # Update admin notes if provided
#     if admin_notes:
#         policy["adminNotes"] = admin_notes
        
#     # Mark this policy as approved
#     policy["status"] = "approved"
#     policy["updatedAt"] = datetime.now().isoformat()
    
#     # Update the policy in the submission
#     submission["policyInitiatives"][policy_index] = policy
#     submission["updatedAt"] = datetime.now().isoformat()
    
#     # Update in MongoDB
#     try:
#         pending_collection.update_one(
#             {"country": country},
#             {"$set": {"policyInitiatives": submission["policyInitiatives"], "updatedAt": submission["updatedAt"]}}
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"MongoDB update error: {str(e)}")
    
#     # Check if we need to create or update in approved collection
#     existing_approved = approved_collection.find_one({"country": country})
    
#     if existing_approved:
#         # If country exists in approved, update that specific policy
#         existing_approved["policyInitiatives"][policy_index] = policy
#         existing_approved["updatedAt"] = datetime.now().isoformat()
#         approved_collection.update_one(
#             {"country": country},
#             {"$set": {"policyInitiatives": existing_approved["policyInitiatives"], "updatedAt": existing_approved["updatedAt"]}}
#         )
#     else:
#         # Otherwise, create a new entry with just this policy approved
#         new_approved = {
#             "country": country,
#             "policyInitiatives": [create_empty_policy(i) for i in range(len(POLICY_TYPES))],
#             "createdAt": datetime.now().isoformat(),
#             "updatedAt": datetime.now().isoformat()
#         }
#         new_approved["policyInitiatives"][policy_index] = policy
#         approved_collection.insert_one(new_approved)
    
#     # Update the CSV file
#     generate_policy_data_csv()
    
#     return {"message": f"Policy {policy_index} for {country} approved"}

# @router.post("/approve-submission")
# def approve_submission(payload: dict = Body(...)):
#     """Approve an entire country submission, moving all policies to approved status"""
#     country = payload.get("country")
#     if not country:
#         raise HTTPException(status_code=400, detail="Country is required")

#     # Find the pending submission
#     submission = pending_collection.find_one({"country": country})
#     if not submission:
#         raise HTTPException(status_code=404, detail="Submission not found")

#     current_time = datetime.now().isoformat()
    
#     # Move files from temp to approved directory if needed
#     policies = submission.get("policyInitiatives", [])
#     for i, policy in enumerate(policies):
#         if policy.get("policyFile"):
#             try:
#                 temp_path = policy["policyFile"]
#                 # Extract filename from path
#                 filename = os.path.basename(temp_path)
#                 approved_path = f"approved_policies/{filename}"
                
#                 # Ensure directory exists
#                 os.makedirs("approved_policies", exist_ok=True)
                
#                 # Move the file
#                 if os.path.exists(temp_path):
#                     shutil.move(temp_path, approved_path)
#                     policies[i]["policyFile"] = approved_path
#             except Exception as e:
#                 # Log the error but continue with the approval process
#                 print(f"Error moving file for {country} policy {i}: {str(e)}")
#                 # Keep the original path if movement fails
#                 if os.path.exists(temp_path):
#                     policies[i]["policyFile"] = temp_path
#                 else:
#                     policies[i]["policyFile"] = None
                
#         # Mark this policy as approved if it has content
#         if policy.get("policyFile") or policy.get("policyDescription"):
#             policies[i]["status"] = "approved"
#             policies[i]["updatedAt"] = current_time
    
#     # Update the submission with new file paths and status
#     submission["policyInitiatives"] = policies
#     submission["updatedAt"] = current_time
    
#     try:
#         # Move submission to approved collection
#         approved_collection.insert_one(submission)
#         pending_collection.delete_one({"country": country})

#         # Update the CSV file
#         generate_policy_data_csv()
#         return {"message": f"Submission for {country} approved and added to the database"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# def create_empty_policy(index):
#     """Helper function to create an empty policy structure"""
#     return {
#         "policyName": f"{POLICY_TYPES[index] if index < len(POLICY_TYPES) else f'Policy {index+1}'} Policy",
#         "policyId": None,
#         "policyArea": POLICY_TYPES[index] if index < len(POLICY_TYPES) else f"Policy {index+1}",
#         "targetGroups": [],
#         "policyDescription": "",
#         "policyFile": None,
#         "policyLink": None,
#         "implementation": {
#             "yearlyBudget": None,
#             "budgetCurrency": "USD",
#             "privateSecFunding": False,
#             "deploymentYear": None
#         },
#         "evaluation": {
#             "isEvaluated": False,
#             "evaluationType": "internal",
#             "riskAssessment": False,
#             "transparencyScore": 0,
#             "explainabilityScore": 0,
#             "accountabilityScore": 0
#         },
#         "participation": {
#             "hasConsultation": False,
#             "consultationStartDate": None,
#             "consultationEndDate": None,
#             "commentsPublic": False,
#             "stakeholderScore": 0
#         },
#         "alignment": {
#             "aiPrinciples": [],
#             "humanRightsAlignment": False,
#             "environmentalConsiderations": False,
#             "internationalCooperation": False
#         },
#         "status": "pending",
#         "createdAt": datetime.now().isoformat(),
#         "updatedAt": datetime.now().isoformat(),
#         "adminNotes": ""
#     }

# @router.post("/decline-policy")
# def decline_policy(payload: dict = Body(...)):
#     """Decline a specific policy from a country's submission"""
#     country = payload.get("country")
#     policy_index = payload.get("policyIndex")
#     admin_notes = payload.get("adminNotes", "")
    
#     if country is None or policy_index is None:
#         raise HTTPException(status_code=400, detail="Country and policyIndex are required")
    
#     # Convert policy_index to integer if it's not already
#     policy_index = int(policy_index)
    
#     # Find the pending submission
#     submission = pending_collection.find_one({"country": country})
#     if not submission:
#         raise HTTPException(status_code=404, detail="Submission not found")
    
#     # Check if policy index is valid
#     if policy_index < 0 or policy_index >= len(submission.get("policyInitiatives", [])):
#         raise HTTPException(status_code=400, detail="Invalid policy index")
    
#     # Get the specific policy
#     policy = submission["policyInitiatives"][policy_index]
    
#     # Delete file if present
#     if policy.get("policyFile") and os.path.exists(policy["policyFile"]):
#         try:
#             os.remove(policy["policyFile"])
#         except Exception as e:
#             # Log the error but continue with the decline process
#             print(f"Error deleting file for {country} policy {policy_index}: {str(e)}")
#         # Set file path to None regardless of deletion success
#         policy["policyFile"] = None
    
#     # Update status and notes
#     policy["status"] = "declined"
#     if admin_notes:
#         policy["adminNotes"] = admin_notes
    
#     policy["updatedAt"] = datetime.now().isoformat()
#     submission["policyInitiatives"][policy_index] = policy
#     submission["updatedAt"] = datetime.now().isoformat()
    
#     try:
#         # Update in MongoDB
#         pending_collection.update_one(
#             {"country": country},
#             {"$set": {"policyInitiatives": submission["policyInitiatives"], "updatedAt": submission["updatedAt"]}}
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
#     return {"message": f"Policy {policy_index} for {country} declined"}

# @router.post("/remove-country")
# def remove_country(payload: dict = Body(...)):
#     """Remove a country from the pending submissions list"""
#     country = payload.get("country")
    
#     if country is None:
#         raise HTTPException(status_code=400, detail="Country is required")
    
#     # Find and delete the country from pending collection
#     result = pending_collection.delete_one({"country": country})
    
#     if result.deleted_count == 0:
#         # Country not found in pending collection
#         raise HTTPException(status_code=404, detail="Country not found in pending submissions")
    
#     return {"message": f"Country {country} removed from pending submissions"}

# @router.get("/rejected-submissions")
# def get_rejected_submissions(page: int = Query(0), per_page: int = Query(5)):
#     """Get a paginated list of rejected policy submissions"""
#     # Calculate skip amount
#     skip = page * per_page
    
#     # Query for submissions with at least one declined policy
#     query = {"policyInitiatives": {"$elemMatch": {"status": "declined"}}}
    
#     # Count total documents for pagination info
#     total_docs = pending_collection.count_documents(query)
#     total_pages = (total_docs + per_page - 1) // per_page  # Ceiling division
    
#     # Fetch rejected submissions from MongoDB with pagination
#     cursor = pending_collection.find(query, {"_id": 0}).skip(skip).limit(per_page)
#     submissions = list(cursor)
    
#     return {
#         "submissions": submissions,
#         "pagination": {
#             "current_page": page,
#             "total_pages": max(1, total_pages),
#             "total_count": total_docs,
#             "per_page": per_page
#         }
#     }

# @router.post("/add-approved-admin-notes")
# async def add_approved_admin_notes(
#     payload: dict = Body(...)
# ):
#     """Add or update admin notes for an approved policy"""
#     try:
#         country = payload.get("country")
#         policy_index = int(payload.get("policyIndex"))
#         notes = payload.get("notes", "")
        
#         # Find the approved submission
#         submission = approved_collection.find_one({"country": country})
#         if not submission:
#             raise HTTPException(status_code=404, detail="Approved submission not found")
        
#         # Check if policy index is valid
#         if policy_index < 0 or policy_index >= len(submission.get("policyInitiatives", [])):
#             raise HTTPException(status_code=400, detail="Invalid policy index")
        
#         # Update admin notes
#         submission["policyInitiatives"][policy_index]["adminNotes"] = notes
#         submission["policyInitiatives"][policy_index]["updatedAt"] = datetime.now().isoformat()
        
#         # Update in MongoDB
#         approved_collection.update_one(
#             {"country": country},
#             {"$set": {"policyInitiatives": submission["policyInitiatives"]}}
#         )
        
#         return {"message": "Admin notes updated successfully for approved policy"}
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid policy index format")
#     except Exception as e:
#         if "detail" not in str(e):  # Don't wrap HTTPExceptions
#             raise HTTPException(status_code=500, detail=f"Error updating admin notes: {str(e)}")
#         raise

# @router.post("/remove-submission")
# def remove_submission(payload: dict = Body(...)):
#     """Remove a country submission from the pending submissions list"""
#     country = payload.get("country")
    
#     if country is None:
#         raise HTTPException(status_code=400, detail="Country is required")
    
#     # Find the pending submission
#     submission = pending_collection.find_one({"country": country})
#     if not submission:
#         raise HTTPException(status_code=404, detail="Submission not found")
    
#     # Remove any uploaded files
#     for policy in submission.get("policyInitiatives", []):
#         if policy.get("policyFile") and os.path.exists(policy["policyFile"]):
#             try:
#                 os.remove(policy["policyFile"])
#             except Exception as e:
#                 # Log the error but continue with the removal process
#                 print(f"Error deleting file: {str(e)}")
    
#     # Delete from MongoDB
#     result = pending_collection.delete_one({"country": country})
    
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Failed to remove country submission")
    
#     return {"message": f"Submission for {country} removed successfully"}

# @router.get("/submission/{country}")
# async def get_submission_details(
#     country: str = Path(..., title="Country name", description="Name of the country to fetch details for")
# ):
#     """
#     Get detailed information about a specific country's submission
#     """
#     try:
#         # Find the submission
#         submission = pending_collection.find_one({"country": country})
#         if not submission:
#             raise HTTPException(status_code=404, detail=f"No submission found for country: {country}")
            
#         # Convert ObjectId to string for JSON serialization
#         submission["_id"] = str(submission["_id"])
        
#         return submission
        
#     except HTTPException as http_ex:
#         raise http_ex
#     except Exception as e:
#         logger.error(f"Error fetching submission details: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to fetch submission details: {str(e)}")

# @router.put("/submission/{country}/mark-read")
# async def mark_submission_as_read(
#     country: str = Path(..., title="Country name")
# ):
#     """
#     Mark a submission as read by admin
#     """
#     try:
#         # Find and update the submission
#         result = pending_collection.update_one(
#             {"country": country},
#             {"$set": {"isRead": True, "updatedAt": datetime.now().isoformat()}}
#         )
        
#         if result.matched_count == 0:
#             raise HTTPException(status_code=404, detail=f"No submission found for country: {country}")
            
#         return {"message": f"Submission for {country} marked as read", "status": "success"}
        
#     except HTTPException as http_ex:
#         raise http_ex
#     except Exception as e:
#         logger.error(f"Error marking submission as read: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to mark submission as read: {str(e)}")

# @router.put("/policy/update")
# async def update_policy(request: PolicyUpdateRequest = Body(...)):
#     """
#     Update a specific policy's text or status and add admin notes
#     """
#     try:
#         country = request.country
#         policy_index = request.policyIndex
#         new_text = request.text
#         status = request.status
        
#         # Validate inputs
#         if policy_index < 0 or policy_index >= 10:
#             raise HTTPException(status_code=400, detail="Policy index must be between 0 and 9")
            
#         # Find the submission
#         submission = pending_collection.find_one({"country": country})
#         if not submission:
#             raise HTTPException(status_code=404, detail=f"No submission found for country: {country}")
            
#         # Check if the policy exists
#         if policy_index >= len(submission.get("policyInitiatives", [])):
#             raise HTTPException(status_code=404, detail=f"Policy with index {policy_index} not found")
        
#         # Update fields in the policy
#         update_fields = {}
#         update_fields[f"policyInitiatives.{policy_index}.policyDescription"] = new_text
#         update_fields["updatedAt"] = datetime.now().isoformat()
        
#         # Update status if provided
#         if status:
#             update_fields[f"policyInitiatives.{policy_index}.status"] = status
        
#         # Update the policy
#         result = pending_collection.update_one(
#             {"country": country},
#             {"$set": update_fields}
#         )
        
#         if result.modified_count == 0:
#             return {"message": "No changes were made", "status": "info"}
            
#         return {"message": f"Policy {policy_index+1} for {country} updated successfully", "status": "success"}
        
#     except HTTPException as http_ex:
#         raise http_ex
#     except Exception as e:
#         logger.error(f"Error updating policy: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")

# @router.put("/policy/approve")
# async def approve_policy(request: PolicyApprovalRequest = Body(...)):
#     """
#     Approve a specific policy and move it to approved collection
#     """
#     try:
#         country = request.country
#         policy_index = request.policyIndex
#         admin_notes = request.text  # Admin notes/comments
        
#         # Find the submission
#         submission = pending_collection.find_one({"country": country})
#         if not submission:
#             raise HTTPException(status_code=404, detail=f"No submission found for country: {country}")
            
#         # Check if the policy exists
#         if policy_index >= len(submission.get("policyInitiatives", [])):
#             raise HTTPException(status_code=404, detail=f"Policy with index {policy_index} not found")
        
#         # Get the policy to approve
#         policies = submission.get("policyInitiatives", [])
#         policy = policies[policy_index]
        
#         # Update the policy status and admin notes
#         policy["status"] = "approved"
#         policy["adminNotes"] = admin_notes
#         policy["updatedAt"] = datetime.now().isoformat()
        
#         # Update in pending collection first
#         pending_collection.update_one(
#             {"country": country},
#             {"$set": {
#                 f"policyInitiatives.{policy_index}": policy,
#                 "updatedAt": datetime.now().isoformat()
#             }}
#         )
        
#         # Check if approved collection has an entry for this country
#         approved_submission = approved_collection.find_one({"country": country})
        
#         if approved_submission:
#             # Add/update this policy in the existing approved submission
#             approved_policies = approved_submission.get("policyInitiatives", [])
            
#             # Check if this policy already exists in approved collection
#             policy_exists = False
#             for i, existing_policy in enumerate(approved_policies):
#                 if existing_policy.get("policyId") == policy.get("policyId"):
#                     # Update existing policy
#                     approved_policies[i] = policy
#                     policy_exists = True
#                     break
                    
#             if not policy_exists:
#                 # Add this policy to approved policies
#                 approved_policies.append(policy)
                
#             # Update the approved collection
#             approved_collection.update_one(
#                 {"country": country},
#                 {"$set": {
#                     "policyInitiatives": approved_policies,
#                     "updatedAt": datetime.now().isoformat()
#                 }}
#             )
#         else:
#             # Create new entry in approved collection with just this policy
#             approved_collection.insert_one({
#                 "country": country,
#                 "policyInitiatives": [policy],
#                 "createdAt": datetime.now().isoformat(),
#                 "updatedAt": datetime.now().isoformat()
#             })
            
#         # Move any policy files if needed
#         if policy.get("policyFile"):
#             # Implementation would depend on file storage system
#             # Would copy file from temp_policies to approved_policies directory
#             pass
            
#         return {"message": f"Policy {policy_index+1} for {country} approved successfully", "status": "success"}
        
#     except HTTPException as http_ex:
#         raise http_ex
#     except Exception as e:
#         logger.error(f"Error approving policy: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to approve policy: {str(e)}")

# @router.put("/policy/decline")
# async def decline_policy(request: PolicyDeclineRequest = Body(...)):
#     """
#     Decline a specific policy with admin notes
#     """
#     try:
#         country = request.country
#         policy_index = request.policyIndex
#         admin_notes = request.text  # Reason for declining
        
#         # Find the submission
#         submission = pending_collection.find_one({"country": country})
#         if not submission:
#             raise HTTPException(status_code=404, detail=f"No submission found for country: {country}")
            
#         # Check if the policy exists
#         if policy_index >= len(submission.get("policyInitiatives", [])):
#             raise HTTPException(status_code=404, detail=f"Policy with index {policy_index} not found")
        
#         # Update the policy status and admin notes
#         update_fields = {
#             f"policyInitiatives.{policy_index}.status": "declined",
#             f"policyInitiatives.{policy_index}.adminNotes": admin_notes,
#             f"policyInitiatives.{policy_index}.updatedAt": datetime.now().isoformat(),
#             "updatedAt": datetime.now().isoformat()
#         }
        
#         # Update in pending collection
#         result = pending_collection.update_one(
#             {"country": country},
#             {"$set": update_fields}
#         )
        
#         if result.modified_count == 0:
#             return {"message": "No changes were made", "status": "info"}
            
#         return {"message": f"Policy {policy_index+1} for {country} declined with comments", "status": "success"}
        
#     except HTTPException as http_ex:
#         raise http_ex
#     except Exception as e:
#         logger.error(f"Error declining policy: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to decline policy: {str(e)}")

# @router.delete("/submission/{country}")
# async def remove_submission(
#     country: str = Path(..., title="Country name")
# ):
#     """
#     Remove an entire country submission
#     """
#     try:
#         # Find the submission first to check if it exists
#         submission = pending_collection.find_one({"country": country})
#         if not submission:
#             raise HTTPException(status_code=404, detail=f"No submission found for country: {country}")
            
#         # Delete any associated files
#         policies = submission.get("policyInitiatives", [])
#         for policy in policies:
#             if policy.get("policyFile"):
#                 file_path = policy["policyFile"]
#                 try:
#                     if os.path.exists(file_path):
#                         os.remove(file_path)
#                 except Exception as e:
#                     logger.warning(f"Failed to delete file {file_path}: {str(e)}")
        
#         # Delete the submission
#         result = pending_collection.delete_one({"country": country})
        
#         if result.deleted_count == 0:
#             return {"message": "No submission was deleted", "status": "info"}
            
#         return {"message": f"Submission for {country} removed successfully", "status": "success"}
        
#     except HTTPException as http_ex:
#         raise http_ex
#     except Exception as e:
#         logger.error(f"Error removing submission: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to remove submission: {str(e)}")