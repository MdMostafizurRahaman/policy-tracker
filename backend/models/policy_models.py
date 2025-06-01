from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator
from .base_models import BaseDBModel

class PolicyFile(BaseModel):
    name: str
    file_id: Optional[str] = None
    size: int
    type: str
    upload_date: Optional[datetime] = None

class Implementation(BaseModel):
    yearlyBudget: str = ""
    budgetCurrency: str = "USD"
    privateSecFunding: bool = False
    deploymentYear: int = Field(default_factory=lambda: datetime.now().year)

class Evaluation(BaseModel):
    isEvaluated: bool = False
    evaluationType: str = "internal"
    riskAssessment: bool = False
    transparencyScore: int = 0
    explainabilityScore: int = 0
    accountabilityScore: int = 0

class Participation(BaseModel):
    hasConsultation: bool = False
    consultationStartDate: str = ""
    consultationEndDate: str = ""
    commentsPublic: bool = False
    stakeholderScore: int = 0

class Alignment(BaseModel):
    aiPrinciples: List[str] = []
    humanRightsAlignment: bool = False
    environmentalConsiderations: bool = False
    internationalCooperation: bool = False

class PolicyInitiative(BaseDBModel):
    policyName: str
    policyId: str = ""
    policyArea: str = ""
    targetGroups: List[str] = []
    policyDescription: str = ""
    policyFile: Optional[PolicyFile] = None
    policyLink: str = ""
    implementation: Implementation
    evaluation: Evaluation
    participation: Participation
    alignment: Alignment
    status: str = "pending"  # pending, approved, rejected, needs_revision
    admin_notes: str = ""

    @validator('policyName')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Policy name must not be empty')
        return v

class FormSubmission(BaseDBModel):
    country: str
    policyInitiatives: List[PolicyInitiative]
    submission_status: str = "pending"

    @validator('country')
    def country_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Country name must not be empty')
        return v

class AdminAction(BaseDBModel):
    action: str  # approve, reject, modify, delete
    policy_id: str
    submission_id: str
    admin_notes: str = ""
    modified_data: Optional[Dict] = None

class PolicyStatusUpdate(BaseModel):
    submission_id: str
    policy_index: int
    status: str
    admin_notes: str = ""

class PolicyUpdate(BaseModel):
    submission_id: str
    policy_index: int
    updated_policy: PolicyInitiative