"""Pydantic models for Terraform module registry entries (terraform/modules/*/module.json)."""
from enum import Enum
from pydantic import BaseModel, Field


class ModuleCategory(str, Enum):
    NETWORKING = "networking"
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    SECURITY = "security"
    OTHER = "other"


class ModuleStatus(str, Enum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class SecurityStatus(str, Enum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    FAILED = "failed"


class Environment(str, Enum):
    DEV = "dev"
    UAT = "uat"
    PROD = "prod"


class ModuleMetadata(BaseModel):
    """Mirrors ai/schemas/module_metadata.schema.json."""

    module_name: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    category: ModuleCategory
    description: str
    path: str
    status: ModuleStatus
    supported_environments: list[Environment]
    capabilities: list[str]
    security_status: SecurityStatus
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
