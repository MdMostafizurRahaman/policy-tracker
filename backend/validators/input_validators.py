"""
Input Validation Utilities
Custom validators for data validation beyond Pydantic
"""
import re
from typing import List, Dict, Any
from fastapi import HTTPException

def validate_email_format(email: str) -> bool:
    """Validate email format using regex"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return detailed feedback"""
    result = {
        "valid": True,
        "score": 0,
        "feedback": []
    }
    
    if len(password) < 8:
        result["valid"] = False
        result["feedback"].append("Password must be at least 8 characters long")
    else:
        result["score"] += 2
    
    if re.search(r'[A-Z]', password):
        result["score"] += 1
    else:
        result["feedback"].append("Include at least one uppercase letter")
    
    if re.search(r'[a-z]', password):
        result["score"] += 1
    else:
        result["feedback"].append("Include at least one lowercase letter")
    
    if re.search(r'\d', password):
        result["score"] += 1
    else:
        result["feedback"].append("Include at least one number")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["score"] += 1
        result["feedback"].append("Strong: includes special characters")
    
    if result["score"] < 3:
        result["valid"] = False
    
    return result

def validate_policy_submission(submission_data: Dict[str, Any]) -> List[str]:
    """Validate policy submission data"""
    errors = []
    
    if not submission_data.get("country"):
        errors.append("Country is required")
    
    policy_areas = submission_data.get("policyAreas", [])
    if not policy_areas:
        errors.append("At least one policy area is required")
    
    for i, area in enumerate(policy_areas):
        if not area.get("area_id"):
            errors.append(f"Policy area {i+1}: area_id is required")
        
        policies = area.get("policies", [])
        for j, policy in enumerate(policies):
            if not policy.get("policyName", "").strip():
                errors.append(f"Policy area {i+1}, policy {j+1}: Policy name is required")
    
    return errors

def validate_file_upload(filename: str, file_size: int, allowed_extensions: List[str] = None) -> List[str]:
    """Validate file upload"""
    errors = []
    
    if not filename:
        errors.append("Filename is required")
        return errors
    
    # Check file extension
    if allowed_extensions:
        file_extension = filename.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            errors.append(f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    # Check file size (default 10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        errors.append(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)")
    
    return errors

def sanitize_input(text: str) -> str:
    """Sanitize text input to prevent XSS and other attacks"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text

