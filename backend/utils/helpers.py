"""
Helper utility functions.
"""
import random
import string
from datetime import datetime
from typing import Any, Dict, List
from bson import ObjectId

def convert_objectid(obj: Any) -> Any:
    """Convert ObjectId to string recursively"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

def pydantic_to_dict(obj: Any) -> Any:
    """Convert Pydantic model to dict recursively"""
    if hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, dict):
        return {key: pydantic_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [pydantic_to_dict(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj
    else:
        return obj

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def calculate_policy_score(policy: dict) -> int:
    """Calculate policy completeness score (0-100)"""
    score = 0
    
    # Basic info (30 points)
    if policy.get("policyName"):
        score += 10
    if policy.get("policyId"):
        score += 5
    if policy.get("policyDescription"):
        score += 15
    
    # Implementation details (25 points)
    impl = policy.get("implementation", {})
    if impl.get("yearlyBudget"):
        score += 10
    if impl.get("deploymentYear"):
        score += 5
    if impl.get("budgetCurrency"):
        score += 5
    if impl.get("privateSecFunding") is not None:
        score += 5
    
    # Evaluation (20 points)
    eval_data = policy.get("evaluation", {})
    if eval_data.get("isEvaluated"):
        score += 10
        if eval_data.get("evaluationType"):
            score += 5
        if eval_data.get("riskAssessment"):
            score += 5
    
    # Participation (15 points)
    part = policy.get("participation", {})
    if part.get("hasConsultation"):
        score += 10
        if part.get("consultationStartDate"):
            score += 3
        if part.get("commentsPublic"):
            score += 2
    
    # Alignment (10 points)
    align = policy.get("alignment", {})
    if align.get("aiPrinciples"):
        score += 5
    if align.get("humanRightsAlignment"):
        score += 3
    if align.get("internationalCooperation"):
        score += 2
    
    return min(score, 100)

def calculate_completeness_score(policy: dict) -> str:
    """Calculate policy completeness level"""
    score = calculate_policy_score(policy)
    
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "fair"
    else:
        return "basic"
