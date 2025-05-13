from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import csv
from datetime import datetime
from database import approved_collection
from models import POLICY_TYPES

router = APIRouter(prefix="/api", tags=["utilities"])

def generate_policy_data_csv():
    """Generate CSV file with policy data from approved submissions"""
    try:
        # Get all approved submissions
        approved_submissions = list(approved_collection.find({}, {"_id": 0}))
        
        # Prepare CSV data
        csv_data = []
        csv_headers = ["Country", "Policy Area", "Policy Name", "Status", "Last Updated", "Has File"]
        
        for submission in approved_submissions:
            country = submission.get("country", "Unknown")
            
            for policy in submission.get("policyInitiatives", []):
                if policy.get("status") == "approved":
                    csv_data.append({
                        "Country": country,
                        "Policy Area": policy.get("policyArea", "Unknown"),
                        "Policy Name": policy.get("policyName", "Unnamed Policy"),
                        "Status": policy.get("status", "Unknown"),
                        "Last Updated": policy.get("updatedAt", datetime.now().isoformat()),
                        "Has File": "Yes" if policy.get("policyFile") else "No"
                    })
        
        # Write CSV file
        os.makedirs("exports", exist_ok=True)
        csv_path = "exports/policy_data.csv"
        
        with open(csv_path, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(csv_data)
        
        return csv_path
        
    except Exception as e:
        print(f"Error generating CSV: {str(e)}")
        return None

@router.get("/export-csv")
def export_csv():
    """Generate and download a CSV export of all approved policies"""
    try:
        csv_path = generate_policy_data_csv()
        
        if not csv_path or not os.path.exists(csv_path):
            raise HTTPException(status_code=500, detail="Failed to generate CSV export")
        
        # Return the file as a download
        return FileResponse(
            path=csv_path, 
            filename="policy_data.csv",
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")

def ensure_directories():
    """Ensure all required directories exist"""
    directories = ["temp_policies", "approved_policies", "exports"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    return True

@router.get("/policy-file/{filename}")
async def get_policy_file(filename: str):
    """Serve policy files from either temp or approved directories"""
    # First check in the approved directory
    approved_path = f"approved_policies/{filename}"
    if os.path.exists(approved_path):
        return FileResponse(approved_path)
    
    # Then check in the temp directory
    temp_path = f"temp_policies/{filename}"
    if os.path.exists(temp_path):
        return FileResponse(temp_path)
    
    # If not found in either location
    raise HTTPException(status_code=404, detail="Policy file not found")

@router.get("/download-csv")
def download_policy_data_csv():
    """Generate and download the policy data CSV file"""
    ensure_directories()
    csv_path = generate_policy_data_csv()
    if csv_path and os.path.exists(csv_path):
        return FileResponse(
            path=csv_path,
            filename="policy_data.csv",
            media_type="text/csv"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to generate CSV file")