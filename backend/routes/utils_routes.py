from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from utils import generate_policy_data_csv

router = APIRouter(prefix="/api", tags=["utilities"])

@router.get("/policy-file/{filename}")
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

@router.get("/download-csv")
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