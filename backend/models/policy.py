"""
Policy Models and Schemas
Pydantic models for policy-related operations
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

# Enhanced Policy Areas Configuration
POLICY_AREAS = [
    {
        "id": "ai-safety",
        "name": "AI Safety",
        "description": "Policies ensuring AI systems are safe and beneficial",
        "icon": "🛡️",
        "color": "from-red-500 to-pink-600",
        "gradient": "bg-gradient-to-r from-red-500 to-pink-600"
    },
    {
        "id": "cyber-safety",
        "name": "CyberSafety", 
        "description": "Cybersecurity and digital safety policies",
        "icon": "🔒",
        "color": "from-blue-500 to-cyan-600",
        "gradient": "bg-gradient-to-r from-blue-500 to-cyan-600"
    },
    {
        "id": "digital-education",
        "name": "Digital Education",
        "description": "Educational technology and digital literacy policies",
        "icon": "🎓",
        "color": "from-green-500 to-emerald-600",
        "gradient": "bg-gradient-to-r from-green-500 to-emerald-600"
    },
    {
        "id": "digital-inclusion",
        "name": "Digital Inclusion",
        "description": "Bridging the digital divide and ensuring equal access",
        "icon": "🌐",
        "color": "from-purple-500 to-indigo-600",
        "gradient": "bg-gradient-to-r from-purple-500 to-indigo-600"
    },
    {
        "id": "digital-leisure",
        "name": "Digital Leisure",
        "description": "Gaming, entertainment, and digital recreation policies",
        "icon": "🎮",
        "color": "from-yellow-500 to-orange-600",
        "gradient": "bg-gradient-to-r from-yellow-500 to-orange-600"
    },
    {
        "id": "disinformation",
        "name": "(Dis)Information",
        "description": "Combating misinformation and promoting truth",
        "icon": "📰",
        "color": "from-gray-500 to-slate-600",
        "gradient": "bg-gradient-to-r from-gray-500 to-slate-600"
    },
    {
        "id": "digital-work",
        "name": "Digital Work",
        "description": "Future of work and digital employment policies",
        "icon": "💼",
        "color": "from-teal-500 to-blue-600",
        "gradient": "bg-gradient-to-r from-teal-500 to-blue-600"
    },
    {
        "id": "mental-health",
        "name": "Mental Health",
        "description": "Digital wellness and mental health policies",
        "icon": "🧠",
        "color": "from-pink-500 to-rose-600",
        "gradient": "bg-gradient-to-r from-pink-500 to-rose-600"
    },
    {
        "id": "physical-health",
        "name": "Physical Health",
        "description": "Healthcare technology and physical wellness policies",
        "icon": "❤️",
        "color": "from-emerald-500 to-green-600",
        "gradient": "bg-gradient-to-r from-emerald-500 to-green-600"
    },
    {
        "id": "social-media-gaming",
        "name": "Social Media/Gaming Regulation",
        "description": "Social media platforms and gaming regulation",
        "icon": "📱",
        "color": "from-indigo-500 to-purple-600",
        "gradient": "bg-gradient-to-r from-indigo-500 to-purple-600"
    }
]

class SubPolicy(BaseModel):
    policyName: str = ""
    policyId: str = ""
    policyDescription: str = ""
    targetGroups: List[str] = []
    policyFile: Optional[Dict] = None
    policyLink: str = ""
    implementation: Dict = Field(default_factory=dict)
    evaluation: Dict = Field(default_factory=dict)
    participation: Dict = Field(default_factory=dict)
    alignment: Dict = Field(default_factory=dict)
    status: str = "pending"
    admin_notes: str = ""

class PolicyArea(BaseModel):
    area_id: str
    area_name: str
    policies: List[SubPolicy] = Field(default_factory=list)

    @validator('area_id')
    def validate_area_id(cls, v):
        valid_ids = [area["id"] for area in POLICY_AREAS]
        if v not in valid_ids:
            raise ValueError(f'Invalid policy area ID. Must be one of: {valid_ids}')
        return v

class EnhancedSubmission(BaseModel):
    user_id: str
    user_email: str
    user_name: str
    country: str
    policyAreas: List[PolicyArea]
    submission_status: str = "pending"
    submitted_at: Optional[str] = None
    
    @validator('policyAreas')
    def validate_policy_areas(cls, v):
        if not v:
            raise ValueError('At least one policy area must be provided')
        return v

    @validator('country')
    def validate_country(cls, v):
        from config.data_constants import COUNTRIES
        if v not in COUNTRIES:
            raise ValueError('Invalid country')
        return v

class PolicyStatusUpdate(BaseModel):
    submission_id: str
    area_id: str
    policy_index: int
    status: str
    admin_notes: str = ""
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'approved', 'rejected', 'under_review', 'needs_revision']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v

    @validator('policy_index')
    def validate_policy_index(cls, v):
        if v < 0:
            raise ValueError('Policy index must be non-negative')
        return v
