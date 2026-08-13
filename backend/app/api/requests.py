"""Deployment request endpoints: POST/GET /api/v1/requests, GET /api/v1/requests/{id}."""
from fastapi import APIRouter, HTTPException

from app.deployments.status_tracker import RequestStatus, get_status_tracker
from app.models.deployment import DeploymentSpecification
from app.repositories.request_repository import get_request_repository

router = APIRouter(prefix="/api/v1/requests", tags=["requests"])


@router.post("", response_model=DeploymentSpecification, status_code=201)
def create_request(spec: DeploymentSpecification) -> DeploymentSpecification:
    repo = get_request_repository()
    try:
        created = repo.create(spec)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    get_status_tracker().set(spec.request_id, RequestStatus.SUBMITTED)
    return created


@router.get("/{request_id}/status")
def get_request_status(request_id: str) -> dict[str, str]:
    if get_request_repository().get(request_id) is None:
        raise HTTPException(status_code=404, detail=f"request '{request_id}' not found")
    status = get_status_tracker().get(request_id)
    return {"request_id": request_id, "status": status.value if status else "UNKNOWN"}


@router.get("", response_model=list[DeploymentSpecification])
def list_requests() -> list[DeploymentSpecification]:
    return get_request_repository().list()


@router.get("/{request_id}", response_model=DeploymentSpecification)
def get_request(request_id: str) -> DeploymentSpecification:
    spec = get_request_repository().get(request_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"request '{request_id}' not found")
    return spec
