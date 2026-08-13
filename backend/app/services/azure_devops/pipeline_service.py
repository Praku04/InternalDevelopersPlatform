"""
Azure DevOps Pipeline Service.

High-level service for triggering and monitoring Terraform deployment pipelines.
"""
import logging
from typing import Any, Optional

from app.config import get_settings
from app.models.deployment import DeploymentRequest, DeploymentStatus
from .client import AzureDevOpsClient

logger = logging.getLogger(__name__)
settings = get_settings()


class PipelineService:
    """
    Service for managing Azure DevOps pipelines for Terraform deployments.
    
    This service orchestrates the deployment workflow:
    1. Trigger pipeline with deployment request parameters
    2. Monitor pipeline execution
    3. Retrieve results and logs
    4. Update deployment status
    """
    
    def __init__(self, client: Optional[AzureDevOpsClient] = None):
        """
        Initialize pipeline service.
        
        Args:
            client: Azure DevOps client (optional, will create if not provided)
        """
        self.client = client or AzureDevOpsClient()
        self.pipeline_id = self._get_pipeline_id()
    
    def _get_pipeline_id(self) -> int:
        """Get deployment pipeline ID from configuration."""
        pipeline_id = getattr(settings, "azdo_pipeline_id", None)
        if not pipeline_id:
            if settings.demo_mode:
                logger.warning("Running in demo mode without Azure DevOps pipeline ID")
                return 0
            raise ValueError("Azure DevOps pipeline ID not configured")
        return int(pipeline_id)
    
    def trigger_deployment(
        self,
        request: DeploymentRequest,
    ) -> dict[str, Any]:
        """
        Trigger Terraform deployment pipeline.
        
        Args:
            request: Deployment request containing infrastructure specification
            
        Returns:
            Pipeline run details including run ID and status
            
        Raises:
            Exception: If pipeline trigger fails
        """
        if settings.demo_mode:
            logger.warning(f"Demo mode: Simulating pipeline trigger for request {request.request_id}")
            return {
                "id": 12345,
                "name": f"Deployment-{request.request_id}",
                "state": "inProgress",
                "result": None,
                "url": f"https://dev.azure.com/demo/project/_build/results?buildId=12345",
                "_demo": True,
            }
        
        logger.info(f"Triggering deployment pipeline for request {request.request_id}")
        
        # Prepare pipeline parameters
        parameters = {
            "requestId": request.request_id,
            "environment": request.environment,
            "workspacePath": f"terraform/generated",
        }
        
        try:
            # Trigger pipeline
            run = self.client.run_pipeline(
                pipeline_id=self.pipeline_id,
                parameters=parameters,
                branch="main",
            )
            
            logger.info(
                f"Pipeline triggered successfully. "
                f"Run ID: {run.get('id')}, State: {run.get('state')}"
            )
            
            return run
            
        except Exception as e:
            logger.error(f"Failed to trigger pipeline: {e}")
            raise
    
    def get_pipeline_status(self, run_id: int) -> dict[str, Any]:
        """
        Get current status of a pipeline run.
        
        Args:
            run_id: Pipeline run ID
            
        Returns:
            Pipeline run status and details
        """
        if settings.demo_mode:
            logger.warning(f"Demo mode: Simulating pipeline status for run {run_id}")
            return {
                "id": run_id,
                "state": "completed",
                "result": "succeeded",
                "_demo": True,
            }
        
        try:
            run = self.client.get_pipeline_run(
                pipeline_id=self.pipeline_id,
                run_id=run_id,
            )
            return run
            
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            raise
    
    def get_deployment_logs(self, run_id: int) -> list[dict[str, Any]]:
        """
        Retrieve logs from deployment pipeline run.
        
        Args:
            run_id: Pipeline run ID
            
        Returns:
            List of log entries from pipeline execution
        """
        if settings.demo_mode:
            logger.warning(f"Demo mode: Simulating logs for run {run_id}")
            return [
                {"id": 1, "type": "stage", "name": "Validate", "status": "succeeded"},
                {"id": 2, "type": "stage", "name": "SecurityScan", "status": "succeeded"},
                {"id": 3, "type": "stage", "name": "Plan", "status": "succeeded"},
                {"id": 4, "type": "stage", "name": "Apply", "status": "succeeded"},
            ]
        
        try:
            # Get build ID from pipeline run
            run = self.client.get_pipeline_run(self.pipeline_id, run_id)
            
            # Pipeline run contains build resources
            build_id = None
            if "resources" in run and "builds" in run["resources"]:
                builds = run["resources"]["builds"].get("self", {})
                build_id = builds.get("id")
            
            if not build_id:
                logger.warning(f"No build ID found for pipeline run {run_id}")
                return []
            
            # Get logs
            logs = self.client.get_build_logs(build_id)
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get deployment logs: {e}")
            raise
    
    def get_pipeline_timeline(self, run_id: int) -> dict[str, Any]:
        """
        Get detailed timeline of pipeline execution.
        
        Args:
            run_id: Pipeline run ID
            
        Returns:
            Timeline with stages, jobs, and tasks
        """
        if settings.demo_mode:
            logger.warning(f"Demo mode: Simulating timeline for run {run_id}")
            return {
                "records": [
                    {
                        "id": "1",
                        "type": "Stage",
                        "name": "Validate",
                        "state": "completed",
                        "result": "succeeded",
                    },
                    {
                        "id": "2",
                        "type": "Stage",
                        "name": "SecurityScan",
                        "state": "completed",
                        "result": "succeeded",
                    },
                    {
                        "id": "3",
                        "type": "Stage",
                        "name": "Plan",
                        "state": "completed",
                        "result": "succeeded",
                    },
                    {
                        "id": "4",
                        "type": "Stage",
                        "name": "Apply",
                        "state": "completed",
                        "result": "succeeded",
                    },
                ]
            }
        
        try:
            run = self.client.get_pipeline_run(self.pipeline_id, run_id)
            
            build_id = None
            if "resources" in run and "builds" in run["resources"]:
                builds = run["resources"]["builds"].get("self", {})
                build_id = builds.get("id")
            
            if not build_id:
                return {}
            
            timeline = self.client.get_build_timeline(build_id)
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get pipeline timeline: {e}")
            raise
    
    def map_pipeline_state_to_deployment_status(self, state: str, result: Optional[str] = None) -> DeploymentStatus:
        """
        Map Azure DevOps pipeline state to deployment status.
        
        Args:
            state: Pipeline state (inProgress, completed, etc.)
            result: Pipeline result (succeeded, failed, canceled, etc.)
            
        Returns:
            Corresponding deployment status
        """
        if state == "inProgress" or state == "notStarted":
            return DeploymentStatus.DEPLOYING
        
        if state == "completed":
            if result == "succeeded":
                return DeploymentStatus.COMPLETED
            elif result == "failed":
                return DeploymentStatus.FAILED
            elif result == "canceled":
                return DeploymentStatus.FAILED
            else:
                return DeploymentStatus.FAILED
        
        return DeploymentStatus.PENDING
    
    def create_module_pr(
        self,
        module_name: str,
        source_branch: str,
        description: str,
    ) -> dict[str, Any]:
        """
        Create pull request for AI-generated module.
        
        Args:
            module_name: Name of the generated module
            source_branch: Branch containing generated code
            description: PR description
            
        Returns:
            Pull request details
        """
        if settings.demo_mode:
            logger.warning(f"Demo mode: Simulating PR creation for module {module_name}")
            return {
                "pullRequestId": 123,
                "title": f"Add generated module: {module_name}",
                "status": "active",
                "url": "https://dev.azure.com/demo/project/_git/repo/pullrequest/123",
                "_demo": True,
            }
        
        repository_id = getattr(settings, "azdo_repository_id", None)
        if not repository_id:
            raise ValueError("Azure DevOps repository ID not configured")
        
        title = f"Add generated Terraform module: {module_name}"
        
        try:
            pr = self.client.create_pull_request(
                repository_id=repository_id,
                source_branch=source_branch,
                target_branch="main",
                title=title,
                description=description,
            )
            
            logger.info(f"Pull request created: {pr.get('pullRequestId')}")
            return pr
            
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            raise
