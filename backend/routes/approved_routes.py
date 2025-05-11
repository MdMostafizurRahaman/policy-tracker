from fastapi import APIRouter, Query, HTTPException
from database import approved_collection, pending_collection
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api", tags=["approved_policies"])

@router.get("/approved-submissions")
def get_approved_submissions(page: int = Query(0), per_page: int = Query(5)):
    """Get a paginated list of approved policy submissions"""
    # Calculate skip amount
    skip = page * per_page
    
    # Count total documents for pagination info
    total_docs = approved_collection.count_documents({})
    total_pages = (total_docs + per_page - 1) // per_page  # Ceiling division
    
    # Fetch approved submissions from MongoDB with pagination
    cursor = approved_collection.find({}, {"_id": 0}).skip(skip).limit(per_page)
    submissions = list(cursor)
    
    return {
        "submissions": submissions,
        "pagination": {
            "current_page": page,
            "total_pages": max(1, total_pages),
            "total_count": total_docs,
            "per_page": per_page
        }
    }

@router.get("/countries")
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

@router.get("/country-policies/{country_name}")
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
    from models import POLICY_TYPES
    for i, policy in enumerate(country_data["policies"]):
        if i < len(POLICY_TYPES) and "type" not in policy:
            policy["type"] = POLICY_TYPES[i]
            
        # Ensure we have default fields even if they're empty
        policy.setdefault("year", "N/A")
        policy.setdefault("description", "")
        policy.setdefault("metrics", [])
    
    return country_data