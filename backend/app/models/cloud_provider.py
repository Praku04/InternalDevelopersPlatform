"""
Cloud Provider models and enumerations.

Defines cloud provider types, regions, and service mappings.
"""
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class CloudService(str, Enum):
    """Cloud service categories (provider-agnostic)."""
    COMPUTE = "compute"
    NETWORKING = "networking"
    STORAGE = "storage"
    DATABASE = "database"
    CONTAINER = "container"
    SERVERLESS = "serverless"
    LOAD_BALANCER = "load_balancer"
    MONITORING = "monitoring"


class AWSRegion(str, Enum):
    """AWS regions."""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTH_1 = "ap-south-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"


class AzureRegion(str, Enum):
    """Azure regions."""
    EAST_US = "eastus"
    WEST_US = "westus"
    WEST_EUROPE = "westeurope"
    CENTRAL_INDIA = "centralindia"
    SOUTHEAST_ASIA = "southeastasia"


class GCPRegion(str, Enum):
    """GCP regions."""
    US_CENTRAL1 = "us-central1"
    US_EAST1 = "us-east1"
    EUROPE_WEST1 = "europe-west1"
    ASIA_SOUTH1 = "asia-south1"
    ASIA_SOUTHEAST1 = "asia-southeast1"


class ServiceMapping(BaseModel):
    """Maps generic service to provider-specific service."""
    service_category: CloudService
    aws_service: str | None = None
    azure_service: str | None = None
    gcp_service: str | None = None
    
    class Config:
        use_enum_values = True


# Service mappings
SERVICE_MAPPINGS: list[ServiceMapping] = [
    # Compute
    ServiceMapping(
        service_category=CloudService.COMPUTE,
        aws_service="ec2",
        azure_service="vm",
        gcp_service="compute-engine",
    ),
    # Networking
    ServiceMapping(
        service_category=CloudService.NETWORKING,
        aws_service="vpc",
        azure_service="vnet",
        gcp_service="vpc",
    ),
    # Storage
    ServiceMapping(
        service_category=CloudService.STORAGE,
        aws_service="s3",
        azure_service="blob",
        gcp_service="cloud-storage",
    ),
    # Database
    ServiceMapping(
        service_category=CloudService.DATABASE,
        aws_service="rds",
        azure_service="sql",
        gcp_service="cloud-sql",
    ),
    # Container
    ServiceMapping(
        service_category=CloudService.CONTAINER,
        aws_service="eks",
        azure_service="aks",
        gcp_service="gke",
    ),
    # Serverless
    ServiceMapping(
        service_category=CloudService.SERVERLESS,
        aws_service="lambda",
        azure_service="functions",
        gcp_service="cloud-functions",
    ),
    # Load Balancer
    ServiceMapping(
        service_category=CloudService.LOAD_BALANCER,
        aws_service="alb",
        azure_service="app-gateway",
        gcp_service="load-balancer",
    ),
]


class CloudResourceRequest(BaseModel):
    """Multi-cloud resource request."""
    cloud_provider: CloudProvider
    region: str
    service_category: CloudService
    provider_service: str | None = None  # If user specifies specific service
    configuration: dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class MultiCloudDeploymentRequest(BaseModel):
    """Multi-cloud deployment request."""
    request_id: str
    application_name: str
    environment: str
    primary_cloud: CloudProvider
    resources: list[CloudResourceRequest]
    tags: dict[str, str] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


def get_provider_service(
    cloud_provider: CloudProvider,
    service_category: CloudService,
) -> str | None:
    """
    Get provider-specific service name.
    
    Args:
        cloud_provider: Cloud provider
        service_category: Service category
        
    Returns:
        Provider-specific service name
    """
    for mapping in SERVICE_MAPPINGS:
        if mapping.service_category == service_category:
            if cloud_provider == CloudProvider.AWS:
                return mapping.aws_service
            elif cloud_provider == CloudProvider.AZURE:
                return mapping.azure_service
            elif cloud_provider == CloudProvider.GCP:
                return mapping.gcp_service
    
    return None


def get_approved_regions(cloud_provider: CloudProvider) -> list[str]:
    """
    Get approved regions for cloud provider.
    
    Args:
        cloud_provider: Cloud provider
        
    Returns:
        List of approved region identifiers
    """
    if cloud_provider == CloudProvider.AWS:
        return [
            AWSRegion.AP_SOUTH_1.value,
            AWSRegion.AP_SOUTHEAST_1.value,
            AWSRegion.US_EAST_1.value,
        ]
    elif cloud_provider == CloudProvider.AZURE:
        return [
            AzureRegion.CENTRAL_INDIA.value,
            AzureRegion.SOUTHEAST_ASIA.value,
            AzureRegion.EAST_US.value,
        ]
    elif cloud_provider == CloudProvider.GCP:
        return [
            GCPRegion.ASIA_SOUTH1.value,
            GCPRegion.ASIA_SOUTHEAST1.value,
            GCPRegion.US_CENTRAL1.value,
        ]
    
    return []


def validate_region(cloud_provider: CloudProvider, region: str) -> bool:
    """
    Validate if region is approved for provider.
    
    Args:
        cloud_provider: Cloud provider
        region: Region identifier
        
    Returns:
        True if region is approved
    """
    approved = get_approved_regions(cloud_provider)
    return region in approved
