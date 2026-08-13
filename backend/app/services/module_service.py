"""Thin service layer over the module registry repository (Phase 1 scope)."""
from app.config import get_settings
from app.models.module import ModuleMetadata
from app.repositories.module_registry import ModuleRegistryRepository


def get_module_registry() -> ModuleRegistryRepository:
    settings = get_settings()
    return ModuleRegistryRepository(settings.terraform_modules_path)


class ModuleService:
    def __init__(self, repo: ModuleRegistryRepository | None = None):
        self._repo = repo or get_module_registry()

    def list_modules(self) -> list[ModuleMetadata]:
        return self._repo.list_modules()

    def get_module(self, name: str) -> ModuleMetadata | None:
        return self._repo.get_module(name)

    def search_by_capabilities(self, capabilities: list[str]) -> list[ModuleMetadata]:
        return self._repo.find_by_capabilities(capabilities)
