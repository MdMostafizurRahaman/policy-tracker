from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Policy types for reference
POLICY_TYPES = [
    "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
    "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
    "Physical Health", "Social Media/Gaming Regulation"
]

# Target group options for reference
TARGET_GROUPS = [
    "Government", "Industry", "Academia", "Small Businesses",
    "General Public", "Specific Sector"
]

# AI Principles options for reference
AI_PRINCIPLES = [
    "Fairness", "Accountability", "Transparency", "Explainability",
    "Safety", "Human Control", "Privacy", "Security",
    "Non-discrimination", "Trust", "Sustainability"
]

class Metric(BaseModel):
    name: str
    value: Any

class Implementation(BaseModel):
    yearlyBudget: Optional[str] = None
    budgetCurrency: str = "USD"
    privateSecFunding: bool = False
    deploymentYear: Optional[int] = None

class Evaluation(BaseModel):
    isEvaluated: bool = False
    evaluationType: str = "internal"
    riskAssessment: bool = False
    transparencyScore: int = 0
    explainabilityScore: int = 0
    accountabilityScore: int = 0

class Participation(BaseModel):
    hasConsultation: bool = False
    consultationStartDate: Optional[str] = None
    consultationEndDate: Optional[str] = None
    commentsPublic: bool = False
    stakeholderScore: int = 0

class Alignment(BaseModel):
    aiPrinciples: List[str] = []
    humanRightsAlignment: bool = False
    environmentalConsiderations: bool = False
    internationalCooperation: bool = False

class Policy(BaseModel):
    policyName: str
    policyId: Optional[str] = None
    policyArea: str
    targetGroups: List[str] = []
    policyDescription: Optional[str] = ""
    policyFile: Optional[str] = None
    policyLink: Optional[str] = None
    implementation: Optional[Implementation] = None
    evaluation: Optional[Evaluation] = None
    participation: Optional[Participation] = None
    alignment: Optional[Alignment] = None
    status: str = "pending"  # pending, approved, declined
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
   
    class Config:
        orm_mode = True

class CountrySubmission(BaseModel):
    country: str
    policyInitiatives: List[Policy]
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
   
    class Config:
        orm_mode = True

class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    total_count: int
    per_page: int

class SubmissionsResponse(BaseModel):
    submissions: List[Dict[str, Any]]
    pagination: PaginationInfo

class PolicyUpdateRequest(BaseModel):
    country: str
    policyIndex: int
    text: str
    status: Optional[str] = None

class PolicyApprovalRequest(BaseModel):
    country: str
    policyIndex: int
    text: str

class PolicyDeclineRequest(BaseModel):
    country: str
    policyIndex: int
    text: str

class SubmissionRemovalRequest(BaseModel):
    country: str