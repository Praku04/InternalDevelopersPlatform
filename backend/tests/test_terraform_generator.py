"""Tests for Terraform root-config generation from a DeploymentSpecification."""
import tempfile
from pathlib import Path

from app.models.deployment import DeploymentSpecification, ResourceAction, ResourceSpec, ResourceType
from app.terraform.generator import generate_root_config


def _spec_with_vpc_sg_ec2() -> DeploymentSpecification:
    return DeploymentSpecification(
        request_id="REQ-GEN-001",
        source="self_service",
        user_id="user123",
        application="payment",
        environment="dev",
        region="ap-south-1",
        resources=[
            ResourceSpec(type=ResourceType.VPC, module="vpc", version="1.0.0", action=ResourceAction.REUSE, configuration={}),
            ResourceSpec(
                type=ResourceType.SECURITY_GROUP,
                module="security-group",
                version="1.0.0",
                action=ResourceAction.REUSE,
                configuration={"name_suffix": "ec2"},
            ),
            ResourceSpec(
                type=ResourceType.EC2,
                module="ec2",
                version="1.0.0",
                action=ResourceAction.REUSE,
                configuration={"instance_type": "t3.medium", "instance_count": 2, "encrypted_ebs": True},
            ),
        ],
    )


def test_generates_provider_and_main_tf() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        working_dir = Path(tmp) / "run"
        files = generate_root_config(_spec_with_vpc_sg_ec2(), working_dir)

        assert (working_dir / "provider.tf").exists()
        assert (working_dir / "main.tf").exists()
        assert len(files) == 2


def test_main_tf_wires_vpc_into_ec2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        working_dir = Path(tmp) / "run"
        generate_root_config(_spec_with_vpc_sg_ec2(), working_dir)
        main_tf = (working_dir / "main.tf").read_text()

        assert 'module "vpc"' in main_tf
        assert 'module "security_group"' in main_tf
        assert 'module "ec2"' in main_tf
        # EC2 subnet_ids should reference the VPC module's private subnets, not a hardcoded list.
        assert "module.vpc.private_subnet_ids" in main_tf
        assert "module.security_group.security_group_id" in main_tf


def test_provider_tf_uses_spec_region() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        working_dir = Path(tmp) / "run"
        generate_root_config(_spec_with_vpc_sg_ec2(), working_dir)
        provider_tf = (working_dir / "provider.tf").read_text()
        assert "ap-south-1" in provider_tf


def test_ec2_only_spec_uses_configuration_fallback_subnets() -> None:
    spec = DeploymentSpecification(
        request_id="REQ-GEN-002",
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
                configuration={"subnet_ids": ["subnet-abc"], "security_group_ids": ["sg-abc"]},
            ),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        working_dir = Path(tmp) / "run"
        generate_root_config(spec, working_dir)
        main_tf = (working_dir / "main.tf").read_text()
        assert "subnet-abc" in main_tf
        assert "sg-abc" in main_tf
