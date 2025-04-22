from fastapi import FastAPI, Form, HTTPException, UploadFile, Body, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
import os
import shutil
import csv
from typing import Optional, List

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient("mongodb+srv://bsse1320:bsse1320@cluster0.xpk6lau.mongodb.net/")
db = client["policy_tracker"]
pending_collection = db["pending_submissions"]
approved_collection = db["approved_policies"]

# Create directories for storing files
os.makedirs("temp_policies", exist_ok=True)
os.makedirs("approved_policies", exist_ok=True)

# Mount static files directory for direct access
app.mount("/files", StaticFiles(directory="temp_policies"), name="policy_files")


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
        policy_data = {"file": None, "text": None, "status": "pending"}
        
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

    # Store submission in MongoDB
    pending_submission = {"country": country, "policies": policies}
    pending_collection.insert_one(pending_submission)
    return {"message": "Submission received and pending approval"}


@app.get("/api/pending-submissions")
def get_pending_submissions():
    # Fetch pending submissions from MongoDB
    submissions = list(pending_collection.find({}, {"_id": 0}))
    return submissions


@app.post("/api/approve-policy")
def approve_policy(payload: dict = Body(...)):
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
        approved_path = f"approved_policies/{filename}"
        
        if os.path.exists(temp_path):
            # Copy instead of move, so we keep the original
            shutil.copy(temp_path, approved_path)
            policy["file"] = approved_path
    
    # Mark this policy as approved
    policy["status"] = "approved"
    
    # Update the policy in the submission
    submission["policies"][policy_index] = policy
    
    # Update in MongoDB
    pending_collection.update_one(
        {"country": country},
        {"$set": {"policies": submission["policies"]}}
    )
    
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
            "policies": [{"file": None, "text": None, "status": "pending"} for _ in range(10)]
        }
        new_approved["policies"][policy_index] = policy
        approved_collection.insert_one(new_approved)
    
    # Update the CSV file
    generate_policy_data_csv()
    
    return {"message": f"Policy {policy_index} for {country} approved"}


@app.post("/api/decline-policy")
def decline_policy(payload: dict = Body(...)):
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
    policy = {"file": None, "text": None, "status": "declined"}
    submission["policies"][policy_index] = policy
    
    # Update in MongoDB
    pending_collection.update_one(
        {"country": country},
        {"$set": {"policies": submission["policies"]}}
    )
    
    return {"message": f"Policy {policy_index} for {country} declined"}


@app.post("/api/approve-submission")
def approve_submission(payload: dict = Body(...)):
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
    
    # Update the submission with new file paths
    submission["policies"] = policies
    
    # Move submission to approved collection
    approved_collection.insert_one(submission)
    pending_collection.delete_one({"country": country})

    # Update the CSV file
    generate_policy_data_csv()
    return {"message": f"Submission for {country} approved and added to the database"}


@app.get("/api/policy-file/{filename}")
def get_policy_file(filename: str):
    # Check in temp policies first
    temp_path = f"temp_policies/{filename}"
    if os.path.exists(temp_path):
        return FileResponse(temp_path)
    
    # Then check in approved policies
    approved_path = f"approved_policies/{filename}"
    if os.path.exists(approved_path):
        return FileResponse(approved_path)
    
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/countries")
def get_all_countries():
    # Fetch all approved policies from MongoDB
    approved_policies = list(approved_collection.find({}, {"_id": 0}))
    
    # Transform the data into the required format
    countries = {}
    for policy in approved_policies:
        country = policy["country"]
        total_policies = sum(1 for p in policy["policies"] if (p["file"] or p["text"]) and p.get("status") == "approved")
        color = "#FF0000" if total_policies <= 3 else "#FFD700" if total_policies <= 7 else "#00AA00"
        countries[country] = {
            "total_policies": total_policies,
            "color": color
        }
    
    return countries


def generate_policy_data_csv():
    # Fetch all approved policies
    approved_policies = list(approved_collection.find({}, {"_id": 0}))

    # Define CSV headers
    headers = [
        "Country", "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
        "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
        "Physical Health", "Social Media/Gaming Regulation"
    ]

    # Write to CSV file
    with open("policy_data.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for policy in approved_policies:
            row = [policy["country"]]
            for p in policy["policies"]:
                # Only count policies that are explicitly approved
                row.append(1 if (p["file"] or p["text"]) and p.get("status") == "approved" else 0)
            writer.writerow(row)