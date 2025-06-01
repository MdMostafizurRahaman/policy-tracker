from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
from typing import Dict

from ..services.export_service import generate_country_data, generate_csv_data
from ..database.connection import get_db

router = APIRouter(prefix="/api", tags=["export"])

@router.get("/generate-country-data")
async def get_country_data(db=Depends(get_db)):
    try:
        country_data = await generate_country_data(db.master_policies)
        policy_types = [
            "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
            "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
            "Physical Health", "Social Media/Gaming Regulation"
        ]
        csv_data = generate_csv_data(country_data, policy_types)
        
        return {
            "success": True,
            "countries": country_data,
            "csv_data": csv_data,
            "total_countries": len(country_data),
            "policy_types": policy_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/countries")
async def get_countries(db=Depends(get_db)):
    try:
        country_data = await generate_country_data(db.master_policies)
        return country_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/country-policies/{country_name}")
async def get_country_policies(country_name: str, db=Depends(get_db)):
    try:
        policy_types = [
            "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
            "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
            "Physical Health", "Social Media/Gaming Regulation"
        ]
        
        policies = [{"status": "not_approved"} for _ in range(10)]
        
        cursor = db.master_policies.find({
            "country": country_name,
            "master_status": {"$ne": "deleted"}
        })
        
        async for policy in cursor:
            policy_area = policy.get("policyArea")
            if policy_area and policy_area in policy_types:
                policy_index = policy_types.index(policy_area)
                policies[policy_index] = {
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
                    ],
                    "policy_name": policy.get("policyName", ""),
                    "target_groups": policy.get("targetGroups", []),
                    "policy_link": policy.get("policyLink", ""),
                    "ai_principles": policy.get("alignment", {}).get("aiPrinciples", []),
                    "human_rights_alignment": policy.get("alignment", {}).get("humanRightsAlignment", False),
                    "environmental_considerations": policy.get("alignment", {}).get("environmentalConsiderations", False),
                    "international_cooperation": policy.get("alignment", {}).get("internationalCooperation", False),
                    "has_consultation": policy.get("participation", {}).get("hasConsultation", False),
                    "is_evaluated": policy.get("evaluation", {}).get("isEvaluated", False),
                    "risk_assessment": policy.get("evaluation", {}).get("riskAssessment", False)
                }
        
        return {
            "country": country_name,
            "policies": policies,
            "policy_types": policy_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export-csv")
async def export_country_csv(db=Depends(get_db)):
    try:
        country_data = await generate_country_data(db.master_policies)
        policy_types = [
            "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
            "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
            "Physical Health", "Social Media/Gaming Regulation"
        ]
        csv_content = generate_csv_data(country_data, policy_types)
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=country_policies.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))