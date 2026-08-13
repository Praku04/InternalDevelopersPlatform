"""
Resource inventory models.

Tracks deployed AWS resources for management, compliance, and cost tracking.
"""
from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ResourceStatus(str, Enum):
    """Resource status enumeration."""
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ComplianceStatus(str, Enum):
    """Compliance status enumeration."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_EVALUATED = "NOT_EVALUATED"


class ManagedBy(str, Enum):
    """Resource management source."""
    AI_CLOUD_PLATFORM = "ai-cloud-platform"
    TERRAFORM = "terraform"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class Resource(BaseModel):
    """
    AWS resource inventory record.
    
    Tracks deployed resources with metadata for management and compliance.
    """
    resource_id: str = Field(default_factory=lambda: f"RES-{uuid4().hex[:8].upper()}")
    
    # AWS identifiers
    aws_resource_id: str  # e.g., i-1234567890abcdef0
    aws_resource_type: str  # e.g., AWS::EC2::Instance
    aws_resource_arn: str | None = None
    
    # Classification
    service: str  # EC2, VPC, S3, RDS, etc.
    resource_type: str  # instance, bucket, database, etc.
    resource_name: str | None = None
    
    # Location
    aws_account_id: str
    aws_region: str
    availability_zone: str | None = None
    
    # Ownership and management
    application: str
    environment: str
    owner: str | None = None
    managed_by: ManagedBy = ManagedBy.UNKNOWN
    
    # Deployment tracking
    deployment_request_id: str | None = None
    terraform_address: str | None = None  # e.g., module.ec2.aws_instance.web
    terraform_workspace: str | None = None
    
    # Status
    status: ResourceStatus = ResourceStatus.ACTIVE
    compliance_status: ComplianceStatus = ComplianceStatus.NOT_EVALUATED
    
    # Configuration
    configuration: dict = Field(default_factory=dict)
    
    # Security
    security_groups: list[str] = Field(default_factory=list)
    subnet_id: str | None = None
    vpc_id: str | None = None
    public_ip: str | None = None
    private_ip: str | None = None
    encrypted: bool | None = None
    
    # Cost tracking
    instance_type: str | None = None  # For EC2, RDS
    estimated_monthly_cost: float | None = None
    
    # Tags
    tags: dict[str, str] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    terminated_at: datetime | None = None
    
    # Compliance findings
    compliance_findings: list[dict] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ResourceSummary(BaseModel):
    """Summary of resources by type."""
    total_resources: int
    by_service: dict[str, int]
    by_environment: dict[str, int]
    by_status: dict[str, int]
    by_managed: dict[str, int]
    by_compliance: dict[str, int]


class DriftRecord(BaseModel):
    """
    Terraform drift detection record.
    
    Tracks when actual AWS state differs from Terraform state.
    """
    drift_id: str = Field(default_factory=lambda: f"DRIFT-{uuid4().hex[:8].upper()}")
    
    resource_id: str
    aws_resource_id: str
    deployment_request_id: str
    
    # Drift details
    terraform_address: str
    drift_detected: bool
    drift_details: dict = Field(default_factory=dict)
    
    # What changed
    expected_state: dict = Field(default_factory=dict)
    actual_state: dict = Field(default_factory=dict)
    differences: list[dict] = Field(default_factory=list)
    
    # Detection
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    detection_method: str = "terraform_plan"  # terraform_plan, aws_config, manual
    
    # Resolution
    resolved: bool = False
    resolved_at: datetime | None = None
    resolution_action: str | None = None  # remediated, accepted, ignored
    resolution_notes: str | None = None


class PostDeploymentValidation(BaseModel):
    """
    Post-deployment validation results.
    
    Validates that deployment was successful and resources are healthy.
    """
    validation_id: str = Field(default_factory=lambda: f"VAL-{uuid4().hex[:8].upper()}")
    deployment_request_id: str
    
    # Overall status
    validation_passed: bool = False
    validation_message: str | None = None
    
    # Resource validation
    resources_expected: int
    resources_found: int
    resources_healthy: int
    resources_missing: list[str] = Field(default_factory=list)
    resources_unhealthy: list[str] = Field(default_factory=list)
    
    # Tag validation
    tags_compliant: bool = False
    missing_tags: list[dict] = Field(default_factory=list)
    
    # Security validation
    security_compliant: bool = False
    security_issues: list[dict] = Field(default_factory=list)
    
    # Output validation
    outputs_captured: dict = Field(default_factory=dict)
    
    # Timing
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validation_duration: float | None = None  # seconds
