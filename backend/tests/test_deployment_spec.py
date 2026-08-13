"""Tests for the DeploymentSpecification / AIDeploymentRecommendation Pydantic models."""
import pytest
from pydantic import ValidationError

from app.models.deployment import (
    AIDeploymentRecommendation,
    DeploymentSpecification,
    ResourceAction,
    ResourceSpec,
    ResourceType,
)


def _valid_spec_kwargs() -> dict:
    return dict(
        request_id="REQ-10001",
        source="self_service",
        user_id="user123",
        application="payment",
        environment="dev",
        region="ap-south-1",
        resources=[
            ResourceSpec(
                type=ResourceType.EC2,
                module="ec2",
                version="1.0.0",
                action=ResourceAction.REUSE,
                configuration={"instance_type": "t3.medium", "instance_count": 2},
            )
        ],
    )


def test_valid_deployment_spec_parses() -> None:
    spec = DeploymentSpecification(**_valid_spec_kwargs())
    assert spec.request_id == "REQ-10001"
    assert spec.resources[0].type == ResourceType.EC2
    assert spec.approval_required is False


def test_requires_at_least_one_resource() -> None:
    kwargs = _valid_spec_kwargs()
    kwargs["resources"] = []
    with pytest.raises(ValidationError):
        DeploymentSpecification(**kwargs)


def test_rejects_invalid_environment() -> None:
    kwargs = _valid_spec_kwargs()
    kwargs["environment"] = "staging"  # not one of dev/uat/prod
    with pytest.raises(ValidationError):
        DeploymentSpecification(**kwargs)


def test_application_slug_is_lowercased() -> None:
    kwargs = _valid_spec_kwargs()
    kwargs["application"] = "Payment"
    spec = DeploymentSpecification(**kwargs)
    assert spec.application == "payment"


def test_rejects_non_slug_application_name() -> None:
    kwargs = _valid_spec_kwargs()
    kwargs["application"] = "payment app!"
    with pytest.raises(ValidationError):
        DeploymentSpecification(**kwargs)


def test_ai_recommendation_schema_validates_untrusted_output() -> None:
    """Simulates parsing raw (untrusted) Bedrock JSON output."""
    raw_model_output = {
        "request_summary": "Create payment development environment",
        "environment": "dev",
        "region": "ap-south-1",
        "resources": [
            {"type": "vpc", "module": "vpc", "version": "1.0.0", "action": "reuse", "configuration": {}},
            {"type": "ec2", "module": "ec2", "version": "1.0.0", "action": "reuse", "configuration": {}},
        ],
        "missing_modules": [],
        "security_requirements": ["encrypted_ebs", "private_subnet", "monitoring"],
        "approval_required": False,
    }
    rec = AIDeploymentRecommendation.model_validate(raw_model_output)
    assert rec.approval_required is False
    assert len(rec.resources) == 2


def test_ai_recommendation_rejects_malformed_output() -> None:
    """An LLM hallucinating a nonexistent resource type must fail validation, not be trusted."""
    raw_model_output = {
        "request_summary": "Create something",
        "environment": "dev",
        "region": "ap-south-1",
        "resources": [
            {"type": "quantum-computer", "module": "qc", "version": "1.0.0", "action": "reuse", "configuration": {}}
        ],
    }
    with pytest.raises(ValidationError):
        AIDeploymentRecommendation.model_validate(raw_model_output)
