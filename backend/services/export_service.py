import csv
import io
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

async def generate_country_data(master_collection: AsyncIOMotorCollection) -> Dict:
    try:
        policy_types = [
            "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
            "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
            "Physical Health", "Social Media/Gaming Regulation"
        ]
        
        cursor = master_collection.find({"master_status": {"$ne": "deleted"}})
        country_data = defaultdict(lambda: {
            "policies": [{"status": "not_approved"} for _ in range(10)],
            "total_policies": 0,
            "color": "#EEE"
        })
        
        async for policy in cursor:
            country = policy.get("country")
            policy_area = policy.get("policyArea")
            
            if country and policy_area and policy_area in policy_types:
                policy_index = policy_types.index(policy_area)
                country_data[country]["policies"][policy_index] = {
                    "status": "approved",
                    "file": policy.get("policyFile", {}).get("file_id") if policy.get("policyFile") else None,
                    "text": policy.get("policyDescription", ""),
                    "year": policy.get("implementation", {}).get("deploymentYear", "N/A"),
                    "description": policy.get("policyDescription", ""),
                    "metrics": [
                        f"Budget: {policy.get('implementation', {}).get('yearlyBudget', 'N/A')} {policy.get('implementation', {}).get('budgetCurrency', 'USD')}",
                        f"Transparency Score: {policy.get('evaluation', {}).get('transparencyScore', 0)}/10",
                        f"Accountability Score: {policy.get('evaluation', {}).get('accountabilityScore', 0)}/10",
                        f"Stakeholder Score: {policy.get('participation', {}).get('stakeholderScore', 0)}/10"
                    ]
                }
        
        for country, data in country_data.items():
            approved_count = sum(1 for p in data["policies"] if p["status"] == "approved")
            data["total_policies"] = approved_count
            
            if approved_count >= 8:
                data["color"] = "#22c55e"
            elif approved_count >= 4:
                data["color"] = "#eab308"
            elif approved_count >= 1:
                data["color"] = "#ef4444"
        
        return dict(country_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating country data: {str(e)}")

def generate_csv_data(country_data: Dict, policy_types: List[str]) -> str:
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        header = ["Country", "Total_Policies", "Color"] + policy_types
        writer.writerow(header)
        
        for country, data in country_data.items():
            row = [
                country,
                data["total_policies"],
                data["color"]
            ]
            row.extend(1 if p["status"] == "approved" else 0 for p in data["policies"])
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        return csv_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")