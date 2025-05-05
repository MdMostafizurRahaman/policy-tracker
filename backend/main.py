from fastapi import FastAPI, Form, HTTPException, UploadFile, Body, File, Query, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
import os
import shutil
import csv
from datetime import datetime
from typing import Optional, List

app = FastAPI()

# CORS configuration - FIX: Specific origin instead of wildcard when using credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific Next.js frontend URL instead of "*"
    allow_credentials=True,                   # Support credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rest of your FastAPI code...
# MongoDB connection
# For local development, use:
# client = MongoClient("mongodb://localhost:27017/")
# For production, use connection string:
client = MongoClient("mongodb+srv://bsse1320:bsse1320@cluster0.xpk6lau.mongodb.net/")
db = client["policy_tracker"]
pending_collection = db["pending_submissions"]
approved_collection = db["approved_policies"]

# Create directories for storing files
os.makedirs("temp_policies", exist_ok=True)
os.makedirs("approved_policies", exist_ok=True)

# Mount static directories for policy files
app.mount("/files", StaticFiles(directory="temp_policies"), name="temp_policy_files")
app.mount("/approved", StaticFiles(directory="approved_policies"), name="approved_policy_files")

# Policy types for reference
POLICY_TYPES = [
    "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
    "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
    "Physical Health", "Social Media/Gaming Regulation"
]

@app.post("/api/submit-policy")
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


@app.get("/api/pending-submissions")
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


@app.post("/api/approve-policy")
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


@app.post("/api/decline-policy")
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


@app.post("/api/approve-submission")
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


@app.post("/api/remove-country")
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


@app.get("/api/policy-file/{filename}")
def get_policy_file(filename: str):
    """Retrieve a policy file from either temp or approved directories"""
    # Check in temp directory first
    temp_path = f"temp_policies/{filename}"
    if os.path.exists(temp_path):
        return FileResponse(temp_path)
    
    # Check in approved directory next
    approved_path = f"approved_policies/{filename}"
    if os.path.exists(approved_path):
        return FileResponse(approved_path)
    
    # If file not found in either directory
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/countries")
def get_all_countries():
    """Get a list of all countries with policy data and color-coding"""
    # Fetch all approved policies from MongoDB
    approved_policies = list(approved_collection.find({}, {"_id": 0}))
    
    # Transform the data into the required format
    countries = {}
    for policy in approved_policies:
        country = policy["country"]
        total_policies = sum(1 for p in policy["policies"] if (p["file"] or p["text"]) and p.get("status") == "approved")
        
        # Color code based on number of approved policies
        color = "#FF0000" if total_policies <= 3 else "#FFD700" if total_policies <= 7 else "#00AA00"
        
        countries[country] = {
            "total_policies": total_policies,
            "color": color
        }
    
    return countries


@app.get("/api/country-policies/{country_name}")
def get_country_policies(country_name: str):
    """Get detailed policy information for a specific country"""
    # Fetch the country's policies from approved collection
    country_data = approved_collection.find_one({"country": country_name})
    
    # If not found, check the pending collection as fallback
    if not country_data:
        country_data = pending_collection.find_one({"country": country_name})
        
    # If still not found, return 404
    if not country_data:
        raise HTTPException(status_code=404, detail=f"No policy data found for {country_name}")
    
    # Format the response by removing MongoDB _id field
    if "_id" in country_data:
        country_data.pop("_id")
        
    # Ensure each policy has proper metadata
    for i, policy in enumerate(country_data["policies"]):
        if i < len(POLICY_TYPES) and "type" not in policy:
            policy["type"] = POLICY_TYPES[i]
            
        # Ensure we have default fields even if they're empty
        policy.setdefault("year", "N/A")
        policy.setdefault("description", "")
        policy.setdefault("metrics", [])
    
    return country_data


@app.get("/api/download-csv")
def download_policy_data_csv():
    """Generate and download the policy data CSV file"""
    csv_path = generate_policy_data_csv()
    if csv_path and os.path.exists(csv_path):
        return FileResponse(
            path=csv_path,
            filename="policy_data.csv",
            media_type="text/csv"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to generate CSV file")


def generate_policy_data_csv():
    """Generate a CSV file with all approved policies data"""
    try:
        # Get all approved policies
        approved_policies = list(approved_collection.find({}, {"_id": 0}))
        
        # Create CSV file with timestamp to avoid caching issues
        csv_path = f"policy_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Define CSV headers based on policy types
            fieldnames = ['country'] + POLICY_TYPES
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Write data for each country
            for country_data in approved_policies:
                country = country_data.get('country', 'Unknown')
                row = {'country': country}
                
                # Map each policy to its corresponding type
                for i, policy in enumerate(country_data.get('policies', [])):
                    if i < len(POLICY_TYPES):
                        policy_type = POLICY_TYPES[i]
                        # Mark as 1 if approved policy exists, 0 otherwise
                        has_policy = 1 if (policy.get('file') or policy.get('text')) and policy.get('status') == 'approved' else 0
                        row[policy_type] = has_policy
                
                writer.writerow(row)
        
        return csv_path
    except Exception as e:
        print(f"Error generating CSV: {str(e)}")
        return None


if __name__ == "__main__":
    import uvicorn
    # Create directories if they don't exist
    os.makedirs("temp_policies", exist_ok=True)
    os.makedirs("approved_policies", exist_ok=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)