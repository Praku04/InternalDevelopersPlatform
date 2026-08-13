"""
Approval models for deployment requests.

Defines approval workflow, approval status, and approval history.
"""
from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Approval status enumeration."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


class ApprovalLevel(str, Enum):
    """Approval level enumeration."""
    SECURITY = "SECURITY"
    TEAM_LEAD = "TEAM_LEAD"
    MANAGER = "MANAGER"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class Approval(BaseModel):
    """
    Approval record for a deployment request.
    
    Tracks approval workflow with multiple levels based on environment.
    """
    approval_id: str = Field(default_factory=lambda: f"APPR-{uuid4().hex[:8].upper()}")
    request_id: str
    
    # Approval level
    level: ApprovalLevel
    required: bool = True
    
    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # Approver information
    approver_id: str | None = None
    approver_name: str | None = None
    approver_email: str | None = None
    
    # Decision
    approved_at: datetime | None = None
    decision_comment: str | None = None
    
    # Rejection
    rejection_reason: str | None = None
    rejected_at: datetime | None = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None  # Auto-reject after expiration
    
    class Config:
        use_enum_values = True


class ApprovalWorkflow(BaseModel):
    """
    Approval workflow configuration for a deployment request.
    
    Defines required approvals based on environment and risk level.
    """
    workflow_id: str = Field(default_factory=lambda: f"WF-{uuid4().hex[:8].upper()}")
    request_id: str
    environment: str
    
    # Required approvals
    required_approvals: list[ApprovalLevel]
    
    # Current approvals
    approvals: list[Approval] = Field(default_factory=list)
    
    # Workflow status
    all_approved: bool = False
    any_rejected: bool = False
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    def add_approval(self, approval: Approval):
        """Add approval to workflow."""
        self.approvals.append(approval)
        self._update_status()
    
    def _update_status(self):
        """Update workflow status based on current approvals."""
        # Check for rejections
        if any(a.status == ApprovalStatus.REJECTED for a in self.approvals):
            self.any_rejected = True
            self.all_approved = False
            return
        
        # Check if all required approvals are granted
        approved_levels = {
            a.level 
            for a in self.approvals 
            if a.status == ApprovalStatus.APPROVED
        }
        
        required_levels = set(self.required_approvals)
        
        self.all_approved = required_levels.issubset(approved_levels)
        
        if self.all_approved:
            self.completed_at = datetime.utcnow()
    
    def is_complete(self) -> bool:
        """Check if workflow is complete (all approved or any rejected)."""
        return self.all_approved or self.any_rejected
    
    def can_deploy(self) -> bool:
        """Check if deployment can proceed."""
        return self.all_approved and not self.any_rejected


class ApprovalRequest(BaseModel):
    """Request to create approval workflow."""
    request_id: str
    environment: str
    deployment_risk: str = "LOW"
    
    # Deployment details for approver context
    application_name: str
    resources: list[dict] = Field(default_factory=list)
    estimated_cost: float | None = None
    security_status: str = "UNKNOWN"


class ApprovalDecision(BaseModel):
    """Approval decision from approver."""
    approve: bool
    comment: str | None = None
    approver_id: str
    approver_name: str
    approver_email: str


def get_required_approvals(environment: str, deployment_risk: str = "LOW") -> list[ApprovalLevel]:
    """
    Determine required approvals based on environment and risk.
    
    Args:
        environment: Deployment environment (dev, uat, prod)
        deployment_risk: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        
    Returns:
        List of required approval levels
    """
    environment = environment.lower()
    deployment_risk = deployment_risk.upper()
    
    # DEV: Security check only (automated if passed)
    if environment == "dev":
        return []  # No manual approvals required, security scan auto-approves
    
    # UAT: Team Lead + Security
    if environment == "uat":
        approvals = [ApprovalLevel.TEAM_LEAD]
        
        if deployment_risk in ["HIGH", "CRITICAL"]:
            approvals.append(ApprovalLevel.SECURITY)
        
        return approvals
    
    # PROD: Manager + Security + Platform Admin (for HIGH/CRITICAL)
    if environment == "prod":
        approvals = [ApprovalLevel.MANAGER, ApprovalLevel.SECURITY]
        
        if deployment_risk in ["HIGH", "CRITICAL"]:
            approvals.append(ApprovalLevel.PLATFORM_ADMIN)
        
        return approvals
    
    # Default: Require security approval
    return [ApprovalLevel.SECURITY]
