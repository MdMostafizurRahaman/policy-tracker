"""
Policy-related Pydantic models
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PolicyStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PolicyType(str, Enum):
    REGULATION = "regulation"
    LEGISLATION = "legislation"
    GUIDELINE = "guideline"
    STANDARD = "standard"
    OTHER = "other"

class PolicyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    country: str = Field(..., min_length=1)
    policyType: PolicyType
    source: Optional[str] = None
    url: Optional[str] = None
    dateImplemented: Optional[datetime] = None
    tags: Optional[List[str]] = []
    keyPoints: Optional[List[str]] = []

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    policyType: Optional[PolicyType] = None
    source: Optional[str] = None
    url: Optional[str] = None
    dateImplemented: Optional[datetime] = None
    tags: Optional[List[str]] = None
    keyPoints: Optional[List[str]] = None

class PolicyResponse(BaseModel):
    id: str
    title: str
    description: str
    country: str
    policyType: str
    source: Optional[str] = None
    url: Optional[str] = None
    dateImplemented: Optional[datetime] = None
    tags: List[str] = []
    keyPoints: List[str] = []
    status: PolicyStatus
    submittedBy: Optional[str] = None
    submittedAt: datetime
    approvedBy: Optional[str] = None
    approvedAt: Optional[datetime] = None

class PolicyApproval(BaseModel):
    policy_id: str
    action: str = Field(..., regex="^(approve|reject)$")
    reason: Optional[str] = None

class PolicySearch(BaseModel):
    query: Optional[str] = None
    country: Optional[str] = None
    policyType: Optional[PolicyType] = None
    tags: Optional[List[str]] = None
    limit: Optional[int] = Field(10, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)
