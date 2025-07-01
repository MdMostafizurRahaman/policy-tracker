"""
Pydantic models for policy submissions and management.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from config.constants import POLICY_AREAS, COUNTRIES, POLICY_STATUSES

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
        if v not in POLICY_STATUSES:
            raise ValueError(f'Status must be one of: {POLICY_STATUSES}')
        return v

    @validator('policy_index')
    def validate_policy_index(cls, v):
        if v < 0:
            raise ValueError('Policy index must be non-negative')
        return v

class PolicyResponse(BaseModel):
    id: str
    policyName: str
    country: str
    policyArea: str
    area_name: str
    status: str
    created_at: str
    policy_score: int = 0
    completeness_score: str = "basic"
