from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
from datetime import datetime

# Import routers from route modules
from routes import pending_routes, approved_routes, utils_routes
from routes.utils_routes import ensure_directories
from database import pending_collection

# Create FastAPI application
app = FastAPI()

# Configure CORS with expanded origins list
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,                  
    allow_methods=["*"],           
    allow_headers=["*"],              
)

# Ensure required directories exist
ensure_directories()

os.makedirs("temp_policies", exist_ok=True)
os.makedirs("approved_policies", exist_ok=True)

# Include routers from different modules
app.include_router(pending_routes.router)
app.include_router(approved_routes.router)
app.include_router(utils_routes.router)

# Special route to handle the form submission directly
@app.post("/api/submit-form")
async def submit_form(request: Request):
    try:
        # Get JSON data from request
        form_data = await request.json()
        
        # Extract country name
        country = form_data.get("country", "")
        if not country:
            return {"success": False, "message": "Country name is required"}
        
        # Extract policy initiatives and filter out empty ones
        policy_initiatives = form_data.get("policyInitiatives", [])
        valid_policies = []
        
        for policy in policy_initiatives:
            # Skip policies without names
            if not policy.get("policyName"):
                continue
                
            # Convert file object to metadata only (actual file upload would need to be handled separately)
            if policy.get("policyFile") and not isinstance(policy["policyFile"], dict):
                policy["policyFile"] = None
                
            # Ensure all nested objects exist
            if "implementation" not in policy:
                policy["implementation"] = {}
            if "evaluation" not in policy:
                policy["evaluation"] = {}
            if "participation" not in policy:
                policy["participation"] = {}
            if "alignment" not in policy:
                policy["alignment"] = {}
                
            policy["status"] = "pending"
            valid_policies.append(policy)
        
        # Skip if no valid policies
        if not valid_policies:
            return {"success": False, "message": "No valid policy entries found"}
            
        # Prepare the document to insert/update
        now = datetime.now().isoformat()
        submission_doc = {
            "country": country,
            "policyInitiatives": valid_policies,
            "updatedAt": now
        }
        
        # Check if country already exists
        existing = pending_collection.find_one({"country": country})
        if existing:
            # Update existing
            pending_collection.update_one(
                {"country": country},
                {"$set": {
                    "policyInitiatives": valid_policies,
                    "updatedAt": now
                }}
            )
        else:
            # Insert new
            submission_doc["createdAt"] = now
            pending_collection.insert_one(submission_doc)
            
        return {"success": True, "message": "Form data submitted successfully"}
        
    except Exception as e:
        print(f"Error processing form submission: {str(e)}")
        return {"success": False, "message": f"Error processing submission: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)