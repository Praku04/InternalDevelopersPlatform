"""
AI-Powered Module Discovery Service.

Uses Bedrock to intelligently match user requirements to existing Terraform modules.
"""
import json
import logging
from typing import Any, Optional

from app.models.deployment import AIDeploymentRecommendation
from app.repositories.module_registry import ModuleRegistryRepository
from .bedrock_client import BedrockClient

logger = logging.getLogger(__name__)


class ModuleDiscoveryService:
    """
    AI-powered module discovery service.
    
    Uses Bedrock to:
    1. Analyze user infrastructure requirements
    2. Search module registry for matching capabilities
    3. Determine if existing modules can be reused
    4. Identify gaps that require new module generation
    5. Assess security and compliance requirements
    """
    
    def __init__(self):
        """Initialize module discovery service."""
        self.bedrock = BedrockClient()
        self.module_registry = ModuleRegistryRepository()
    
    def analyze_request(
        self,
        user_request: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AIDeploymentRecommendation:
        """
        Analyze natural language request and recommend deployment.
        
        Args:
            user_request: Natural language infrastructure request
            context: Additional context (user, application, etc.)
            
        Returns:
            AI deployment recommendation
        """
        logger.info(f"Analyzing request: {user_request[:100]}...")
        
        # Get all available modules
        modules = self.module_registry.list_modules()
        
        # Build system prompt
        system_prompt = self._build_system_prompt(modules)
        
        # Build tool definitions
        tools = self._build_tools()
        
        # Build user prompt with context
        full_prompt = self._build_user_prompt(user_request, context)
        
        try:
            # Invoke Bedrock with tools
            response = self.bedrock.invoke_with_tools(
                prompt=full_prompt,
                tools=tools,
                system_prompt=system_prompt,
            )
            
            # Process tool calls if any
            if response['tool_calls']:
                return self._process_tool_calls(
                    user_request,
                    response['tool_calls'],
                    context,
                )
            
            # Extract JSON recommendation
            json_response = self.bedrock.extract_json_response(response['response'])
            
            # Validate and return
            recommendation = self._validate_recommendation(json_response)
            
            logger.info(
                f"Recommendation generated: "
                f"{len(recommendation.modules_found)} modules found, "
                f"{len(recommendation.modules_missing)} missing"
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to analyze request: {e}")
            # Return fallback recommendation
            return self._fallback_recommendation(user_request, context)
    
    def _build_system_prompt(self, modules: list[dict]) -> str:
        """Build system prompt with module registry information."""
        module_list = "\n".join([
            f"- {m['name']} v{m['version']}: {m.get('description', 'No description')}\n"
            f"  Capabilities: {', '.join(m.get('capabilities', []))}\n"
            f"  Status: {m.get('status', 'unknown')}"
            for m in modules
        ])
        
        return f"""You are an expert cloud infrastructure architect for an enterprise AWS self-service platform.

Your responsibilities:
1. Analyze user infrastructure requirements
2. Match requirements to existing approved Terraform modules
3. Prefer module reuse over new generation
4. Identify security and compliance requirements
5. Assess deployment risk
6. Provide clear, actionable recommendations

CRITICAL RULES:
- NEVER recommend generating a new module if an approved module exists
- NEVER bypass security requirements
- NEVER recommend direct Terraform execution
- ALWAYS validate against security policies
- ALWAYS assess risk level (LOW, MEDIUM, HIGH, CRITICAL)

Available Approved Modules:
{module_list}

Security Requirements:
- SSH/RDP must not be open to 0.0.0.0/0
- All storage must be encrypted
- RDS must not be publicly accessible
- EC2 must use IMDSv2
- All resources must have required tags: Application, Environment, Owner, ManagedBy
- Only approved regions: ap-south-1, ap-southeast-1

Response Format:
Provide a JSON object with:
- application_name: string
- environment: "dev" | "uat" | "prod"
- resources: array of resource specifications
- modules_found: array of matching modules
- modules_missing: array of missing capabilities
- security_requirements: array of requirements
- security_warnings: array of potential issues
- deployment_risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
- risk_factors: array of risk factors
- estimated_monthly_cost: number (USD)
- recommendations: array of recommendations
- confidence_score: number (0-1)
"""
    
    def _build_tools(self) -> list[dict]:
        """Build tool definitions for Bedrock."""
        return [
            {
                "name": "search_modules",
                "description": "Search for Terraform modules by capability",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "capabilities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required capabilities (e.g., 'encrypted-ebs', 'private-subnet')"
                        },
                        "resource_type": {
                            "type": "string",
                            "description": "Resource type (e.g., 'ec2', 'vpc', 's3')"
                        }
                    },
                    "required": ["capabilities"]
                }
            },
            {
                "name": "get_module_details",
                "description": "Get detailed information about a specific module",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "module_name": {
                            "type": "string",
                            "description": "Module name"
                        }
                    },
                    "required": ["module_name"]
                }
            },
            {
                "name": "validate_security_policy",
                "description": "Validate request against security policies",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {
                            "type": "string",
                            "description": "Resource type to validate"
                        },
                        "configuration": {
                            "type": "object",
                            "description": "Resource configuration"
                        }
                    },
                    "required": ["resource_type", "configuration"]
                }
            }
        ]
    
    def _build_user_prompt(
        self,
        request: str,
        context: Optional[dict[str, Any]],
    ) -> str:
        """Build user prompt with context."""
        prompt = f"User Request: {request}\n\n"
        
        if context:
            if context.get('application'):
                prompt += f"Application: {context['application']}\n"
            if context.get('environment'):
                prompt += f"Environment: {context['environment']}\n"
            if context.get('user'):
                prompt += f"Requested by: {context['user']}\n"
        
        prompt += "\nAnalyze this request and provide a deployment recommendation."
        
        return prompt
    
    def _process_tool_calls(
        self,
        request: str,
        tool_calls: list[dict],
        context: Optional[dict[str, Any]],
    ) -> AIDeploymentRecommendation:
        """Process tool calls and generate recommendation."""
        tool_results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_input = tool_call['input']
            
            if tool_name == 'search_modules':
                result = self._search_modules_tool(tool_input)
                tool_results.append(result)
            
            elif tool_name == 'get_module_details':
                result = self._get_module_details_tool(tool_input)
                tool_results.append(result)
            
            elif tool_name == 'validate_security_policy':
                result = self._validate_security_tool(tool_input)
                tool_results.append(result)
        
        # For now, return a basic recommendation
        # In production, would make follow-up Bedrock call with tool results
        return self._fallback_recommendation(request, context, tool_results)
    
    def _search_modules_tool(self, input: dict) -> dict:
        """Execute search_modules tool."""
        capabilities = input.get('capabilities', [])
        resource_type = input.get('resource_type')
        
        results = self.module_registry.search_by_capabilities(capabilities)
        
        if resource_type:
            results = [r for r in results if r['name'] == resource_type]
        
        return {
            "tool": "search_modules",
            "results": results,
            "count": len(results)
        }
    
    def _get_module_details_tool(self, input: dict) -> dict:
        """Execute get_module_details tool."""
        module_name = input.get('module_name')
        module = self.module_registry.get_module(module_name)
        
        if not module:
            return {
                "tool": "get_module_details",
                "error": f"Module {module_name} not found"
            }
        
        return {
            "tool": "get_module_details",
            "module": module
        }
    
    def _validate_security_tool(self, input: dict) -> dict:
        """Execute validate_security_policy tool."""
        resource_type = input.get('resource_type')
        configuration = input.get('configuration', {})
        
        # Basic validation rules
        warnings = []
        
        if resource_type == 'security_group':
            for rule in configuration.get('ingress_rules', []):
                if rule.get('cidr_blocks') == ['0.0.0.0/0']:
                    if rule.get('from_port') == 22:
                        warnings.append("SSH open to internet")
                    elif rule.get('from_port') == 3389:
                        warnings.append("RDP open to internet")
        
        elif resource_type == 's3':
            if not configuration.get('encryption'):
                warnings.append("S3 encryption not enabled")
        
        elif resource_type == 'rds':
            if configuration.get('publicly_accessible'):
                warnings.append("RDS publicly accessible")
            if not configuration.get('storage_encrypted'):
                warnings.append("RDS storage not encrypted")
        
        return {
            "tool": "validate_security_policy",
            "valid": len(warnings) == 0,
            "warnings": warnings
        }
    
    def _validate_recommendation(
        self,
        json_response: dict,
    ) -> AIDeploymentRecommendation:
        """Validate and parse recommendation."""
        # This would use Pydantic validation in production
        return AIDeploymentRecommendation(**json_response)
    
    def _fallback_recommendation(
        self,
        request: str,
        context: Optional[dict[str, Any]],
        tool_results: Optional[list[dict]] = None,
    ) -> AIDeploymentRecommendation:
        """Generate fallback recommendation when AI fails."""
        logger.warning("Using fallback recommendation")
        
        return AIDeploymentRecommendation(
            request_summary=request[:200],
            environment=context.get('environment', 'dev') if context else 'dev',
            region='ap-south-1',
            resources=[],
            missing_modules=[],
            security_requirements=[],
            approval_required=True,
        )
