from fastapi import FastAPI, Form, HTTPException, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import shutil
import csv

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient("mongodb+srv://bsse1320:dC5zofg6ysfspCKA@cluster0.uwlupqg.mongodb.net/")
db = client["policy_tracker"]
pending_collection = db["pending_submissions"]
approved_collection = db["approved_policies"]

@app.post("/api/submit-policy")
async def submit_policy(
    country: str = Form(...),
    policy_1_file: UploadFile = None, policy_1_text: str = Form(None),
    policy_2_file: UploadFile = None, policy_2_text: str = Form(None),
    policy_3_file: UploadFile = None, policy_3_text: str = Form(None),
    policy_4_file: UploadFile = None, policy_4_text: str = Form(None),
    policy_5_file: UploadFile = None, policy_5_text: str = Form(None),
    policy_6_file: UploadFile = None, policy_6_text: str = Form(None),
    policy_7_file: UploadFile = None, policy_7_text: str = Form(None),
    policy_8_file: UploadFile = None, policy_8_text: str = Form(None),
    policy_9_file: UploadFile = None, policy_9_text: str = Form(None),
    policy_10_file: UploadFile = None, policy_10_text: str = Form(None),
):
    # Save uploaded files or text inputs
    os.makedirs("temp_policies", exist_ok=True)
    policies = []
    for i, (file, text) in enumerate([
        (policy_1_file, policy_1_text), (policy_2_file, policy_2_text),
        (policy_3_file, policy_3_text), (policy_4_file, policy_4_text),
        (policy_5_file, policy_5_text), (policy_6_file, policy_6_text),
        (policy_7_file, policy_7_text), (policy_8_file, policy_8_text),
        (policy_9_file, policy_9_text), (policy_10_file, policy_10_text),
    ]):
        if file:
            file_path = f"temp_policies/{country}_policy_{i + 1}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            policies.append({"file": file_path, "text": None})
        elif text:
            policies.append({"file": None, "text": text})
        else:
            policies.append({"file": None, "text": None})

    # Store submission in MongoDB
    pending_submission = {"country": country, "policies": policies}
    pending_collection.insert_one(pending_submission)
    return {"message": "Submission received and pending approval"}

@app.get("/api/pending-submissions")
def get_pending_submissions():
    # Fetch pending submissions from MongoDB
    submissions = list(pending_collection.find({}, {"_id": 0}))
    return submissions

@app.post("/api/approve-submission")
def approve_submission(payload: dict = Body(...)):
    country = payload.get("country")
    if not country:
        raise HTTPException(status_code=400, detail="Country is required")

    # Find the pending submission
    submission = pending_collection.find_one({"country": country})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Move submission to approved collection
    approved_collection.insert_one(submission)
    pending_collection.delete_one({"country": country})

    # Update the CSV file
    generate_policy_data_csv()
    return {"message": f"Submission for {country} approved and added to the database"}

@app.get("/api/countries")
def get_all_countries():
    # Fetch all approved policies from MongoDB
    approved_policies = list(approved_collection.find({}, {"_id": 0}))
    
    # Transform the data into the required format
    countries = {}
    for policy in approved_policies:
        country = policy["country"]
        total_policies = sum(1 for p in policy["policies"] if p["file"] or p["text"])
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
                row.append(1 if p["file"] or p["text"] else 0)
            writer.writerow(row)