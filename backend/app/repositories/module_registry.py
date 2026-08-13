"""
Reads module.json metadata files out of the Terraform module registry
(terraform/modules/<name>/module.json) and exposes them as validated
ModuleMetadata objects.

Phase 1: filesystem-backed. A later phase can swap this for a DynamoDB-backed
repository behind the same interface without touching callers.
"""
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.models.module import ModuleMetadata

logger = logging.getLogger(__name__)


class ModuleRegistryRepository:
    def __init__(self, modules_root: str | Path):
        self._root = Path(modules_root)

    def list_modules(self) -> list[ModuleMetadata]:
        modules: list[ModuleMetadata] = []
        if not self._root.exists():
            logger.warning("terraform modules path does not exist: %s", self._root)
            return modules

        for module_dir in sorted(self._root.iterdir()):
            metadata_file = module_dir / "module.json"
            if not metadata_file.is_file():
                continue
            try:
                raw = json.loads(metadata_file.read_text())
                modules.append(ModuleMetadata.model_validate(raw))
            except (json.JSONDecodeError, ValidationError) as exc:
                logger.error("invalid module.json in %s: %s", module_dir, exc)
        return modules

    def get_module(self, module_name: str) -> ModuleMetadata | None:
        for module in self.list_modules():
            if module.module_name == module_name:
                return module
        return None

    def find_by_capabilities(self, required_capabilities: list[str]) -> list[ModuleMetadata]:
        """
        Naive capability match used until the AI/embedding-based semantic
        search (Phase 11) lands. Returns approved modules whose capability
        set is a superset of what's required.
        """
        required = set(required_capabilities)
        return [
            m
            for m in self.list_modules()
            if m.status.value == "approved" and required.issubset(set(m.capabilities))
        ]
