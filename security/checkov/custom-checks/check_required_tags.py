"""
Custom Checkov check: Ensure required tags are present on resources.

All infrastructure resources must have:
- Application
- Environment
- Owner
- ManagedBy
"""
from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class RequiredTags(BaseResourceCheck):
    """Check that resources have required tags."""
    
    def __init__(self):
        name = "Ensure resource has required tags"
        id = "CKV_AWS_CUSTOM_001"
        supported_resources = [
            "aws_instance",
            "aws_vpc",
            "aws_subnet",
            "aws_security_group",
            "aws_lb",
            "aws_s3_bucket",
            "aws_db_instance",
            "aws_eks_cluster",
            "aws_lambda_function",
        ]
        categories = [CheckCategories.CONVENTION]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)
    
    def scan_resource_conf(self, conf):
        """
        Check if resource has required tags.
        
        Args:
            conf: Resource configuration
            
        Returns:
            CheckResult
        """
        required_tags = ["Application", "Environment", "Owner", "ManagedBy"]
        
        # Get tags from configuration
        tags = conf.get("tags")
        if not tags:
            return CheckResult.FAILED
        
        # Handle both list and dict format
        if isinstance(tags, list) and len(tags) > 0:
            tags = tags[0]
        
        if not isinstance(tags, dict):
            return CheckResult.FAILED
        
        # Check for required tags
        missing_tags = []
        for tag in required_tags:
            if tag not in tags:
                missing_tags.append(tag)
        
        if missing_tags:
            self.details = f"Missing required tags: {', '.join(missing_tags)}"
            return CheckResult.FAILED
        
        return CheckResult.PASSED


check = RequiredTags()
