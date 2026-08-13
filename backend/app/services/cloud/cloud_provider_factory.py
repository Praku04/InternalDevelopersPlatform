"""
Cloud Provider Factory.

Creates appropriate cloud provider instance based on provider type.
"""
import logging
from typing import Optional

from app.models.cloud_provider import CloudProvider
from .base_provider import BaseCloudProvider
from .aws_provider import AWSProvider
from .azure_provider import AzureProvider
from .gcp_provider import GCPProvider

logger = logging.getLogger(__name__)


class CloudProviderFactory:
    """
    Factory for creating cloud provider instances.
    
    Usage:
        provider = CloudProviderFactory.get_provider(CloudProvider.AWS)
        module_path = provider.get_module_path("ec2")
    """
    
    _providers: dict[CloudProvider, BaseCloudProvider] = {}
    
    @classmethod
    def get_provider(cls, cloud_provider: CloudProvider) -> BaseCloudProvider:
        """
        Get cloud provider instance.
        
        Args:
            cloud_provider: Cloud provider type
            
        Returns:
            Cloud provider instance
            
        Raises:
            ValueError: If provider not supported
        """
        # Return cached instance if exists
        if cloud_provider in cls._providers:
            return cls._providers[cloud_provider]
        
        # Create new instance
        if cloud_provider == CloudProvider.AWS:
            provider = AWSProvider()
        elif cloud_provider == CloudProvider.AZURE:
            provider = AzureProvider()
        elif cloud_provider == CloudProvider.GCP:
            provider = GCPProvider()
        else:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
        
        # Cache and return
        cls._providers[cloud_provider] = provider
        logger.info(f"Created {cloud_provider.value} provider instance")
        
        return provider
    
    @classmethod
    def get_all_providers(cls) -> dict[CloudProvider, BaseCloudProvider]:
        """
        Get all cloud provider instances.
        
        Returns:
            Dictionary of all providers
        """
        return {
            CloudProvider.AWS: cls.get_provider(CloudProvider.AWS),
            CloudProvider.AZURE: cls.get_provider(CloudProvider.AZURE),
            CloudProvider.GCP: cls.get_provider(CloudProvider.GCP),
        }
    
    @classmethod
    def validate_credentials_all(cls) -> dict[CloudProvider, bool]:
        """
        Validate credentials for all providers.
        
        Returns:
            Dictionary mapping provider to validation status
        """
        results = {}
        
        for cloud_provider in CloudProvider:
            try:
                provider = cls.get_provider(cloud_provider)
                results[cloud_provider] = provider.validate_credentials()
            except Exception as e:
                logger.error(f"Failed to validate {cloud_provider.value} credentials: {e}")
                results[cloud_provider] = False
        
        return results
    
    @classmethod
    def get_provider_by_name(cls, provider_name: str) -> Optional[BaseCloudProvider]:
        """
        Get provider by string name.
        
        Args:
            provider_name: Provider name ('aws', 'azure', 'gcp')
            
        Returns:
            Provider instance or None if not found
        """
        try:
            cloud_provider = CloudProvider(provider_name.lower())
            return cls.get_provider(cloud_provider)
        except ValueError:
            logger.error(f"Unknown provider name: {provider_name}")
            return None
