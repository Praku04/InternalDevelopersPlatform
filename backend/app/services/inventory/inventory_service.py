"""
Resource Inventory Service.

Tracks and manages infrastructure resources deployed through the platform.
"""
import logging
from datetime import datetime
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class InventoryService:
    """
    Service for managing resource inventory.
    
    Tracks:
    - All AWS resources created by the platform
    - Resource metadata (application, environment, owner)
    - Resource state and compliance
    - Cost allocation tags
    - Drift detection
    """
    
    def __init__(self):
        """Initialize inventory service."""
        self.region = settings.aws_region
        
        if not settings.demo_mode:
            self.config_client = boto3.client('config', region_name=self.region)
            self.tags_client = boto3.client('resourcegroupstaggingapi', region_name=self.region)
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.s3_client = boto3.client('s3')
        
        # In-memory inventory (would be DynamoDB in production)
        self._inventory: dict[str, dict[str, Any]] = {}
    
    def record_deployment(
        self,
        request_id: str,
        resources: list[dict[str, Any]],
        deployment_info: dict[str, Any],
    ):
        """
        Record deployed resources in inventory.
        
        Args:
            request_id: Deployment request ID
            resources: List of deployed resources
            deployment_info: Deployment metadata
        """
        logger.info(f"Recording {len(resources)} resources for request {request_id}")
        
        for resource in resources:
            resource_id = resource.get('values', {}).get('id') or resource.get('address')
            
            if not resource_id:
                continue
            
            inventory_record = {
                "resource_id": resource_id,
                "resource_type": resource.get('type'),
                "resource_name": resource.get('name'),
                "request_id": request_id,
                "application": deployment_info.get('application_name'),
                "environment": deployment_info.get('environment'),
                "owner": deployment_info.get('created_by'),
                "region": deployment_info.get('aws_region', self.region),
                "account_id": deployment_info.get('aws_account_id'),
                "created_at": datetime.utcnow().isoformat(),
                "managed_by": "ai-cloud-platform",
                "terraform_managed": True,
                "compliance_status": "UNKNOWN",
                "drift_status": "UNKNOWN",
                "tags": resource.get('values', {}).get('tags', {}),
            }
            
            self._inventory[resource_id] = inventory_record
            
            logger.debug(f"Recorded resource: {resource_id}")
    
    def get_resource(self, resource_id: str) -> Optional[dict[str, Any]]:
        """
        Get resource from inventory.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Resource record if found
        """
        return self._inventory.get(resource_id)
    
    def query_resources(
        self,
        application: Optional[str] = None,
        environment: Optional[str] = None,
        resource_type: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query resources with filters.
        
        Args:
            application: Filter by application
            environment: Filter by environment
            resource_type: Filter by resource type
            owner: Filter by owner
            
        Returns:
            List of matching resources
        """
        results = []
        
        for resource in self._inventory.values():
            if application and resource.get('application') != application:
                continue
            if environment and resource.get('environment') != environment:
                continue
            if resource_type and resource.get('resource_type') != resource_type:
                continue
            if owner and resource.get('owner') != owner:
                continue
            
            results.append(resource)
        
        return results
    
    def discover_unmanaged_resources(self) -> list[dict[str, Any]]:
        """
        Discover resources not managed by the platform.
        
        Returns:
            List of unmanaged resources
        """
        if settings.demo_mode:
            return []
        
        unmanaged = []
        
        try:
            # Query all resources, exclude those with ManagedBy=ai-cloud-platform tag
            response = self.tags_client.get_resources(
                ResourceTypeFilters=[
                    'ec2:instance',
                    'ec2:vpc',
                    'ec2:security-group',
                    's3:bucket',
                    'rds:db',
                    'elasticloadbalancing:loadbalancer',
                ]
            )
            
            for resource in response.get('ResourceTagMappingList', []):
                tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                
                # Check if managed by platform
                if tags.get('ManagedBy') != 'ai-cloud-platform':
                    unmanaged.append({
                        'resource_arn': resource['ResourceARN'],
                        'tags': tags,
                        'managed_by': tags.get('ManagedBy', 'UNKNOWN'),
                    })
            
            logger.info(f"Found {len(unmanaged)} unmanaged resources")
            return unmanaged
            
        except ClientError as e:
            logger.error(f"Failed to discover unmanaged resources: {e}")
            return []
    
    def get_inventory_summary(self) -> dict[str, Any]:
        """
        Get inventory summary statistics.
        
        Returns:
            Summary statistics
        """
        total = len(self._inventory)
        
        # Count by type
        by_type = {}
        by_environment = {}
        by_application = {}
        
        for resource in self._inventory.values():
            # By type
            rtype = resource.get('resource_type', 'unknown')
            by_type[rtype] = by_type.get(rtype, 0) + 1
            
            # By environment
            env = resource.get('environment', 'unknown')
            by_environment[env] = by_environment.get(env, 0) + 1
            
            # By application
            app = resource.get('application', 'unknown')
            by_application[app] = by_application.get(app, 0) + 1
        
        return {
            "total_resources": total,
            "by_type": by_type,
            "by_environment": by_environment,
            "by_application": by_application,
            "managed_resources": total,  # All in inventory are managed
            "unmanaged_resources": 0,  # Would query AWS for unmanaged
        }
    
    def sync_with_aws_config(self):
        """
        Sync inventory with AWS Config.
        
        Updates compliance status based on AWS Config rules.
        """
        if settings.demo_mode:
            logger.warning("Demo mode: Skipping AWS Config sync")
            return
        
        try:
            # Get compliance status from AWS Config
            for resource_id, resource in self._inventory.items():
                resource_type = resource.get('resource_type')
                
                # Map Terraform resource type to AWS Config resource type
                config_resource_type = self._map_to_config_type(resource_type)
                
                if not config_resource_type:
                    continue
                
                try:
                    response = self.config_client.get_compliance_details_by_resource(
                        ResourceType=config_resource_type,
                        ResourceId=resource_id,
                    )
                    
                    evaluation_results = response.get('EvaluationResults', [])
                    
                    if not evaluation_results:
                        resource['compliance_status'] = 'NOT_EVALUATED'
                        continue
                    
                    # Check if any rules failed
                    has_non_compliant = any(
                        result.get('ComplianceType') == 'NON_COMPLIANT'
                        for result in evaluation_results
                    )
                    
                    resource['compliance_status'] = 'NON_COMPLIANT' if has_non_compliant else 'COMPLIANT'
                    resource['last_compliance_check'] = datetime.utcnow().isoformat()
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotDiscoveredException':
                        resource['compliance_status'] = 'NOT_FOUND'
                    else:
                        logger.warning(f"Failed to check compliance for {resource_id}: {e}")
            
            logger.info("AWS Config sync completed")
            
        except Exception as e:
            logger.error(f"Failed to sync with AWS Config: {e}")
    
    def _map_to_config_type(self, terraform_type: str) -> Optional[str]:
        """Map Terraform resource type to AWS Config resource type."""
        mapping = {
            'aws_instance': 'AWS::EC2::Instance',
            'aws_vpc': 'AWS::EC2::VPC',
            'aws_security_group': 'AWS::EC2::SecurityGroup',
            'aws_s3_bucket': 'AWS::S3::Bucket',
            'aws_db_instance': 'AWS::RDS::DBInstance',
            'aws_lb': 'AWS::ElasticLoadBalancingV2::LoadBalancer',
        }
        return mapping.get(terraform_type)
    
    def export_inventory(self, format: str = 'json') -> str:
        """
        Export inventory to file.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Export file path or content
        """
        import json
        
        if format == 'json':
            return json.dumps(list(self._inventory.values()), indent=2)
        
        # CSV export would go here
        return ""
