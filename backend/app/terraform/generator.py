"""
Generates a Terraform root configuration from a DeploymentSpecification,
composing calls to approved modules only (Section 11 module reuse rule).

Resource wiring for this phase is intentionally simple and order-dependent:
vpc -> security-group -> ec2 -> alb -> s3, each stage feeding outputs
(vpc_id, subnet_ids, security_group_id) into the next. This covers the
Section 46 first-MVP shape (EC2 in a VPC with a security group); RDS/EKS
composition is left for a later phase along with the AI-driven module
selection that will eventually replace this fixed ordering.

Never generates a `terraform destroy` or `apply` call — this module only
ever writes `.tf` files to disk. Execution is handled separately and only
through the whitelisted TerraformEngine (see app/terraform/engine.py).
"""
import json
from pathlib import Path

from app.config import get_settings
from app.models.deployment import DeploymentSpecification, ResourceType


def _modules_root() -> Path:
    return Path(get_settings().terraform_modules_path).resolve()


def _hcl_value(value) -> str:
    """Render a Python value as an HCL literal (minimal, safe subset)."""
    return json.dumps(value)


def generate_root_config(spec: DeploymentSpecification, working_dir: Path) -> list[str]:
    """
    Writes provider.tf and main.tf into working_dir. Returns the list of
    generated file paths (as strings) for reporting back to the caller.
    """
    working_dir.mkdir(parents=True, exist_ok=True)
    modules_root = _modules_root()

    provider_tf = working_dir / "provider.tf"
    provider_tf.write_text(
        "terraform {\n"
        '  required_version = ">= 1.5.0"\n'
        "  required_providers {\n"
        '    aws = {\n'
        '      source  = "hashicorp/aws"\n'
        '      version = ">= 5.0"\n'
        "    }\n"
        "  }\n"
        "}\n\n"
        "provider \"aws\" {\n"
        f"  region = {_hcl_value(spec.region)}\n"
        "}\n"
    )

    blocks: list[str] = []
    resource_by_type = {r.type: r for r in spec.resources}

    has_vpc = ResourceType.VPC in resource_by_type
    has_sg = ResourceType.SECURITY_GROUP in resource_by_type
    has_ec2 = ResourceType.EC2 in resource_by_type
    has_alb = ResourceType.ALB in resource_by_type
    has_s3 = ResourceType.S3 in resource_by_type

    if has_vpc:
        r = resource_by_type[ResourceType.VPC]
        cfg = r.configuration
        blocks.append(
            f'module "vpc" {{\n'
            f'  source = {_hcl_value(str(modules_root / "vpc"))}\n\n'
            f'  application           = {_hcl_value(spec.application)}\n'
            f'  environment           = {_hcl_value(spec.environment.value)}\n'
            f'  cidr_block            = {_hcl_value(cfg.get("cidr_block", "10.0.0.0/16"))}\n'
            f'  azs                   = {_hcl_value(cfg.get("azs", ["ap-south-1a", "ap-south-1b"]))}\n'
            f'  public_subnet_cidrs   = {_hcl_value(cfg.get("public_subnet_cidrs", ["10.0.0.0/24", "10.0.1.0/24"]))}\n'
            f'  private_subnet_cidrs  = {_hcl_value(cfg.get("private_subnet_cidrs", ["10.0.10.0/24", "10.0.11.0/24"]))}\n'
            f'  enable_nat_gateway    = {_hcl_value(cfg.get("enable_nat_gateway", True))}\n'
            f'  enable_flow_logs      = {_hcl_value(cfg.get("enable_flow_logs", True))}\n'
            f"}}\n"
        )

    if has_sg:
        r = resource_by_type[ResourceType.SECURITY_GROUP]
        cfg = r.configuration
        vpc_id_expr = "module.vpc.vpc_id" if has_vpc else _hcl_value(cfg.get("vpc_id", ""))
        blocks.append(
            f'module "security_group" {{\n'
            f'  source = {_hcl_value(str(modules_root / "security-group"))}\n\n'
            f'  application   = {_hcl_value(spec.application)}\n'
            f'  environment   = {_hcl_value(spec.environment.value)}\n'
            f'  vpc_id        = {vpc_id_expr}\n'
            f'  name_suffix   = {_hcl_value(cfg.get("name_suffix", "app"))}\n'
            f'  ingress_rules = {_hcl_value(cfg.get("ingress_rules", []))}\n'
            f"}}\n"
        )

    if has_ec2:
        r = resource_by_type[ResourceType.EC2]
        cfg = r.configuration
        subnet_ids_expr = "module.vpc.private_subnet_ids" if has_vpc else _hcl_value(cfg.get("subnet_ids", []))
        sg_ids_expr = (
            "[module.security_group.security_group_id]"
            if has_sg
            else _hcl_value(cfg.get("security_group_ids", []))
        )
        blocks.append(
            f'module "ec2" {{\n'
            f'  source = {_hcl_value(str(modules_root / "ec2"))}\n\n'
            f'  application          = {_hcl_value(spec.application)}\n'
            f'  environment          = {_hcl_value(spec.environment.value)}\n'
            f'  instance_type        = {_hcl_value(cfg.get("instance_type", "t3.medium"))}\n'
            f'  instance_count       = {_hcl_value(cfg.get("instance_count", 1))}\n'
            f'  ami_id               = {_hcl_value(cfg.get("ami_id", ""))}\n'
            f'  subnet_ids           = {subnet_ids_expr}\n'
            f'  security_group_ids   = {sg_ids_expr}\n'
            f'  associate_public_ip  = {_hcl_value(cfg.get("associate_public_ip", False))}\n'
            f'  ebs_volume_size      = {_hcl_value(cfg.get("ebs_volume_size", 30))}\n'
            f'  ebs_encrypted        = {_hcl_value(cfg.get("encrypted_ebs", True))}\n'
            f'  detailed_monitoring  = {_hcl_value(cfg.get("monitoring", True))}\n'
            f'  enable_backup        = {_hcl_value(cfg.get("backup", True))}\n'
            f"}}\n"
        )

    if has_alb:
        r = resource_by_type[ResourceType.ALB]
        cfg = r.configuration
        subnet_ids_expr = "module.vpc.public_subnet_ids" if has_vpc else _hcl_value(cfg.get("subnet_ids", []))
        sg_ids_expr = (
            "[module.security_group.security_group_id]"
            if has_sg
            else _hcl_value(cfg.get("security_group_ids", []))
        )
        vpc_id_expr = "module.vpc.vpc_id" if has_vpc else _hcl_value(cfg.get("vpc_id", ""))
        target_ids_expr = "module.ec2.instance_ids" if has_ec2 else _hcl_value(cfg.get("target_ids", []))
        blocks.append(
            f'module "alb" {{\n'
            f'  source = {_hcl_value(str(modules_root / "alb"))}\n\n'
            f'  application         = {_hcl_value(spec.application)}\n'
            f'  environment         = {_hcl_value(spec.environment.value)}\n'
            f'  vpc_id              = {vpc_id_expr}\n'
            f'  subnet_ids          = {subnet_ids_expr}\n'
            f'  security_group_ids  = {sg_ids_expr}\n'
            f'  internal            = {_hcl_value(cfg.get("internal", True))}\n'
            f'  target_port         = {_hcl_value(cfg.get("target_port", 80))}\n'
            f'  target_ids          = {target_ids_expr}\n'
            f'  enable_access_logs  = {_hcl_value(False)}\n'
            f"}}\n"
        )

    if has_s3:
        r = resource_by_type[ResourceType.S3]
        cfg = r.configuration
        blocks.append(
            f'module "s3" {{\n'
            f'  source = {_hcl_value(str(modules_root / "s3"))}\n\n'
            f'  application     = {_hcl_value(spec.application)}\n'
            f'  environment     = {_hcl_value(spec.environment.value)}\n'
            f'  bucket_suffix   = {_hcl_value(cfg.get("bucket_suffix", "data"))}\n'
            f'  enable_logging  = {_hcl_value(False)}\n'
            f"}}\n"
        )

    main_tf = working_dir / "main.tf"
    main_tf.write_text("\n".join(blocks) + "\n" if blocks else "# No resources in this deployment specification.\n")

    return [str(provider_tf), str(main_tf)]
