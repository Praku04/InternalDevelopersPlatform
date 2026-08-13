"""
FastAPI application entrypoint.

Phase 1 scope: health check, module registry endpoints, and deployment
request endpoints backed by an in-memory store. Authentication/authorization,
Bedrock integration, Terraform execution, and deployment orchestration are
deliberately out of scope for this phase (see docs/architecture/overview.md).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, modules, requests, terraform, deployments, approvals, ai, inventory
from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)

app = FastAPI(
    title="AI-Powered AWS Self-Service Infrastructure Platform",
    version="0.1.0",
    description="Backend API for the self-service infrastructure portal (Phase 1).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(modules.router, prefix="/api/v1/modules", tags=["modules"])
app.include_router(requests.router, prefix="/api/v1/requests", tags=["requests"])
app.include_router(terraform.router, prefix="/api/v1/terraform", tags=["terraform"])
app.include_router(deployments.router, prefix="/api/v1/deployments", tags=["deployments"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "ai-cloud-self-service-backend",
        "environment": settings.environment,
        "docs": "/docs",
    }
