"""Module registry endpoints: GET /api/v1/modules, GET /api/v1/modules/{name}, POST /api/v1/modules/search."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.module import ModuleMetadata
from app.services.module_service import ModuleService

router = APIRouter(prefix="/api/v1/modules", tags=["modules"])


class ModuleSearchRequest(BaseModel):
    capabilities: list[str]


@router.get("", response_model=list[ModuleMetadata])
def list_modules() -> list[ModuleMetadata]:
    return ModuleService().list_modules()


@router.get("/{module_name}", response_model=ModuleMetadata)
def get_module(module_name: str) -> ModuleMetadata:
    module = ModuleService().get_module(module_name)
    if module is None:
        raise HTTPException(status_code=404, detail=f"module '{module_name}' not found")
    return module


@router.post("/search", response_model=list[ModuleMetadata])
def search_modules(payload: ModuleSearchRequest) -> list[ModuleMetadata]:
    """
    Reuse-first search: returns approved modules that already satisfy the
    requested capabilities. An empty result means the AI/backend should
    treat this as a missing-module case (see Section 14 of the build spec).
    """
    return ModuleService().search_by_capabilities(payload.capabilities)
