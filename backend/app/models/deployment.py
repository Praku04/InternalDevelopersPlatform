"""
Pydantic models for the Deployment Specification — the canonical contract
between the UI, the AI orchestrator, and the Terraform engine.

Mirrors ai/schemas/deployment_specification.schema.json. Raw LLM output is
never used directly; it must first be parsed into (and validated as) an
AIDeploymentRecommendation, which the backend then turns into a
DeploymentSpecification.
"""
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.module import Environment


class RequestSource(str, Enum):
    SELF_SERVICE = "self_service"
    AI_ASSISTANT = "ai_assistant"


class ResourceType(str, Enum):
    VPC = "vpc"
    EC2 = "ec2"
    SECURITY_GROUP = "security-group"
    ALB = "alb"
    S3 = "s3"
    RDS = "rds"


class ResourceAction(str, Enum):
    REUSE = "reuse"
    GENERATE = "generate"


class ResourceSpec(BaseModel):
    type: ResourceType
    module: str
    version: str
    action: ResourceAction = ResourceAction.REUSE
    configuration: dict[str, Any] = Field(default_factory=dict)


class DeploymentSpecification(BaseModel):
    request_id: str
    source: RequestSource
    user_id: str
    application: str
    environment: Environment
    region: str
    resources: list[ResourceSpec] = Field(min_length=1)
    missing_modules: list[str] = Field(default_factory=list)
    security_requirements: list[str] = Field(default_factory=list)
    approval_required: bool = False

    @field_validator("application")
    @classmethod
    def application_must_be_slug(cls, v: str) -> str:
        if not v.replace("-", "").isalnum():
            raise ValueError("application must be an alphanumeric slug (hyphens allowed)")
        return v.lower()


# Alias for backward compatibility
DeploymentRequest = DeploymentSpecification


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentSource(str, Enum):
    """Deployment source enumeration."""
    SELF_SERVICE = "self_service"
    AI_ASSISTANT = "ai_assistant"


class AIDeploymentRecommendation(BaseModel):
    """
    The schema-validated shape an AI (Bedrock) response must conform to
    before the backend will act on it. Raw model text is never trusted —
    it is parsed into this model, and parsing failures are treated as a
    failed AI request, not silently coerced into a deployment.
    """

    request_summary: str
    environment: Environment
    region: str
    resources: list[ResourceSpec]
    missing_modules: list[str] = Field(default_factory=list)
    security_requirements: list[str] = Field(default_factory=list)
    approval_required: bool = False
