"""
Inventory API endpoints.

Provides endpoints for AWS resource inventory management:
- Get resource inventory
- Get resource details
- Get resource summary
- Search resources
- Get deployment resources
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.inventory import InventoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

# Dependencies
inventory_service = InventoryService()


@router.get("/summary")
def get_inventory_summary() -> dict[str, Any]:
    """
    Get resource inventory summary.
    
    Returns:
        Summary statistics of all resources
    """
    summary = inventory_service.get_summary()
    
    return {
        "total_resources": summary.total_resources,
        "by_service": summary.by_service,
        "by_environment": summary.by_environment,
        "by_status": summary.by_status,
        "by_managed": summary.by_managed,
        "by_compliance": summary.by_compliance,
    }


@router.get("/resources")
def list_resources(
    service: str | None = Query(None, description="Filter by service (EC2, S3, RDS, etc.)"),
    environment: str | None = Query(None, description="Filter by environment (dev, uat, prod)"),
    status: str | None = Query(None, description="Filter by status (ACTIVE, STOPPED, etc.)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
) -> dict[str, Any]:
    """
    List all resources with optional filters.
    
    Args:
        service: Service filter
        environment: Environment filter
        status: Status filter
        limit: Maximum results
        
    Returns:
        List of resources
    """
    resources = list(inventory_service._resources.values())
    
    # Apply filters
    if service:
        resources = [r for r in resources if r.service.upper() == service.upper()]
    
    if environment:
        resources = [r for r in resources if r.environment.lower() == environment.lower()]
    
    if status:
        resources = [r for r in resources if r.status == status.upper()]
    
    # Limit results
    resources = resources[:limit]
    
    return {
        "resources": [
            {
                "resource_id": r.resource_id,
                "aws_resource_id": r.aws_resource_id,
                "service": r.service,
                "resource_type": r.resource_type,
                "resource_name": r.resource_name,
                "environment": r.environment,
                "application": r.application,
                "status": r.status,
                "aws_region": r.aws_region,
                "managed_by": r.managed_by,
                "compliance_status": r.compliance_status,
                "created_at": r.created_at.isoformat(),
                "last_seen": r.last_seen.isoformat(),
            }
            for r in resources
        ],
        "count": len(resources),
    }


@router.get("/resources/{resource_id}")
def get_resource_details(resource_id: str) -> dict[str, Any]:
    """
    Get detailed information about a resource.
    
    Args:
        resource_id: Resource ID
        
    Returns:
        Resource details
    """
    resource = inventory_service.get_resource(resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource {resource_id} not found",
        )
    
    return {
        "resource_id": resource.resource_id,
        "aws_resource_id": resource.aws_resource_id,
        "aws_resource_type": resource.aws_resource_type,
        "aws_resource_arn": resource.aws_resource_arn,
        "service": resource.service,
        "resource_type": resource.resource_type,
        "resource_name": resource.resource_name,
        "aws_account_id": resource.aws_account_id,
        "aws_region": resource.aws_region,
        "availability_zone": resource.availability_zone,
        "application": resource.application,
        "environment": resource.environment,
        "owner": resource.owner,
        "managed_by": resource.managed_by,
        "deployment_request_id": resource.deployment_request_id,
        "terraform_address": resource.terraform_address,
        "status": resource.status,
        "compliance_status": resource.compliance_status,
        "configuration": resource.configuration,
        "security_groups": resource.security_groups,
        "subnet_id": resource.subnet_id,
        "vpc_id": resource.vpc_id,
        "public_ip": resource.public_ip,
        "private_ip": resource.private_ip,
        "encrypted": resource.encrypted,
        "instance_type": resource.instance_type,
        "estimated_monthly_cost": resource.estimated_monthly_cost,
        "tags": resource.tags,
        "created_at": resource.created_at.isoformat(),
        "last_seen": resource.last_seen.isoformat(),
        "terminated_at": resource.terminated_at.isoformat() if resource.terminated_at else None,
        "compliance_findings": resource.compliance_findings,
    }


@router.get("/deployments/{deployment_id}/resources")
def get_deployment_resources(deployment_id: str) -> dict[str, Any]:
    """
    Get all resources for a deployment.
    
    Args:
        deployment_id: Deployment request ID
        
    Returns:
        List of resources created by deployment
    """
    resources = inventory_service.get_resources_by_deployment(deployment_id)
    
    return {
        "deployment_id": deployment_id,
        "resources": [
            {
                "resource_id": r.resource_id,
                "aws_resource_id": r.aws_resource_id,
                "service": r.service,
                "resource_type": r.resource_type,
                "resource_name": r.resource_name,
                "status": r.status,
                "aws_region": r.aws_region,
                "created_at": r.created_at.isoformat(),
            }
            for r in resources
        ],
        "count": len(resources),
    }


@router.post("/discover/{deployment_id}")
def discover_deployment_resources(deployment_id: str) -> dict[str, Any]:
    """
    Trigger resource discovery for a deployment.
    
    Args:
        deployment_id: Deployment request ID
        
    Returns:
        Discovered resources
    """
    logger.info(f"Triggering resource discovery for deployment {deployment_id}")
    
    resources = inventory_service.discover_resources(deployment_id)
    
    return {
        "deployment_id": deployment_id,
        "resources_discovered": len(resources),
        "resources": [
            {
                "resource_id": r.resource_id,
                "aws_resource_id": r.aws_resource_id,
                "service": r.service,
                "resource_type": r.resource_type,
                "status": r.status,
            }
            for r in resources
        ],
    }
