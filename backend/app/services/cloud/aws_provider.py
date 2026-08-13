"""
AWS Cloud Provider Implementation.

Implements BaseCloudProvider interface for AWS.
"""
import logging
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from .base_provider import BaseCloudProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class AWSProvider(BaseCloudProvider):
    """AWS cloud provider implementation."""
    
    def __init__(self):
        """Initialize AWS provider."""
        self.region = settings.aws_region
        
        if not settings.demo_mode:
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.s3_client = boto3.client('s3')
            self.pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    def get_provider_name(self) -> str:
        """Get cloud provider name."""
        return "aws"
    
    def validate_credentials(self) -> bool:
        """Validate AWS credentials."""
        if settings.demo_mode:
            return True
        
        try:
            sts = boto3.client('sts', region_name=self.region)
            sts.get_caller_identity()
            return True
        except ClientError:
            return False
    
    def get_module_path(self, service: str) -> str:
        """Get Terraform module path for AWS service."""
        service_category_map = {
            "ec2": "compute/ec2",
            "lambda": "serverless/lambda",
            "eks": "container/eks",
            "vpc": "networking/vpc",
            "security-group": "networking/security-group",
            "alb": "networking/alb",
            "s3": "storage/s3",
            "ebs": "storage/ebs",
            "rds": "database/rds",
            "dynamodb": "database/dynamodb",
        }
        
        category_path = service_category_map.get(service, service)
        return f"aws/{category_path}"
    
    def get_terraform_provider_config(self) -> dict[str, Any]:
        """Get Terraform AWS provider configuration."""
        return {
            "terraform": {
                "required_providers": {
                    "aws": {
                        "source": "hashicorp/aws",
                        "version": "~> 5.0"
                    }
                }
            },
            "provider": {
                "aws": {
                    "region": self.region,
                    "default_tags": {
                        "tags": {
                            "ManagedBy": "ai-cloud-platform",
                            "Terraform": "true"
                        }
                    }
                }
            }
        }
    
    def get_state_backend_config(
        self,
        request_id: str,
        environment: str,
    ) -> dict[str, Any]:
        """Get Terraform S3 backend configuration."""
        return {
            "backend": {
                "s3": {
                    "bucket": settings.s3_tfstate_bucket or "ai-cloud-platform-tfstate",
                    "key": f"deployments/{environment}/{request_id}/terraform.tfstate",
                    "region": self.region,
                    "encrypt": True,
                    "dynamodb_table": settings.dynamodb_lock_table or "ai-cloud-platform-tfstate-lock"
                }
            }
        }
    
    def validate_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """Validate AWS resource."""
        if settings.demo_mode:
            return {"status": "valid", "resource_id": resource_id}
        
        try:
            if resource_type in ["instance", "ec2"]:
                response = self.ec2_client.describe_instances(InstanceIds=[resource_id])
                if response['Reservations']:
                    instance = response['Reservations'][0]['Instances'][0]
                    return {
                        "status": "valid",
                        "resource_id": resource_id,
                        "state": instance['State']['Name']
                    }
            # Add more resource types as needed
            
            return {"status": "unknown", "resource_id": resource_id}
        
        except ClientError as e:
            return {"status": "error", "resource_id": resource_id, "error": str(e)}
    
    def get_resource_inventory(
        self,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Get AWS resource inventory."""
        # Implementation from InventoryService
        return []
    
    def get_security_findings(
        self,
        resource_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get AWS Security Hub findings."""
        if settings.demo_mode:
            return []
        
        try:
            security_hub = boto3.client('securityhub', region_name=self.region)
            
            filters_dict = {}
            if resource_id:
                filters_dict['ResourceId'] = [{'Value': resource_id, 'Comparison': 'EQUALS'}]
            
            response = security_hub.get_findings(Filters=filters_dict)
            return response.get('Findings', [])
        
        except ClientError:
            return []
    
    def estimate_cost(
        self,
        resources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Estimate AWS monthly cost."""
        # Basic cost estimation
        total_cost = 0.0
        breakdown = []
        
        for resource in resources:
            resource_type = resource.get('type')
            config = resource.get('configuration', {})
            
            if resource_type == 'ec2':
                instance_type = config.get('instance_type', 't3.micro')
                count = config.get('instance_count', 1)
                # Rough estimate: $30/month for t3.micro
                cost = 30 * count
                total_cost += cost
                breakdown.append({
                    "resource": "EC2",
                    "quantity": count,
                    "unit_cost": 30,
                    "total": cost
                })
        
        return {
            "provider": "aws",
            "total_monthly_cost": total_cost,
            "currency": "USD",
            "breakdown": breakdown,
            "note": "Rough estimate. Actual costs may vary."
        }
    
    def get_approved_regions(self) -> list[str]:
        """Get approved AWS regions."""
        return [
            "ap-south-1",
            "ap-southeast-1",
            "us-east-1"
        ]
    
    def validate_region(self, region: str) -> bool:
        """Validate AWS region."""
        return region in self.get_approved_regions()
    
    def map_generic_service(self, service_category: str) -> str:
        """Map generic service to AWS service."""
        mapping = {
            "compute": "ec2",
            "networking": "vpc",
            "storage": "s3",
            "database": "rds",
            "container": "eks",
            "serverless": "lambda",
            "load_balancer": "alb"
        }
        return mapping.get(service_category, service_category)
    
    def get_authentication_config(self) -> dict[str, Any]:
        """Get AWS authentication configuration."""
        return {
            "type": "oidc",
            "provider": "Azure DevOps",
            "service_connection": "aws-terraform-apply",
            "role_arn": f"arn:aws:iam::ACCOUNT_ID:role/TerraformApplyRole"
        }
