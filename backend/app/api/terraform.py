"""Terraform plan endpoints: POST /api/v1/terraform/plan, GET /api/v1/terraform/plan/{request_id}."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.terraform import TerraformPlanResult
from app.services.terraform_service import RequestNotFoundError, run_terraform_plan

router = APIRouter(prefix="/api/v1/terraform", tags=["terraform"])

# In-memory cache of the most recent plan result per request (Phase 1 only).
_last_plan: dict[str, TerraformPlanResult] = {}


class TerraformPlanRequest(BaseModel):
    request_id: str


@router.post("/plan", response_model=TerraformPlanResult)
def create_plan(payload: TerraformPlanRequest) -> TerraformPlanResult:
    try:
        result = run_terraform_plan(payload.request_id)
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"request '{exc}' not found") from exc
    _last_plan[payload.request_id] = result
    return result


@router.get("/plan/{request_id}", response_model=TerraformPlanResult)
def get_plan(request_id: str) -> TerraformPlanResult:
    result = _last_plan.get(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"no plan found for request '{request_id}'")
    return result
