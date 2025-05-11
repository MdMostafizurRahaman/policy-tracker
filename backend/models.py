from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Policy types for reference
POLICY_TYPES = [
    "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
    "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
    "Physical Health", "Social Media/Gaming Regulation"
]

class Metric(BaseModel):
    name: str
    value: Any

class Policy(BaseModel):
    file: Optional[str] = None
    text: Optional[str] = None
    status: str = "pending"
    type: str
    year: str = "N/A"
    description: str = ""
    metrics: List[Dict[str, Any]] = []

class CountrySubmission(BaseModel):
    country: str
    policies: List[Policy]

class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    total_count: int
    per_page: int

class SubmissionsResponse(BaseModel):
    submissions: List[Dict[str, Any]]
    pagination: PaginationInfo