"""
Base Cloud Provider Interface.

Defines common interface that all cloud providers must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseCloudProvider(ABC):
    """
    Base class for cloud provider implementations.
    
    All cloud providers (AWS, Azure, GCP) must implement this interface.
    """
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get cloud provider name."""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate cloud provider credentials.
        
        Returns:
            True if credentials are valid
        """
        pass
    
    @abstractmethod
    def get_module_path(self, service: str) -> str:
        """
        Get Terraform module path for service.
        
        Args:
            service: Service name (e.g., 'ec2', 'vm', 'compute-engine')
            
        Returns:
            Module path relative to terraform/modules
        """
        pass
    
    @abstractmethod
    def get_terraform_provider_config(self) -> dict[str, Any]:
        """
        Get Terraform provider configuration.
        
        Returns:
            Provider configuration dict for main.tf
        """
        pass
    
    @abstractmethod
    def get_state_backend_config(
        self,
        request_id: str,
        environment: str,
    ) -> dict[str, Any]:
        """
        Get Terraform state backend configuration.
        
        Args:
            request_id: Deployment request ID
            environment: Environment name
            
        Returns:
            Backend configuration dict
        """
        pass
    
    @abstractmethod
    def validate_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """
        Validate deployed resource exists and is healthy.
        
        Args:
            resource_type: Type of resource (e.g., 'instance', 'vm')
            resource_id: Resource identifier
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def get_resource_inventory(
        self,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Get resource inventory from cloud provider.
        
        Args:
            filters: Optional filters (tags, resource type, etc.)
            
        Returns:
            List of resources
        """
        pass
    
    @abstractmethod
    def get_security_findings(
        self,
        resource_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get security findings for resources.
        
        Args:
            resource_id: Optional specific resource
            
        Returns:
            List of security findings
        """
        pass
    
    @abstractmethod
    def estimate_cost(
        self,
        resources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Estimate monthly cost for resources.
        
        Args:
            resources: List of resources with configuration
            
        Returns:
            Cost estimate with breakdown
        """
        pass
    
    @abstractmethod
    def get_approved_regions(self) -> list[str]:
        """
        Get list of approved regions for this provider.
        
        Returns:
            List of region identifiers
        """
        pass
    
    @abstractmethod
    def validate_region(self, region: str) -> bool:
        """
        Validate if region is approved.
        
        Args:
            region: Region identifier
            
        Returns:
            True if approved
        """
        pass
    
    @abstractmethod
    def map_generic_service(self, service_category: str) -> str:
        """
        Map generic service category to provider-specific service.
        
        Args:
            service_category: Generic category (compute, storage, etc.)
            
        Returns:
            Provider-specific service name
        """
        pass
    
    @abstractmethod
    def get_authentication_config(self) -> dict[str, Any]:
        """
        Get authentication configuration for CI/CD.
        
        Returns:
            Authentication configuration
        """
        pass
