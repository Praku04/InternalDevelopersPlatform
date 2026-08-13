from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/v1/health")
def health() -> dict[str, str]:
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status information
    """
    from app.config import get_settings
    settings = get_settings()
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
    }
