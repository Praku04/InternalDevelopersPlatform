"""AI services powered by Amazon Bedrock."""

from .bedrock_client import BedrockClient
from .module_discovery import ModuleDiscoveryService

__all__ = ["BedrockClient", "ModuleDiscoveryService"]
