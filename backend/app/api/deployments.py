"""
Deployment API endpoints.

Provides endpoints for managing infrastructure deployments:
- Trigger deployments
- Get deployment status
- Get deployment logs
- Update deployment status (called by Azure DevOps pipelines)
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models.deployment import DeploymentRequest, DeploymentStatus
from app.repositories.request_repository import get_request_repository
from app.services.azure_devops import PipelineService
from app.services.terraform_service import TerraformService
from app.terraform.generator import TerraformGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deployments", tags=["deployments"])

# Dependencies
request_repo = get_request_repository()
pipeline_service = PipelineService()
terraform_service = TerraformService()


class TriggerDeploymentRequest(BaseModel):
    """Request to trigger a deployment."""
    request_id: str


class DeploymentStatusUpdate(BaseModel):
    """Deployment status update from Azure DevOps pipeline."""
    status: str
    message: str | None = None
    pipeline_run_id: str | None = None
    deployment_summary: dict[str, Any] | None = None
    completed_at: str | None = None
    failed_at: str | None = None


class PlanUpdate(BaseModel):
    """Terraform plan update from Azure DevOps pipeline."""
    status: str
    plan_summary: dict[str, Any] | None = None
    cost_estimate: dict[str, Any] | None = None
    pipeline_run_id: str | None = None
    plan_artifact: str | None = None


class SecurityUpdate(BaseModel):
    """Security scan update from Azure DevOps pipeline."""
    scan_type: str
    status: str
    results: dict[str, Any]
    pipeline_run_id: str | None = None


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_deployment(payload: TriggerDeploymentRequest) -> dict[str, Any]:
    """
    Trigger deployment for an approved request.
    
    This generates Terraform configuration and triggers Azure DevOps pipeline.
    
    Args:
        payload: Request containing deployment request ID
        
    Returns:
        Deployment status and pipeline information
    """
    request_id = payload.request_id
    
    logger.info(f"Triggering deployment for request {request_id}")
    
    # Get request
    deployment_request = request_repo.get(request_id)
    if not deployment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found",
        )
    
    # Check if already deployed
    if deployment_request.status == DeploymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request has already been deployed",
        )
    
    try:
        # Generate Terraform workspace
        workspace_path = terraform_service.prepare_workspace(deployment_request)
        
        logger.info(f"Terraform workspace created: {workspace_path}")
        
        # Update status
        deployment_request.status = DeploymentStatus.PENDING
        request_repo.create(deployment_request)
        
        # Trigger Azure DevOps pipeline
        pipeline_run = pipeline_service.trigger_deployment(deployment_request)
        
        # Store pipeline run ID
        deployment_request.pipeline_run_id = str(pipeline_run.get("id", ""))
        deployment_request.status = DeploymentStatus.DEPLOYING
        request_repo.create(deployment_request)
        
        return {
            "request_id": request_id,
            "status": deployment_request.status.value,
            "pipeline_run_id": deployment_request.pipeline_run_id,
            "pipeline_url": pipeline_run.get("url"),
            "workspace_path": workspace_path,
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger deployment: {e}")
        deployment_request.status = DeploymentStatus.FAILED
        request_repo.create(deployment_request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger deployment: {str(e)}",
        )


@router.get("/{request_id}")
def get_deployment(request_id: str) -> dict[str, Any]:
    """
    Get deployment details.
    
    Args:
        request_id: Deployment request ID
        
    Returns:
        Deployment details including status, resources, and logs
    """
    deployment_request = request_repo.get(request_id)
    if not deployment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {request_id} not found",
        )
    
    result = {
        "request_id": deployment_request.request_id,
        "application_name": deployment_request.application_name,
        "environment": deployment_request.environment,
        "status": deployment_request.status.value,
        "created_by": deployment_request.created_by,
        "created_at": deployment_request.created_at.isoformat() if deployment_request.created_at else None,
        "pipeline_run_id": deployment_request.pipeline_run_id,
    }
    
    # Get pipeline status if running
    if deployment_request.pipeline_run_id and deployment_request.status == DeploymentStatus.DEPLOYING:
        try:
            run_id = int(deployment_request.pipeline_run_id)
            pipeline_status = pipeline_service.get_pipeline_status(run_id)
            result["pipeline_status"] = pipeline_status
        except Exception as e:
            logger.warning(f"Failed to get pipeline status: {e}")
    
    return result


@router.get("/{request_id}/status")
def get_deployment_status(request_id: str) -> dict[str, Any]:
    """
    Get current deployment status.
    
    Args:
        request_id: Deployment request ID
        
    Returns:
        Current deployment status
    """
    deployment_request = request_repo.get(request_id)
    if not deployment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {request_id} not found",
        )
    
    return {
        "request_id": request_id,
        "status": deployment_request.status.value,
        "pipeline_run_id": deployment_request.pipeline_run_id,
    }


@router.put("/{request_id}/status")
def update_deployment_status(request_id: str, update: DeploymentStatusUpdate) -> dict[str, str]:
    """
    Update deployment status.
    
    Called by Azure DevOps pipeline to update deployment status.
    
    Args:
        request_id: Deployment request ID
        update: Status update
        
    Returns:
        Success message
    """
    logger.info(f"Updating status for deployment {request_id}: {update.status}")
    
    deployment_request = request_repo.get(request_id)
    if not deployment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {request_id} not found",
        )
    
    # Map status string to enum
    try:
        new_status = DeploymentStatus(update.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {update.status}",
        )
    
    deployment_request.status = new_status
    if update.pipeline_run_id:
        deployment_request.pipeline_run_id = update.pipeline_run_id
    
    request_repo.create(deployment_request)
    
    logger.info(f"Deployment {request_id} status updated to {new_status.value}")
    
    return {"message": f"Status updated to {new_status.value}"}


@router.get("/{request_id}/logs")
def get_deployment_logs(request_id: str) -> dict[str, Any]:
    """
    Get deployment logs from Azure DevOps pipeline.
    
    Args:
        request_id: Deployment request ID
        
    Returns:
        Pipeline execution logs
    """
    deployment_request = request_repo.get(request_id)
    if not deployment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {request_id} not found",
        )
    
    if not deployment_request.pipeline_run_id:
        return {
            "request_id": request_id,
            "logs": [],
            "message": "No pipeline run associated with this deployment",
        }
    
    try:
        run_id = int(deployment_request.pipeline_run_id)
        logs = pipeline_service.get_deployment_logs(run_id)
        
        return {
            "request_id": request_id,
            "pipeline_run_id": deployment_request.pipeline_run_id,
            "logs": logs,
        }
        
    except Exception as e:
        logger.error(f"Failed to get deployment logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}",
        )


@router.post("/{request_id}/plan")
def update_plan(request_id: str, update: PlanUpdate) -> dict[str, str]:
    """
    Update Terraform plan information.
    
    Called by Azure DevOps pipeline after plan generation.
    
    Args:
        request_id: Deployment request ID
        update: Plan update
        
    Returns:
        Success message
    """
    logger.info(f"Updating plan for deployment {request_id}")
    
    deployment_request = request_repo.get(request_id)
    if not deployment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {request_id} not found",
        )
    
    # Store plan information (in production, this would go to DynamoDB)
    logger.info(f"Plan summary: {update.plan_summary}")
    logger.info(f"Cost estimate: {update.cost_estimate}")
    
    return {"message": "Plan information updated"}


@router.post("/{request_id}/security")
def update_security_scan(request_id: str, update: SecurityUpdate) -> dict[str, str]:
    """
    Update security scan results.
    
    Called by Azure DevOps pipeline after security scanning.
    
    Args:
        request_id: Deployment request ID
        update: Security scan update
        
    Returns:
        Success message
    """
    logger.info(f"Updating security scan for deployment {request_id}: {update.scan_type}")
    
    deployment_request = request_repo.get(request_id)
    if not deployment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment {request_id} not found",
        )
    
    # Store security scan results (in production, this would go to DynamoDB)
    logger.info(f"{update.scan_type} scan completed with status: {update.status}")
    
    return {"message": f"{update.scan_type} scan results updated"}
