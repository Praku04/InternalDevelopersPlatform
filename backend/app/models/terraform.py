"""Pydantic models for Terraform generation/plan results."""
from enum import Enum

from pydantic import BaseModel, Field


class TerraformStepStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"  # e.g. terraform binary not available in this environment


class TerraformStepResult(BaseModel):
    step: str
    status: TerraformStepStatus
    detail: str = ""


class TerraformPlanResult(BaseModel):
    request_id: str
    working_dir: str
    steps: list[TerraformStepResult] = Field(default_factory=list)
    overall_status: TerraformStepStatus
    generated_files: list[str] = Field(default_factory=list)
