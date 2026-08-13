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
from typing import NamedTuple

from app.config import get_settings
from app.models.deployment import DeploymentSpecification, ResourceType


class TerraformConfig(NamedTuple):
    """Generated Terraform configuration files."""
    main_tf: str
    variables_tf: str
    outputs_tf: str
    versions_tf: str


class TerraformGenerator:
    """
    Generates Terraform configuration from deployment specifications.
    """
    
    def __init__(self):
        """Initialize the generator."""
        self.settings = get_settings()
        self.modules_path = Path(self.settings.terraform_modules_path).resolve()
    
    def generate(self, spec: DeploymentSpecification) -> TerraformConfig:
        """
        Generate complete Terraform configuration.
        
        Args:
            spec: Deployment specification
            
        Returns:
            TerraformConfig with all required files
        """
        return TerraformConfig(
            main_tf=self._generate_main_tf(spec),
            variables_tf=self._generate_variables_tf(spec),
            outputs_tf=self._generate_outputs_tf(spec),
            versions_tf=self._generate_versions_tf(spec),
        )
    
    def _generate_versions_tf(self, spec: DeploymentSpecification) -> str:
        """Generate versions.tf with provider configuration."""
        return (
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
            f"  region = {self._hcl_value(spec.region)}\n"
            "}\n"
        )
    
    def _generate_variables_tf(self, spec: DeploymentSpecification) -> str:
        """Generate variables.tf."""
        return (
            'variable "application" {\n'
            '  description = "Application name"\n'
            '  type        = string\n'
            '}\n\n'
            'variable "environment" {\n'
            '  description = "Environment name"\n'
            '  type        = string\n'
            '}\n\n'
            'variable "aws_region" {\n'
            '  description = "AWS region"\n'
            '  type        = string\n'
            '}\n'
        )
    
    def _generate_outputs_tf(self, spec: DeploymentSpecification) -> str:
        """Generate outputs.tf."""
        outputs = []
        
        resource_types = {r.type for r in spec.resources}
        
        if ResourceType.VPC in resource_types:
            outputs.append(
                'output "vpc_id" {\n'
                '  description = "VPC ID"\n'
                '  value       = module.vpc.vpc_id\n'
                '}'
            )
        
        if ResourceType.EC2 in resource_types:
            outputs.append(
                'output "instance_ids" {\n'
                '  description = "EC2 instance IDs"\n'
                '  value       = module.ec2.instance_ids\n'
                '}'
            )
        
        if ResourceType.S3 in resource_types:
            outputs.append(
                'output "bucket_name" {\n'
                '  description = "S3 bucket name"\n'
                '  value       = module.s3.bucket_name\n'
                '}'
            )
        
        return '\n\n'.join(outputs) + '\n' if outputs else '# No outputs\n'
    
    def _generate_main_tf(self, spec: DeploymentSpecification) -> str:
        """Generate main.tf with module calls."""
        blocks: list[str] = []
        resource_by_type = {r.type: r for r in spec.resources}
        
        has_vpc = ResourceType.VPC in resource_by_type
        has_sg = ResourceType.SECURITY_GROUP in resource_by_type
        has_ec2 = ResourceType.EC2 in resource_by_type
        has_alb = ResourceType.ALB in resource_by_type
        has_s3 = ResourceType.S3 in resource_by_type
        
        if has_vpc:
            blocks.append(self._generate_vpc_module(spec, resource_by_type[ResourceType.VPC]))
        
        if has_sg:
            blocks.append(self._generate_sg_module(spec, resource_by_type[ResourceType.SECURITY_GROUP], has_vpc))
        
        if has_ec2:
            blocks.append(self._generate_ec2_module(spec, resource_by_type[ResourceType.EC2], has_vpc, has_sg))
        
        if has_alb:
            blocks.append(self._generate_alb_module(spec, resource_by_type[ResourceType.ALB], has_vpc, has_sg, has_ec2))
        
        if has_s3:
            blocks.append(self._generate_s3_module(spec, resource_by_type[ResourceType.S3]))
        
        return '\n\n'.join(blocks) + '\n' if blocks else '# No resources\n'
    
    def _generate_vpc_module(self, spec: DeploymentSpecification, resource) -> str:
        """Generate VPC module block."""
        cfg = resource.configuration
        return (
            f'module "vpc" {{\n'
            f'  source = {self._hcl_value(str(self.modules_path / "vpc"))}\n\n'
            f'  application           = {self._hcl_value(spec.application)}\n'
            f'  environment           = {self._hcl_value(spec.environment.value)}\n'
            f'  cidr_block            = {self._hcl_value(cfg.get("cidr_block", "10.0.0.0/16"))}\n'
            f'  azs                   = {self._hcl_value(cfg.get("azs", ["ap-south-1a", "ap-south-1b"]))}\n'
            f'  public_subnet_cidrs   = {self._hcl_value(cfg.get("public_subnet_cidrs", ["10.0.0.0/24", "10.0.1.0/24"]))}\n'
            f'  private_subnet_cidrs  = {self._hcl_value(cfg.get("private_subnet_cidrs", ["10.0.10.0/24", "10.0.11.0/24"]))}\n'
            f'  enable_nat_gateway    = {self._hcl_value(cfg.get("enable_nat_gateway", True))}\n'
            f'  enable_flow_logs      = {self._hcl_value(cfg.get("enable_flow_logs", True))}\n'
            f'}}'
        )
    
    def _generate_sg_module(self, spec: DeploymentSpecification, resource, has_vpc: bool) -> str:
        """Generate security group module block."""
        cfg = resource.configuration
        vpc_id_expr = "module.vpc.vpc_id" if has_vpc else self._hcl_value(cfg.get("vpc_id", ""))
        return (
            f'module "security_group" {{\n'
            f'  source = {self._hcl_value(str(self.modules_path / "security-group"))}\n\n'
            f'  application   = {self._hcl_value(spec.application)}\n'
            f'  environment   = {self._hcl_value(spec.environment.value)}\n'
            f'  vpc_id        = {vpc_id_expr}\n'
            f'  name_suffix   = {self._hcl_value(cfg.get("name_suffix", "app"))}\n'
            f'  ingress_rules = {self._hcl_value(cfg.get("ingress_rules", []))}\n'
            f'}}'
        )
    
    def _generate_ec2_module(self, spec: DeploymentSpecification, resource, has_vpc: bool, has_sg: bool) -> str:
        """Generate EC2 module block."""
        cfg = resource.configuration
        subnet_ids_expr = "module.vpc.private_subnet_ids" if has_vpc else self._hcl_value(cfg.get("subnet_ids", []))
        sg_ids_expr = "[module.security_group.security_group_id]" if has_sg else self._hcl_value(cfg.get("security_group_ids", []))
        return (
            f'module "ec2" {{\n'
            f'  source = {self._hcl_value(str(self.modules_path / "ec2"))}\n\n'
            f'  application          = {self._hcl_value(spec.application)}\n'
            f'  environment          = {self._hcl_value(spec.environment.value)}\n'
            f'  instance_type        = {self._hcl_value(cfg.get("instance_type", "t3.medium"))}\n'
            f'  instance_count       = {self._hcl_value(cfg.get("instance_count", 1))}\n'
            f'  ami_id               = {self._hcl_value(cfg.get("ami_id", ""))}\n'
            f'  subnet_ids           = {subnet_ids_expr}\n'
            f'  security_group_ids   = {sg_ids_expr}\n'
            f'  associate_public_ip  = {self._hcl_value(cfg.get("associate_public_ip", False))}\n'
            f'  ebs_volume_size      = {self._hcl_value(cfg.get("ebs_volume_size", 30))}\n'
            f'  ebs_encrypted        = {self._hcl_value(cfg.get("encrypted_ebs", True))}\n'
            f'  detailed_monitoring  = {self._hcl_value(cfg.get("monitoring", True))}\n'
            f'  enable_backup        = {self._hcl_value(cfg.get("backup", True))}\n'
            f'}}'
        )
    
    def _generate_alb_module(self, spec: DeploymentSpecification, resource, has_vpc: bool, has_sg: bool, has_ec2: bool) -> str:
        """Generate ALB module block."""
        cfg = resource.configuration
        subnet_ids_expr = "module.vpc.public_subnet_ids" if has_vpc else self._hcl_value(cfg.get("subnet_ids", []))
        sg_ids_expr = "[module.security_group.security_group_id]" if has_sg else self._hcl_value(cfg.get("security_group_ids", []))
        vpc_id_expr = "module.vpc.vpc_id" if has_vpc else self._hcl_value(cfg.get("vpc_id", ""))
        target_ids_expr = "module.ec2.instance_ids" if has_ec2 else self._hcl_value(cfg.get("target_ids", []))
        return (
            f'module "alb" {{\n'
            f'  source = {self._hcl_value(str(self.modules_path / "alb"))}\n\n'
            f'  application         = {self._hcl_value(spec.application)}\n'
            f'  environment         = {self._hcl_value(spec.environment.value)}\n'
            f'  vpc_id              = {vpc_id_expr}\n'
            f'  subnet_ids          = {subnet_ids_expr}\n'
            f'  security_group_ids  = {sg_ids_expr}\n'
            f'  internal            = {self._hcl_value(cfg.get("internal", True))}\n'
            f'  target_port         = {self._hcl_value(cfg.get("target_port", 80))}\n'
            f'  target_ids          = {target_ids_expr}\n'
            f'  enable_access_logs  = {self._hcl_value(False)}\n'
            f'}}'
        )
    
    def _generate_s3_module(self, spec: DeploymentSpecification, resource) -> str:
        """Generate S3 module block."""
        cfg = resource.configuration
        return (
            f'module "s3" {{\n'
            f'  source = {self._hcl_value(str(self.modules_path / "s3"))}\n\n'
            f'  application     = {self._hcl_value(spec.application)}\n'
            f'  environment     = {self._hcl_value(spec.environment.value)}\n'
            f'  bucket_suffix   = {self._hcl_value(cfg.get("bucket_suffix", "data"))}\n'
            f'  enable_logging  = {self._hcl_value(False)}\n'
            f'}}'
        )
    
    def _hcl_value(self, value) -> str:
        """Render a Python value as an HCL literal."""
        return json.dumps(value)


def _modules_root() -> Path:
    return Path(get_settings().terraform_modules_path).resolve()


def _hcl_value(value) -> str:
    """Render a Python value as an HCL literal (minimal, safe subset)."""
    return json.dumps(value)


def generate_root_config(spec: DeploymentSpecification, working_dir: Path) -> list[str]:
    """
    Writes provider.tf and main.tf into working_dir. Returns the list of
    generated file paths (as strings) for reporting back to the caller.
    
    This function is kept for backward compatibility.
    """
    generator = TerraformGenerator()
    config = generator.generate(spec)
    
    working_dir.mkdir(parents=True, exist_ok=True)
    
    # Write all files
    (working_dir / "versions.tf").write_text(config.versions_tf)
    (working_dir / "variables.tf").write_text(config.variables_tf)
    (working_dir / "main.tf").write_text(config.main_tf)
    (working_dir / "outputs.tf").write_text(config.outputs_tf)
    
    return [
        str(working_dir / "versions.tf"),
        str(working_dir / "variables.tf"),
        str(working_dir / "main.tf"),
        str(working_dir / "outputs.tf"),
    ]
