"""
Approval API endpoints.

Provides endpoints for managing deployment approvals:
- Create approval workflows
- Get pending approvals
- Approve/reject deployments
- Get approval history
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models.approval import (
    ApprovalDecision,
    ApprovalLevel,
    ApprovalRequest,
)
from app.services.approval import ApprovalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])

# Dependencies
approval_service = ApprovalService()


class CreateApprovalWorkflowRequest(BaseModel):
    """Request to create approval workflow."""
    request_id: str
    environment: str
    deployment_risk: str = "LOW"
    application_name: str
    resources: list[dict] = []
    estimated_cost: float | None = None
    security_status: str = "UNKNOWN"


class ApproveRequest(BaseModel):
    """Request to approve deployment."""
    approver_id: str
    approver_name: str
    approver_email: str
    comment: str | None = None


class RejectRequest(BaseModel):
    """Request to reject deployment."""
    approver_id: str
    approver_name: str
    approver_email: str
    reason: str


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
def create_approval_workflow(payload: CreateApprovalWorkflowRequest) -> dict[str, Any]:
    """
    Create approval workflow for deployment request.
    
    Args:
        payload: Workflow creation request
        
    Returns:
        Created workflow details
    """
    logger.info(f"Creating approval workflow for request {payload.request_id}")
    
    request = ApprovalRequest(
        request_id=payload.request_id,
        environment=payload.environment,
        deployment_risk=payload.deployment_risk,
        application_name=payload.application_name,
        resources=payload.resources,
        estimated_cost=payload.estimated_cost,
        security_status=payload.security_status,
    )
    
    workflow = approval_service.create_workflow(request)
    
    # Notify approvers
    approval_service.notify_approvers(workflow)
    
    return {
        "workflow_id": workflow.workflow_id,
        "request_id": workflow.request_id,
        "environment": workflow.environment,
        "required_approvals": [level.value for level in workflow.required_approvals],
        "approvals": [
            {
                "approval_id": a.approval_id,
                "level": a.level.value,
                "status": a.status.value,
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            }
            for a in workflow.approvals
        ],
        "all_approved": workflow.all_approved,
        "can_deploy": workflow.can_deploy(),
    }


@router.get("/requests/{request_id}")
def get_approval_workflow(request_id: str) -> dict[str, Any]:
    """
    Get approval workflow for request.
    
    Args:
        request_id: Deployment request ID
        
    Returns:
        Workflow details
    """
    workflow = approval_service.get_workflow(request_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval workflow not found for request {request_id}",
        )
    
    return {
        "workflow_id": workflow.workflow_id,
        "request_id": workflow.request_id,
        "environment": workflow.environment,
        "required_approvals": [level.value for level in workflow.required_approvals],
        "approvals": [
            {
                "approval_id": a.approval_id,
                "level": a.level.value,
                "status": a.status.value,
                "approver_name": a.approver_name,
                "approver_email": a.approver_email,
                "approved_at": a.approved_at.isoformat() if a.approved_at else None,
                "rejected_at": a.rejected_at.isoformat() if a.rejected_at else None,
                "decision_comment": a.decision_comment,
                "rejection_reason": a.rejection_reason,
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            }
            for a in workflow.approvals
        ],
        "all_approved": workflow.all_approved,
        "any_rejected": workflow.any_rejected,
        "can_deploy": workflow.can_deploy(),
        "is_complete": workflow.is_complete(),
    }


@router.post("/requests/{request_id}/approve/{level}")
def approve_deployment(
    request_id: str,
    level: str,
    payload: ApproveRequest,
) -> dict[str, Any]:
    """
    Approve deployment for specific approval level.
    
    Args:
        request_id: Deployment request ID
        level: Approval level (SECURITY, TEAM_LEAD, MANAGER, PLATFORM_ADMIN)
        payload: Approval details
        
    Returns:
        Updated workflow
    """
    try:
        approval_level = ApprovalLevel(level.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid approval level: {level}",
        )
    
    decision = ApprovalDecision(
        approve=True,
        comment=payload.comment,
        approver_id=payload.approver_id,
        approver_name=payload.approver_name,
        approver_email=payload.approver_email,
    )
    
    try:
        workflow = approval_service.process_decision(
            request_id=request_id,
            level=approval_level,
            decision=decision,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return {
        "message": "Approval processed successfully",
        "workflow_id": workflow.workflow_id,
        "all_approved": workflow.all_approved,
        "can_deploy": workflow.can_deploy(),
    }


@router.post("/requests/{request_id}/reject/{level}")
def reject_deployment(
    request_id: str,
    level: str,
    payload: RejectRequest,
) -> dict[str, Any]:
    """
    Reject deployment for specific approval level.
    
    Args:
        request_id: Deployment request ID
        level: Approval level
        payload: Rejection details
        
    Returns:
        Updated workflow
    """
    try:
        approval_level = ApprovalLevel(level.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid approval level: {level}",
        )
    
    decision = ApprovalDecision(
        approve=False,
        comment=payload.reason,
        approver_id=payload.approver_id,
        approver_name=payload.approver_name,
        approver_email=payload.approver_email,
    )
    
    try:
        workflow = approval_service.process_decision(
            request_id=request_id,
            level=approval_level,
            decision=decision,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return {
        "message": "Rejection processed successfully",
        "workflow_id": workflow.workflow_id,
        "any_rejected": workflow.any_rejected,
        "can_deploy": workflow.can_deploy(),
    }


@router.get("/pending")
def get_pending_approvals() -> dict[str, Any]:
    """
    Get all pending approvals.
    
    Returns:
        List of pending approvals
    """
    # In production, this would filter by current user
    approvals = approval_service.get_pending_approvals(approver_id="current_user")
    
    return {
        "pending_approvals": [
            {
                "approval_id": a.approval_id,
                "request_id": a.request_id,
                "level": a.level.value,
                "created_at": a.created_at.isoformat(),
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            }
            for a in approvals
        ],
        "count": len(approvals),
    }


@router.get("/requests/{request_id}/history")
def get_approval_history(request_id: str) -> dict[str, Any]:
    """
    Get approval history for request.
    
    Args:
        request_id: Deployment request ID
        
    Returns:
        Approval history
    """
    approvals = approval_service.get_approval_history(request_id)
    
    return {
        "request_id": request_id,
        "approvals": [
            {
                "approval_id": a.approval_id,
                "level": a.level.value,
                "status": a.status.value,
                "approver_name": a.approver_name,
                "approver_email": a.approver_email,
                "approved_at": a.approved_at.isoformat() if a.approved_at else None,
                "rejected_at": a.rejected_at.isoformat() if a.rejected_at else None,
                "decision_comment": a.decision_comment,
                "rejection_reason": a.rejection_reason,
                "created_at": a.created_at.isoformat(),
            }
            for a in approvals
        ],
    }


@router.get("/statistics")
def get_approval_statistics() -> dict[str, Any]:
    """
    Get approval statistics.
    
    Returns:
        Approval metrics
    """
    return approval_service.get_approval_statistics()
