"""
Approval Service.

Manages approval workflows for deployment requests.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.models.approval import (
    Approval,
    ApprovalDecision,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalWorkflow,
    get_required_approvals,
)

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Service for managing deployment approval workflows.
    
    Responsibilities:
    - Create approval workflows based on environment and risk
    - Process approval decisions
    - Track approval status
    - Notify approvers
    - Handle approval timeouts
    """
    
    def __init__(self):
        """Initialize approval service."""
        # In production, this would use DynamoDB
        self._workflows: dict[str, ApprovalWorkflow] = {}
        self._approvals: dict[str, Approval] = {}
    
    def create_workflow(self, request: ApprovalRequest) -> ApprovalWorkflow:
        """
        Create approval workflow for deployment request.
        
        Args:
            request: Approval request with deployment details
            
        Returns:
            Created approval workflow
        """
        logger.info(f"Creating approval workflow for request {request.request_id}")
        
        # Determine required approvals
        required_approvals = get_required_approvals(
            request.environment,
            request.deployment_risk,
        )
        
        # Create workflow
        workflow = ApprovalWorkflow(
            request_id=request.request_id,
            environment=request.environment,
            required_approvals=required_approvals,
        )
        
        # Create approval records for each required level
        for level in required_approvals:
            approval = Approval(
                request_id=request.request_id,
                level=level,
                status=ApprovalStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(days=7),  # 7 day timeout
            )
            self._approvals[approval.approval_id] = approval
            workflow.add_approval(approval)
        
        # Store workflow
        self._workflows[workflow.workflow_id] = workflow
        
        logger.info(
            f"Workflow created: {workflow.workflow_id}, "
            f"Required approvals: {required_approvals}"
        )
        
        return workflow
    
    def get_workflow(self, request_id: str) -> Optional[ApprovalWorkflow]:
        """
        Get approval workflow for request.
        
        Args:
            request_id: Deployment request ID
            
        Returns:
            Approval workflow if found
        """
        for workflow in self._workflows.values():
            if workflow.request_id == request_id:
                return workflow
        return None
    
    def process_decision(
        self,
        request_id: str,
        level: ApprovalLevel,
        decision: ApprovalDecision,
    ) -> ApprovalWorkflow:
        """
        Process approval decision.
        
        Args:
            request_id: Deployment request ID
            level: Approval level
            decision: Approval decision
            
        Returns:
            Updated workflow
            
        Raises:
            ValueError: If workflow not found or approval already processed
        """
        logger.info(
            f"Processing approval decision for request {request_id}, "
            f"level {level}, approve={decision.approve}"
        )
        
        # Get workflow
        workflow = self.get_workflow(request_id)
        if not workflow:
            raise ValueError(f"Workflow not found for request {request_id}")
        
        # Find pending approval for this level
        approval = None
        for a in workflow.approvals:
            if a.level == level and a.status == ApprovalStatus.PENDING:
                approval = a
                break
        
        if not approval:
            raise ValueError(
                f"No pending approval found for level {level} in request {request_id}"
            )
        
        # Update approval
        if decision.approve:
            approval.status = ApprovalStatus.APPROVED
            approval.approved_at = datetime.utcnow()
        else:
            approval.status = ApprovalStatus.REJECTED
            approval.rejected_at = datetime.utcnow()
            approval.rejection_reason = decision.comment
        
        approval.approver_id = decision.approver_id
        approval.approver_name = decision.approver_name
        approval.approver_email = decision.approver_email
        approval.decision_comment = decision.comment
        
        # Update workflow status
        workflow._update_status()
        
        logger.info(
            f"Approval processed: {approval.approval_id}, "
            f"Status: {approval.status}, "
            f"Workflow complete: {workflow.is_complete()}"
        )
        
        return workflow
    
    def check_expired_approvals(self):
        """
        Check and mark expired approvals.
        
        Should be run periodically (e.g., every hour).
        """
        now = datetime.utcnow()
        expired_count = 0
        
        for approval in self._approvals.values():
            if (
                approval.status == ApprovalStatus.PENDING
                and approval.expires_at
                and now > approval.expires_at
            ):
                approval.status = ApprovalStatus.EXPIRED
                expired_count += 1
                
                # Update workflow
                workflow = self.get_workflow(approval.request_id)
                if workflow:
                    workflow._update_status()
                
                logger.warning(
                    f"Approval expired: {approval.approval_id}, "
                    f"Request: {approval.request_id}, "
                    f"Level: {approval.level}"
                )
        
        if expired_count > 0:
            logger.info(f"Marked {expired_count} approvals as expired")
    
    def get_pending_approvals(self, approver_id: str) -> list[Approval]:
        """
        Get pending approvals for an approver.
        
        Args:
            approver_id: Approver user ID
            
        Returns:
            List of pending approvals
        """
        # In production, this would query DynamoDB with proper indexing
        # For now, return all pending approvals (would filter by approver)
        return [
            approval
            for approval in self._approvals.values()
            if approval.status == ApprovalStatus.PENDING
        ]
    
    def get_approval_history(self, request_id: str) -> list[Approval]:
        """
        Get approval history for request.
        
        Args:
            request_id: Deployment request ID
            
        Returns:
            List of approvals
        """
        return [
            approval
            for approval in self._approvals.values()
            if approval.request_id == request_id
        ]
    
    def cancel_workflow(self, request_id: str):
        """
        Cancel approval workflow.
        
        Args:
            request_id: Deployment request ID
        """
        workflow = self.get_workflow(request_id)
        if not workflow:
            return
        
        # Cancel all pending approvals
        for approval in workflow.approvals:
            if approval.status == ApprovalStatus.PENDING:
                approval.status = ApprovalStatus.CANCELED
        
        workflow._update_status()
        
        logger.info(f"Workflow canceled for request {request_id}")
    
    def notify_approvers(self, workflow: ApprovalWorkflow):
        """
        Notify approvers that their approval is required.
        
        Args:
            workflow: Approval workflow
        """
        # In production, this would send notifications via:
        # - Email
        # - Slack
        # - Microsoft Teams
        # - In-app notifications
        
        for approval in workflow.approvals:
            if approval.status == ApprovalStatus.PENDING:
                logger.info(
                    f"Notification would be sent for approval: {approval.approval_id}, "
                    f"Level: {approval.level}, "
                    f"Request: {approval.request_id}"
                )
                # TODO: Implement actual notification
    
    def get_approval_statistics(self) -> dict:
        """
        Get approval statistics.
        
        Returns:
            Dictionary with approval metrics
        """
        total_approvals = len(self._approvals)
        pending = sum(
            1 for a in self._approvals.values()
            if a.status == ApprovalStatus.PENDING
        )
        approved = sum(
            1 for a in self._approvals.values()
            if a.status == ApprovalStatus.APPROVED
        )
        rejected = sum(
            1 for a in self._approvals.values()
            if a.status == ApprovalStatus.REJECTED
        )
        expired = sum(
            1 for a in self._approvals.values()
            if a.status == ApprovalStatus.EXPIRED
        )
        
        return {
            "total_approvals": total_approvals,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "expired": expired,
        }
