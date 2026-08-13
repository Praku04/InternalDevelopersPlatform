"""
Post-Deployment Validation Service.

Validates that deployments completed successfully and resources are healthy.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.models.deployment import DeploymentRequest
from app.models.inventory import PostDeploymentValidation, Resource
from .inventory_service import InventoryService

logger = logging.getLogger(__name__)
settings = get_settings()


class ValidationService:
    """
    Service for post-deployment validation.
    
    Responsibilities:
    - Verify resources were created
    - Check resource health
    - Validate tags
    - Validate security compliance
    - Capture outputs
    """
    
    def __init__(self, inventory_service: Optional[InventoryService] = None):
        """Initialize validation service."""
        self.inventory_service = inventory_service or InventoryService()
    
    def validate_deployment(
        self,
        deployment_request: DeploymentRequest,
        terraform_outputs: dict,
    ) -> PostDeploymentValidation:
        """
        Validate deployment after terraform apply.
        
        Args:
            deployment_request: Original deployment request
            terraform_outputs: Terraform output values
            
        Returns:
            Validation results
        """
        logger.info(f"Validating deployment {deployment_request.request_id}")
        
        validation = PostDeploymentValidation(
            deployment_request_id=deployment_request.request_id,
        )
        
        # Discover created resources
        resources = self.inventory_service.discover_resources(
            deployment_request.request_id
        )
        
        # Calculate expected resources
        resources_expected = self._count_expected_resources(deployment_request)
        validation.resources_expected = resources_expected
        validation.resources_found = len(resources)
        
        # Check if all resources were created
        if len(resources) < resources_expected:
            validation.validation_message = f"Expected {resources_expected} resources, found {len(resources)}"
            validation.resources_missing = self._identify_missing_resources(
                deployment_request,
                resources,
            )
        
        # Validate resource health
        healthy_resources = []
        unhealthy_resources = []
        
        for resource in resources:
            if self._is_resource_healthy(resource):
                healthy_resources.append(resource.aws_resource_id)
            else:
                unhealthy_resources.append(resource.aws_resource_id)
        
        validation.resources_healthy = len(healthy_resources)
        validation.resources_unhealthy = unhealthy_resources
        
        # Validate tags
        validation.tags_compliant, validation.missing_tags = self._validate_tags(resources)
        
        # Validate security
        validation.security_compliant, validation.security_issues = self._validate_security(resources)
        
        # Capture outputs
        validation.outputs_captured = terraform_outputs
        
        # Overall validation
        validation.validation_passed = (
            len(resources) == resources_expected
            and len(unhealthy_resources) == 0
            and validation.tags_compliant
            and validation.security_compliant
        )
        
        if validation.validation_passed:
            validation.validation_message = "Deployment validation passed"
        elif not validation.validation_message:
            validation.validation_message = "Deployment validation failed"
        
        logger.info(
            f"Validation complete: "
            f"Passed={validation.validation_passed}, "
            f"Resources={len(resources)}/{resources_expected}, "
            f"Healthy={len(healthy_resources)}"
        )
        
        return validation
    
    def _count_expected_resources(self, deployment_request: DeploymentRequest) -> int:
        """Count expected resources from deployment request."""
        count = 0
        
        for resource_spec in deployment_request.resources:
            if resource_spec.type == "vpc":
                count += 1  # VPC
                count += 2  # 2 subnets
                count += 1  # Internet gateway
                count += 1  # Route table
            elif resource_spec.type == "ec2":
                instance_count = resource_spec.properties.get("instance_count", 1)
                count += instance_count
            elif resource_spec.type == "security-group":
                count += 1
            elif resource_spec.type == "alb":
                count += 1  # ALB
                count += 1  # Target group
            elif resource_spec.type == "s3":
                count += 1
            elif resource_spec.type == "rds":
                count += 1
        
        return count
    
    def _identify_missing_resources(
        self,
        deployment_request: DeploymentRequest,
        resources: list[Resource],
    ) -> list[str]:
        """Identify which resources are missing."""
        missing = []
        
        # Check for expected resource types
        found_types = {r.service for r in resources}
        
        for resource_spec in deployment_request.resources:
            expected_type = resource_spec.type.upper()
            
            if expected_type == "EC2" and "EC2" not in found_types:
                missing.append("EC2 instances")
            elif expected_type == "VPC" and "VPC" not in found_types:
                missing.append("VPC")
            elif expected_type == "S3" and "S3" not in found_types:
                missing.append("S3 bucket")
            elif expected_type == "ALB" and "ALB" not in found_types:
                missing.append("Application Load Balancer")
            elif expected_type == "RDS" and "RDS" not in found_types:
                missing.append("RDS database")
        
        return missing
    
    def _is_resource_healthy(self, resource: Resource) -> bool:
        """Check if resource is healthy."""
        # Check status
        if resource.status not in ["ACTIVE", "active"]:
            return False
        
        # Service-specific health checks
        if resource.service == "EC2":
            # For EC2, check if instance is running
            return resource.status == "ACTIVE"
        
        elif resource.service == "RDS":
            # For RDS, check if available
            return resource.status == "ACTIVE"
        
        elif resource.service == "ALB":
            # For ALB, check if active
            return resource.status == "ACTIVE"
        
        elif resource.service == "S3":
            # S3 buckets are always healthy if they exist
            return True
        
        return True
    
    def _validate_tags(self, resources: list[Resource]) -> tuple[bool, list[dict]]:
        """Validate required tags on resources."""
        required_tags = ["Application", "Environment", "Owner", "ManagedBy"]
        missing_tags = []
        
        for resource in resources:
            resource_missing_tags = []
            
            for tag in required_tags:
                if tag not in resource.tags:
                    resource_missing_tags.append(tag)
            
            if resource_missing_tags:
                missing_tags.append({
                    "resource_id": resource.aws_resource_id,
                    "resource_type": resource.service,
                    "missing_tags": resource_missing_tags,
                })
        
        tags_compliant = len(missing_tags) == 0
        
        return tags_compliant, missing_tags
    
    def _validate_security(self, resources: list[Resource]) -> tuple[bool, list[dict]]:
        """Validate security compliance of resources."""
        security_issues = []
        
        for resource in resources:
            # Check encryption
            if resource.service in ["EC2", "RDS", "S3"]:
                if resource.encrypted is False:
                    security_issues.append({
                        "resource_id": resource.aws_resource_id,
                        "resource_type": resource.service,
                        "issue": "Encryption not enabled",
                        "severity": "HIGH",
                    })
            
            # Check public exposure
            if resource.public_ip and resource.service == "RDS":
                security_issues.append({
                    "resource_id": resource.aws_resource_id,
                    "resource_type": resource.service,
                    "issue": "RDS instance is publicly accessible",
                    "severity": "CRITICAL",
                })
        
        security_compliant = len(security_issues) == 0
        
        return security_compliant, security_issues
    
    def load_terraform_outputs(self, workspace_path: str) -> dict:
        """
        Load Terraform outputs from workspace.
        
        Args:
            workspace_path: Path to Terraform workspace
            
        Returns:
            Terraform outputs
        """
        outputs_file = Path(workspace_path) / "outputs.json"
        
        if not outputs_file.exists():
            logger.warning(f"Outputs file not found: {outputs_file}")
            return {}
        
        try:
            with open(outputs_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load outputs: {e}")
            return {}
