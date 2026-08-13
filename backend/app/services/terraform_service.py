"""
Terraform Service.

High-level service for managing Terraform workspaces and deployments.
Coordinates between Terraform generator, engine, and Azure DevOps.
"""
import logging
import os
import shutil
from pathlib import Path

from app.config import get_settings
from app.models.deployment import DeploymentSpecification
from app.models.terraform import TerraformPlanResult
from app.repositories.request_repository import RequestRepository
from app.terraform.generator import TerraformGenerator
from app.terraform.engine import TerraformEngine

logger = logging.getLogger(__name__)
settings = get_settings()


class RequestNotFoundError(Exception):
    """Raised when a deployment request is not found."""
    pass


class TerraformService:
    """
    Service for managing Terraform deployment lifecycle.
    
    Responsibilities:
    - Create isolated workspace for each deployment
    - Generate Terraform configuration
    - Prepare workspace for Azure DevOps pipeline
    - Clean up workspaces
    """
    
    def __init__(self):
        """Initialize Terraform service."""
        self.generator = TerraformGenerator()
        self.base_workspace_path = Path("terraform/generated")
        self.base_workspace_path.mkdir(parents=True, exist_ok=True)
    
    def prepare_workspace(self, request: DeploymentSpecification) -> str:
        """
        Prepare Terraform workspace for deployment.
        
        Creates isolated directory with generated Terraform configuration
        ready for Azure DevOps pipeline to execute.
        
        Args:
            request: Deployment specification
            
        Returns:
            Path to workspace directory
        """
        workspace_path = self.base_workspace_path / request.request_id
        
        logger.info(f"Preparing workspace for request {request.request_id}")
        
        # Clean up existing workspace if it exists
        if workspace_path.exists():
            logger.warning(f"Workspace already exists, cleaning up: {workspace_path}")
            shutil.rmtree(workspace_path)
        
        # Create workspace directory
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Generate Terraform configuration
        try:
            config = self.generator.generate(request)
            
            # Write main configuration
            main_tf = workspace_path / "main.tf"
            main_tf.write_text(config.main_tf)
            
            # Write variables
            variables_tf = workspace_path / "variables.tf"
            variables_tf.write_text(config.variables_tf)
            
            # Write outputs
            outputs_tf = workspace_path / "outputs.tf"
            outputs_tf.write_text(config.outputs_tf)
            
            # Write versions
            versions_tf = workspace_path / "versions.tf"
            versions_tf.write_text(config.versions_tf)
            
            # Write terraform.tfvars
            tfvars = workspace_path / "terraform.tfvars"
            tfvars.write_text(self._generate_tfvars(request))
            
            logger.info(f"Terraform configuration generated in {workspace_path}")
            
            return str(workspace_path)
            
        except Exception as e:
            logger.error(f"Failed to prepare workspace: {e}")
            # Clean up on failure
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
            raise
    
    def _generate_tfvars(self, request: DeploymentSpecification) -> str:
        """
        Generate terraform.tfvars file.
        
        Args:
            request: Deployment specification
            
        Returns:
            tfvars content
        """
        lines = [
            f"# Generated for request {request.request_id}",
            f"# Application: {request.application}",
            f"# Environment: {request.environment}",
            "",
            f'application_name = "{request.application}"',
            f'environment = "{request.environment}"',
            f'aws_region = "{request.region}"',
            "",
        ]
        
        # Add resource-specific variables
        for resource in request.resources:
            config = resource.configuration
            if resource.type.value == "ec2":
                lines.extend([
                    f'instance_type = "{config.get("instance_type", "t3.micro")}"',
                    f'instance_count = {config.get("instance_count", 1)}',
                ])
            elif resource.type.value == "s3":
                lines.extend([
                    f'bucket_encryption = {str(config.get("encryption_enabled", True)).lower()}',
                    f'versioning = {str(config.get("versioning_enabled", False)).lower()}',
                ])
        
        return "\n".join(lines)
    
    def validate_workspace(self, workspace_path: str) -> bool:
        """
        Validate Terraform configuration in workspace.
        
        Args:
            workspace_path: Path to workspace
            
        Returns:
            True if validation passes
        """
        logger.info(f"Validating workspace: {workspace_path}")
        
        engine = TerraformEngine(working_dir=workspace_path)
        
        try:
            # Format check
            engine.fmt(check=True)
            
            # Initialize
            engine.init()
            
            # Validate
            result = engine.validate()
            
            if result.get("valid"):
                logger.info("Workspace validation passed")
                return True
            else:
                logger.error(f"Workspace validation failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Workspace validation error: {e}")
            return False
    
    def cleanup_workspace(self, request_id: str):
        """
        Clean up workspace directory.
        
        Args:
            request_id: Deployment request ID
        """
        workspace_path = self.base_workspace_path / request_id
        
        if workspace_path.exists():
            logger.info(f"Cleaning up workspace: {workspace_path}")
            shutil.rmtree(workspace_path)
        else:
            logger.warning(f"Workspace not found: {workspace_path}")
    
    def get_workspace_path(self, request_id: str) -> Path:
        """
        Get workspace path for request.
        
        Args:
            request_id: Deployment request ID
            
        Returns:
            Path to workspace
        """
        return self.base_workspace_path / request_id



def run_terraform_plan(request_id: str) -> TerraformPlanResult:
    """
    Run terraform plan for a deployment request.
    
    Args:
        request_id: Deployment request ID
        
    Returns:
        TerraformPlanResult with plan output
        
    Raises:
        RequestNotFoundError: If request not found
    """
    # Get request from repository
    repo = RequestRepository()
    request = repo.get(request_id)
    
    if request is None:
        raise RequestNotFoundError(request_id)
    
    # Initialize service and prepare workspace
    service = TerraformService()
    workspace_path = service.prepare_workspace(request)
    
    # Run terraform plan
    engine = TerraformEngine(working_dir=workspace_path)
    
    try:
        # Initialize terraform
        engine.init()
        
        # Run plan
        plan_output = engine.plan()
        
        # Parse plan output (simplified for Phase 1)
        return TerraformPlanResult(
            request_id=request_id,
            plan_output=plan_output.get("stdout", ""),
            plan_json=plan_output,
            changes_summary={
                "add": 0,  # Would parse from plan output
                "change": 0,
                "destroy": 0,
            },
            estimated_cost=0.0,  # Would calculate from resources
        )
        
    except Exception as e:
        logger.error(f"Terraform plan failed: {e}")
        return TerraformPlanResult(
            request_id=request_id,
            plan_output=f"Error: {str(e)}",
            plan_json={},
            changes_summary={"add": 0, "change": 0, "destroy": 0},
            estimated_cost=0.0,
        )
