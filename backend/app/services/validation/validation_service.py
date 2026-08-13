"""
Post-Deployment Validation Service.

Validates that deployed resources match expectations and are properly configured.
"""
import json
import logging
from pathlib import Path
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ValidationService:
    """
    Service for post-deployment validation.
    
    Validates:
    - Resources exist in AWS
    - Tags are correctly applied
    - Security configurations match requirements
    - Outputs are accessible
    - Resources are in expected state
    """
    
    def __init__(self):
        """Initialize validation service."""
        self.region = settings.aws_region
        
        if not settings.demo_mode:
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.s3_client = boto3.client('s3', region_name=self.region)
            self.elbv2_client = boto3.client('elbv2', region_name=self.region)
            self.rds_client = boto3.client('rds', region_name=self.region)
            self.tags_client = boto3.client('resourcegroupstaggingapi', region_name=self.region)
    
    def validate_deployment(
        self,
        request_id: str,
        workspace_path: str,
    ) -> dict[str, Any]:
        """
        Validate deployment.
        
        Args:
            request_id: Deployment request ID
            workspace_path: Path to Terraform workspace
            
        Returns:
            Validation results
        """
        logger.info(f"Validating deployment for request {request_id}")
        
        if settings.demo_mode:
            return self._demo_validation_results(request_id)
        
        results = {
            "request_id": request_id,
            "validation_status": "PASSED",
            "checks": [],
            "resources_validated": 0,
            "resources_failed": 0,
        }
        
        try:
            # Read Terraform outputs
            outputs = self._read_terraform_outputs(workspace_path)
            if not outputs:
                results["validation_status"] = "FAILED"
                results["checks"].append({
                    "check": "terraform_outputs",
                    "status": "FAILED",
                    "message": "No Terraform outputs found",
                })
                return results
            
            # Validate resources based on outputs
            for output_key, output_value in outputs.items():
                if not output_value or not isinstance(output_value, dict):
                    continue
                
                value = output_value.get("value")
                if not value:
                    continue
                
                # Determine resource type and validate
                if "instance_id" in output_key or "ec2" in output_key:
                    check = self._validate_ec2_instance(value, request_id)
                    results["checks"].append(check)
                    
                elif "bucket" in output_key or "s3" in output_key:
                    check = self._validate_s3_bucket(value, request_id)
                    results["checks"].append(check)
                    
                elif "load_balancer" in output_key or "alb" in output_key:
                    check = self._validate_alb(value, request_id)
                    results["checks"].append(check)
                    
                elif "vpc" in output_key:
                    check = self._validate_vpc(value, request_id)
                    results["checks"].append(check)
            
            # Count results
            results["resources_validated"] = len(results["checks"])
            results["resources_failed"] = sum(
                1 for c in results["checks"] if c["status"] == "FAILED"
            )
            
            if results["resources_failed"] > 0:
                results["validation_status"] = "FAILED"
            
            # Validate tags across all resources
            tag_check = self._validate_tags(request_id)
            results["checks"].append(tag_check)
            
            if tag_check["status"] == "FAILED":
                results["validation_status"] = "FAILED"
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            results["validation_status"] = "ERROR"
            results["checks"].append({
                "check": "validation_error",
                "status": "FAILED",
                "message": str(e),
            })
        
        return results
    
    def _read_terraform_outputs(self, workspace_path: str) -> dict[str, Any]:
        """Read Terraform outputs from state."""
        outputs_file = Path(workspace_path) / "outputs.json"
        
        if not outputs_file.exists():
            logger.warning(f"Outputs file not found: {outputs_file}")
            return {}
        
        try:
            with open(outputs_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read outputs: {e}")
            return {}
    
    def _validate_ec2_instance(
        self,
        instance_id: str | list[str],
        request_id: str,
    ) -> dict[str, Any]:
        """Validate EC2 instance exists and is properly configured."""
        instance_ids = [instance_id] if isinstance(instance_id, str) else instance_id
        
        try:
            response = self.ec2_client.describe_instances(InstanceIds=instance_ids)
            
            if not response['Reservations']:
                return {
                    "check": "ec2_instance_exists",
                    "resource_id": instance_id,
                    "status": "FAILED",
                    "message": "Instance not found",
                }
            
            instance = response['Reservations'][0]['Instances'][0]
            state = instance['State']['Name']
            
            # Check if running or pending
            if state not in ['running', 'pending']:
                return {
                    "check": "ec2_instance_state",
                    "resource_id": instance_id,
                    "status": "FAILED",
                    "message": f"Instance in unexpected state: {state}",
                }
            
            # Check IMDSv2
            metadata_options = instance.get('MetadataOptions', {})
            if metadata_options.get('HttpTokens') != 'required':
                return {
                    "check": "ec2_imdsv2",
                    "resource_id": instance_id,
                    "status": "FAILED",
                    "message": "IMDSv2 not enforced",
                }
            
            # Check monitoring
            monitoring = instance.get('Monitoring', {}).get('State')
            if monitoring != 'enabled':
                return {
                    "check": "ec2_monitoring",
                    "resource_id": instance_id,
                    "status": "WARNING",
                    "message": "Detailed monitoring not enabled",
                }
            
            return {
                "check": "ec2_instance",
                "resource_id": instance_id,
                "status": "PASSED",
                "message": f"Instance {state}, IMDSv2 enabled",
            }
            
        except ClientError as e:
            return {
                "check": "ec2_instance",
                "resource_id": instance_id,
                "status": "FAILED",
                "message": str(e),
            }
    
    def _validate_s3_bucket(self, bucket_name: str, request_id: str) -> dict[str, Any]:
        """Validate S3 bucket exists and is properly configured."""
        try:
            # Check bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            
            # Check encryption
            try:
                encryption = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
                if not encryption.get('ServerSideEncryptionConfiguration'):
                    return {
                        "check": "s3_encryption",
                        "resource_id": bucket_name,
                        "status": "FAILED",
                        "message": "Bucket encryption not configured",
                    }
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    return {
                        "check": "s3_encryption",
                        "resource_id": bucket_name,
                        "status": "FAILED",
                        "message": "Bucket encryption not configured",
                    }
            
            # Check public access block
            try:
                public_access = self.s3_client.get_public_access_block(Bucket=bucket_name)
                config = public_access.get('PublicAccessBlockConfiguration', {})
                
                if not all([
                    config.get('BlockPublicAcls'),
                    config.get('BlockPublicPolicy'),
                    config.get('IgnorePublicAcls'),
                    config.get('RestrictPublicBuckets'),
                ]):
                    return {
                        "check": "s3_public_access",
                        "resource_id": bucket_name,
                        "status": "FAILED",
                        "message": "Public access block not fully configured",
                    }
            except ClientError:
                return {
                    "check": "s3_public_access",
                    "resource_id": bucket_name,
                    "status": "FAILED",
                    "message": "Public access block not configured",
                }
            
            return {
                "check": "s3_bucket",
                "resource_id": bucket_name,
                "status": "PASSED",
                "message": "Bucket properly secured",
            }
            
        except ClientError as e:
            return {
                "check": "s3_bucket",
                "resource_id": bucket_name,
                "status": "FAILED",
                "message": str(e),
            }
    
    def _validate_alb(self, alb_arn: str, request_id: str) -> dict[str, Any]:
        """Validate ALB exists and is properly configured."""
        try:
            response = self.elbv2_client.describe_load_balancers(
                LoadBalancerArns=[alb_arn]
            )
            
            if not response['LoadBalancers']:
                return {
                    "check": "alb_exists",
                    "resource_id": alb_arn,
                    "status": "FAILED",
                    "message": "ALB not found",
                }
            
            alb = response['LoadBalancers'][0]
            state = alb['State']['Code']
            
            if state not in ['active', 'provisioning']:
                return {
                    "check": "alb_state",
                    "resource_id": alb_arn,
                    "status": "FAILED",
                    "message": f"ALB in unexpected state: {state}",
                }
            
            # Check attributes
            attrs_response = self.elbv2_client.describe_load_balancer_attributes(
                LoadBalancerArn=alb_arn
            )
            
            attrs = {a['Key']: a['Value'] for a in attrs_response['Attributes']}
            
            # Check drop_invalid_header_fields
            if attrs.get('routing.http.drop_invalid_header_fields.enabled') != 'true':
                return {
                    "check": "alb_security",
                    "resource_id": alb_arn,
                    "status": "WARNING",
                    "message": "ALB not configured to drop invalid headers",
                }
            
            return {
                "check": "alb",
                "resource_id": alb_arn,
                "status": "PASSED",
                "message": f"ALB {state}",
            }
            
        except ClientError as e:
            return {
                "check": "alb",
                "resource_id": alb_arn,
                "status": "FAILED",
                "message": str(e),
            }
    
    def _validate_vpc(self, vpc_id: str, request_id: str) -> dict[str, Any]:
        """Validate VPC exists."""
        try:
            response = self.ec2_client.describe_vpcs(VpcIds=[vpc_id])
            
            if not response['Vpcs']:
                return {
                    "check": "vpc_exists",
                    "resource_id": vpc_id,
                    "status": "FAILED",
                    "message": "VPC not found",
                }
            
            return {
                "check": "vpc",
                "resource_id": vpc_id,
                "status": "PASSED",
                "message": "VPC exists",
            }
            
        except ClientError as e:
            return {
                "check": "vpc",
                "resource_id": vpc_id,
                "status": "FAILED",
                "message": str(e),
            }
    
    def _validate_tags(self, request_id: str) -> dict[str, Any]:
        """Validate required tags are present on all resources."""
        try:
            # Query resources by RequestId tag
            response = self.tags_client.get_resources(
                TagFilters=[
                    {
                        'Key': 'RequestId',
                        'Values': [request_id],
                    }
                ]
            )
            
            resources = response.get('ResourceTagMappingList', [])
            
            if not resources:
                return {
                    "check": "resource_tags",
                    "status": "WARNING",
                    "message": "No resources found with RequestId tag",
                }
            
            required_tags = ['Application', 'Environment', 'Owner', 'ManagedBy']
            missing_tags = []
            
            for resource in resources:
                tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                
                for required_tag in required_tags:
                    if required_tag not in tags:
                        missing_tags.append({
                            "resource": resource['ResourceARN'],
                            "missing_tag": required_tag,
                        })
            
            if missing_tags:
                return {
                    "check": "resource_tags",
                    "status": "FAILED",
                    "message": f"Missing required tags on {len(missing_tags)} resource(s)",
                    "details": missing_tags[:5],  # Show first 5
                }
            
            return {
                "check": "resource_tags",
                "status": "PASSED",
                "message": f"All {len(resources)} resources properly tagged",
            }
            
        except ClientError as e:
            return {
                "check": "resource_tags",
                "status": "ERROR",
                "message": str(e),
            }
    
    def _demo_validation_results(self, request_id: str) -> dict[str, Any]:
        """Return demo validation results."""
        logger.warning(f"Demo mode: Returning simulated validation for {request_id}")
        
        return {
            "request_id": request_id,
            "validation_status": "PASSED",
            "checks": [
                {
                    "check": "ec2_instance",
                    "resource_id": "i-0123456789abcdef0",
                    "status": "PASSED",
                    "message": "Instance running, IMDSv2 enabled",
                },
                {
                    "check": "s3_bucket",
                    "resource_id": "my-app-bucket-12345",
                    "status": "PASSED",
                    "message": "Bucket properly secured",
                },
                {
                    "check": "resource_tags",
                    "status": "PASSED",
                    "message": "All 5 resources properly tagged",
                },
            ],
            "resources_validated": 3,
            "resources_failed": 0,
        }
