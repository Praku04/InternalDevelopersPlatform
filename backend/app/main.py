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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(modules.router)
app.include_router(requests.router)
app.include_router(terraform.router)
app.include_router(deployments.router)
app.include_router(approvals.router)
app.include_router(ai.router)
app.include_router(inventory.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "ai-cloud-self-service-backend",
        "environment": settings.environment,
        "docs": "/docs",
    }
