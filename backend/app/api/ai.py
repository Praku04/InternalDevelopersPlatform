"""
AI Assistant API endpoints.

Provides endpoints for natural language infrastructure requests using Amazon Bedrock.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models.deployment import AIDeploymentRecommendation, DeploymentRequest, DeploymentSource
from app.repositories.request_repository import get_request_repository
from app.services.ai import ModuleDiscoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

# Dependencies
module_discovery = ModuleDiscoveryService()
request_repo = get_request_repository()


class AIRequest(BaseModel):
    """Natural language infrastructure request."""
    prompt: str
    application: str | None = None
    environment: str | None = None
    user_id: str = "system"


class AIResponse(BaseModel):
    """AI assistant response."""
    recommendation: dict[str, Any]
    deployment_spec: dict[str, Any] | None = None
    can_deploy: bool
    requires_review: bool
    warnings: list[str]


@router.post("/analyze", response_model=AIResponse)
def analyze_request(payload: AIRequest) -> AIResponse:
    """
    Analyze natural language infrastructure request.
    
    Uses Bedrock to:
    1. Parse user requirements
    2. Search for matching modules
    3. Assess security and risk
    4. Generate deployment recommendation
    
    Args:
        payload: User's natural language request
        
    Returns:
        AI analysis and recommendation
    """
    logger.info(f"Analyzing AI request from user {payload.user_id}")
    
    try:
        # Build context
        context = {
            "application": payload.application,
            "environment": payload.environment,
            "user": payload.user_id,
        }
        
        # Analyze with Bedrock
        recommendation = module_discovery.analyze_request(
            user_request=payload.prompt,
            context=context,
        )
        
        # Determine if deployment can proceed
        can_deploy = (
            len(recommendation.modules_missing) == 0 and
            len(recommendation.security_warnings) == 0 and
            recommendation.confidence_score >= 0.8
        )
        
        requires_review = (
            len(recommendation.modules_missing) > 0 or
            recommendation.deployment_risk in ["HIGH", "CRITICAL"] or
            recommendation.confidence_score < 0.8
        )
        
        # Convert to deployment spec if ready
        deployment_spec = None
        if can_deploy:
            deployment_spec = {
                "application_name": recommendation.request_summary.split()[0],  # Extract app name
                "environment": recommendation.environment,
                "aws_region": recommendation.region,
                "resources": [
                    {
                        "type": r.type,
                        "properties": r.configuration,
                    }
                    for r in recommendation.resources
                ],
            }
        
        return AIResponse(
            recommendation=recommendation.dict(),
            deployment_spec=deployment_spec,
            can_deploy=can_deploy,
            requires_review=requires_review,
            warnings=recommendation.security_warnings,
        )
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}",
        )


@router.post("/chat")
def chat(payload: AIRequest) -> dict[str, Any]:
    """
    Chat with AI assistant.
    
    For conversational interactions and clarifications.
    
    Args:
        payload: User message
        
    Returns:
        AI response
    """
    logger.info(f"AI chat request from user {payload.user_id}")
    
    try:
        from app.services.ai import BedrockClient
        
        bedrock = BedrockClient()
        
        # Load system prompt
        from pathlib import Path
        system_prompt_path = Path("ai/prompts/system_prompt.md")
        
        if system_prompt_path.exists():
            system_prompt = system_prompt_path.read_text()
        else:
            system_prompt = "You are a helpful cloud infrastructure assistant."
        
        # Invoke Bedrock
        response = bedrock.invoke_model(
            prompt=payload.prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
            temperature=0.7,
        )
        
        # Extract text response
        content = response.get('content', [])
        text_response = ""
        
        for item in content:
            if item.get('type') == 'text':
                text_response += item.get('text', '')
        
        return {
            "response": text_response,
            "model": response.get('model'),
            "usage": response.get('usage'),
        }
        
    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI chat failed: {str(e)}",
        )


@router.post("/create-request")
def create_request_from_ai(payload: AIRequest) -> dict[str, Any]:
    """
    Analyze request and create deployment request.
    
    End-to-end flow:
    1. Analyze with AI
    2. If approved, create deployment request
    3. Return request ID
    
    Args:
        payload: Natural language request
        
    Returns:
        Created deployment request
    """
    logger.info(f"Creating deployment request from AI for user {payload.user_id}")
    
    # Analyze first
    analysis = analyze_request(payload)
    
    if not analysis.can_deploy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create deployment: " + ", ".join(analysis.warnings or ["Requirements not clear"]),
        )
    
    if not analysis.deployment_spec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create deployment: Specification not generated",
        )
    
    # Create deployment request
    try:
        recommendation = analysis.recommendation
        
        deployment_request = DeploymentRequest(
            application_name=recommendation.get('application_name', 'unknown'),
            environment=recommendation.get('environment', 'dev'),
            aws_region=recommendation.get('region', 'ap-south-1'),
            resources=[
                {"type": r['type'], "properties": r.get('configuration', {})}
                for r in recommendation.get('resources', [])
            ],
            source=DeploymentSource.AI,
            created_by=payload.user_id,
        )
        
        # Store request
        request_repo.create(deployment_request)
        
        logger.info(f"Created deployment request: {deployment_request.request_id}")
        
        return {
            "request_id": deployment_request.request_id,
            "status": deployment_request.status.value,
            "application_name": deployment_request.application_name,
            "environment": deployment_request.environment,
            "source": "AI",
            "recommendation": recommendation,
        }
        
    except Exception as e:
        logger.error(f"Failed to create deployment request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create request: {str(e)}",
        )


@router.get("/health")
def ai_health() -> dict[str, Any]:
    """
    Check AI service health.
    
    Verifies Bedrock connectivity and module registry availability.
    
    Returns:
        Health status
    """
    from app.config import get_settings
    
    settings = get_settings()
    
    health = {
        "status": "healthy",
        "bedrock_configured": bool(settings.bedrock_model_id),
        "demo_mode": settings.demo_mode,
        "model_id": settings.bedrock_model_id,
        "region": settings.aws_region,
    }
    
    # Check module registry
    try:
        from app.repositories.module_registry import ModuleRegistryRepository
        registry = ModuleRegistryRepository()
        modules = registry.list_modules()
        health["modules_available"] = len(modules)
        health["module_registry"] = "healthy"
    except Exception as e:
        health["module_registry"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    # Try Bedrock connection if not in demo mode
    if not settings.demo_mode:
        try:
            from app.services.ai import BedrockClient
            bedrock = BedrockClient()
            # Simple test invocation
            response = bedrock.invoke_model(
                prompt="Hello",
                max_tokens=10,
            )
            health["bedrock_connection"] = "healthy"
        except Exception as e:
            health["bedrock_connection"] = f"error: {str(e)}"
            health["status"] = "degraded"
    
    return health
