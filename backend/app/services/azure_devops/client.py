"""
Azure DevOps API client.

Provides low-level API access to Azure DevOps REST APIs for pipelines,
repositories, and build management.
"""
import logging
from typing import Any, Optional
from urllib.parse import quote

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AzureDevOpsClient:
    """
    Azure DevOps REST API client.
    
    Authentication uses Personal Access Token (PAT) stored in AWS Secrets Manager
    or environment variable for development.
    """
    
    def __init__(
        self,
        organization: str | None = None,
        project: str | None = None,
        pat: str | None = None,
    ):
        """
        Initialize Azure DevOps client.
        
        Args:
            organization: Azure DevOps organization name
            project: Project name
            pat: Personal Access Token (if None, will attempt to load from secrets)
        """
        self.organization = organization or self._get_organization()
        self.project = project or self._get_project()
        self.pat = pat or self._get_pat()
        
        self.base_url = f"https://dev.azure.com/{self.organization}/{quote(self.project)}"
        self.api_version = "7.1"
        
        self.client = httpx.Client(
            auth=("", self.pat),  # PAT uses empty username
            timeout=30.0,
        )
    
    def _get_organization(self) -> str:
        """Get Azure DevOps organization from config."""
        org = getattr(settings, "azdo_organization", None)
        if not org:
            raise ValueError("Azure DevOps organization not configured")
        return org
    
    def _get_project(self) -> str:
        """Get Azure DevOps project from config."""
        project = getattr(settings, "azdo_project", None)
        if not project:
            raise ValueError("Azure DevOps project not configured")
        return project
    
    def _get_pat(self) -> str:
        """
        Get Personal Access Token.
        
        In production, this should retrieve from AWS Secrets Manager.
        For development, uses environment variable.
        """
        pat = getattr(settings, "azdo_pat", None)
        if not pat:
            if settings.demo_mode:
                logger.warning("Running in demo mode without Azure DevOps PAT")
                return "demo-token"
            raise ValueError("Azure DevOps PAT not configured")
        return pat
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request to Azure DevOps API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters
            json: Request body
            
        Returns:
            Response JSON
            
        Raises:
            httpx.HTTPError: On request failure
        """
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        params["api-version"] = self.api_version
        
        logger.debug(f"Azure DevOps API: {method} {url}")
        
        response = self.client.request(
            method=method,
            url=url,
            params=params,
            json=json,
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_pipeline(self, pipeline_id: int) -> dict[str, Any]:
        """Get pipeline definition."""
        return self._make_request("GET", f"/_apis/pipelines/{pipeline_id}")
    
    def run_pipeline(
        self,
        pipeline_id: int,
        parameters: dict[str, Any],
        branch: str = "main",
    ) -> dict[str, Any]:
        """
        Trigger a pipeline run.
        
        Args:
            pipeline_id: Pipeline ID
            parameters: Pipeline parameters
            branch: Branch to run from
            
        Returns:
            Pipeline run details
        """
        payload = {
            "resources": {
                "repositories": {
                    "self": {
                        "refName": f"refs/heads/{branch}",
                    }
                }
            },
            "templateParameters": parameters,
        }
        
        return self._make_request(
            "POST",
            f"/_apis/pipelines/{pipeline_id}/runs",
            json=payload,
        )
    
    def get_pipeline_run(self, pipeline_id: int, run_id: int) -> dict[str, Any]:
        """Get pipeline run details."""
        return self._make_request(
            "GET",
            f"/_apis/pipelines/{pipeline_id}/runs/{run_id}",
        )
    
    def get_build(self, build_id: int) -> dict[str, Any]:
        """Get build details."""
        return self._make_request("GET", f"/_apis/build/builds/{build_id}")
    
    def get_build_logs(self, build_id: int) -> list[dict[str, Any]]:
        """Get build logs."""
        return self._make_request("GET", f"/_apis/build/builds/{build_id}/logs")
    
    def get_build_timeline(self, build_id: int) -> dict[str, Any]:
        """Get build timeline (stages, jobs, tasks)."""
        return self._make_request("GET", f"/_apis/build/builds/{build_id}/timeline")
    
    def create_pull_request(
        self,
        repository_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        reviewers: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            repository_id: Repository ID
            source_branch: Source branch name
            target_branch: Target branch name
            title: PR title
            description: PR description
            reviewers: List of reviewer IDs
            
        Returns:
            Pull request details
        """
        payload = {
            "sourceRefName": f"refs/heads/{source_branch}",
            "targetRefName": f"refs/heads/{target_branch}",
            "title": title,
            "description": description,
        }
        
        if reviewers:
            payload["reviewers"] = [{"id": reviewer_id} for reviewer_id in reviewers]
        
        return self._make_request(
            "POST",
            f"/_apis/git/repositories/{repository_id}/pullrequests",
            json=payload,
        )
    
    def get_pull_request(self, repository_id: str, pr_id: int) -> dict[str, Any]:
        """Get pull request details."""
        return self._make_request(
            "GET",
            f"/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}",
        )
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, *args):
        """Context manager exit."""
        self.close()
