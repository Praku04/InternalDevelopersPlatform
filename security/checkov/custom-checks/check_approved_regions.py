"""
Custom Checkov check: Ensure resources are deployed in approved AWS regions.

Only approved regions are allowed for deployment to ensure compliance
with data residency requirements.
"""
from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.terraform.checks.provider.base_check import BaseProviderCheck


class ApprovedRegions(BaseProviderCheck):
    """Check that AWS provider uses approved region."""
    
    def __init__(self):
        name = "Ensure AWS provider uses approved region"
        id = "CKV_AWS_CUSTOM_002"
        supported_provider = ["aws"]
        categories = [CheckCategories.CONVENTION]
        super().__init__(name=name, id=id, categories=categories, supported_provider=supported_provider)
    
    def scan_provider_conf(self, conf):
        """
        Check if provider region is approved.
        
        Args:
            conf: Provider configuration
            
        Returns:
            CheckResult
        """
        # Define approved regions
        approved_regions = [
            "ap-south-1",      # Mumbai (primary)
            "ap-southeast-1",  # Singapore
            "us-east-1",       # N. Virginia (for global services)
        ]
        
        # Get region from provider configuration
        region = conf.get("region")
        
        if not region:
            self.details = "No region specified in provider configuration"
            return CheckResult.FAILED
        
        # Handle both list and single value
        if isinstance(region, list) and len(region) > 0:
            region = region[0]
        
        if region not in approved_regions:
            self.details = f"Region '{region}' is not approved. Approved regions: {', '.join(approved_regions)}"
            return CheckResult.FAILED
        
        return CheckResult.PASSED


check = ApprovedRegions()
