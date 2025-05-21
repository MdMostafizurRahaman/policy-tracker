from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime
import os
import motor.motor_asyncio
import shutil
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(title="AI Policy Database API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get MongoDB connection string from environment variables
MONGODB_URL = os.getenv("MONGO_URI")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL environment variable is not set")

# Connect to MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.ai_policy_database
policies_collection = db.policies

# Pydantic Models for validating request data
class PolicyFile(BaseModel):
    name: str
    path: str
    size: int
    type: str
    localOnly: Optional[bool]
    uploadFailed: Optional[bool]

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
    policyFile: Optional[PolicyFile]
    policyLink: str = ""
    implementation: Implementation
    evaluation: Evaluation
    participation: Participation
    alignment: Alignment

    @validator('policyName')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Policy name must not be empty')
        return v

class FormSubmission(BaseModel):
    country: str
    policyInitiatives: List[PolicyInitiative]

    @validator('country')
    def country_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Country name must not be empty')
        return v

    @validator('policyInitiatives')
    def must_have_at_least_one_policy(cls, v):
        if not v or not v[0].policyName.strip():
            raise ValueError('At least one policy initiative must be provided')
        return v

# Helper function to sanitize filenames
def sanitize_filename(filename: str) -> str:
    """Sanitize filename to avoid potential security issues"""
    # Get the filename without extension and the extension
    name, ext = os.path.splitext(filename)
    
    # Generate a UUID for uniqueness
    unique_id = str(uuid.uuid4())[:8]
    
    # Create a safe filename with the original extension
    safe_name = f"{name.replace(' ', '_')}_{unique_id}{ext}"
    
    return safe_name

@app.post("/api/upload-policy-file")
async def upload_policy_file(
    country: str = Form(...),
    policy_index: int = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Create country-specific directory
        country_dir = UPLOAD_DIR / country.replace(" ", "_")
        country_dir.mkdir(exist_ok=True)
        
        # Sanitize filename and prepare path
        safe_filename = sanitize_filename(file.filename)
        file_path = country_dir / safe_filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return the relative file path
        return {"success": True, "file_path": str(file_path.relative_to(UPLOAD_DIR))}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/api/submit-form")
async def submit_form(submission: FormSubmission):
    try:
        # Add timestamps
        submission_dict = submission.dict()
        submission_dict["created_at"] = datetime.utcnow()
        submission_dict["updated_at"] = datetime.utcnow()
        
        # Insert into MongoDB
        result = await policies_collection.insert_one(submission_dict)
        
        if result.inserted_id:
            return {"success": True, "message": "Form submitted successfully", "id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Failed to insert data into database")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Form submission failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI Policy Database API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)