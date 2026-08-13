"""Tests for the filesystem-backed module registry against the real terraform/modules directory."""
from pathlib import Path

import pytest

from app.repositories.module_registry import ModuleRegistryRepository

MODULES_ROOT = Path(__file__).resolve().parents[2] / "terraform" / "modules"


@pytest.fixture
def repo() -> ModuleRegistryRepository:
    return ModuleRegistryRepository(MODULES_ROOT)


def test_lists_all_approved_modules(repo: ModuleRegistryRepository) -> None:
    modules = repo.list_modules()
    names = {m.module_name for m in modules}
    assert {"vpc", "ec2", "security-group", "alb", "s3"}.issubset(names)


def test_all_seeded_modules_are_approved(repo: ModuleRegistryRepository) -> None:
    for module in repo.list_modules():
        assert module.status.value == "approved"
        assert module.security_status.value == "approved"


def test_get_module_by_name(repo: ModuleRegistryRepository) -> None:
    ec2 = repo.get_module("ec2")
    assert ec2 is not None
    assert "encrypted-ebs" in ec2.capabilities
    assert "imdsv2" in ec2.capabilities


def test_get_missing_module_returns_none(repo: ModuleRegistryRepository) -> None:
    assert repo.get_module("eks") is None


def test_find_by_capabilities_matches_ec2(repo: ModuleRegistryRepository) -> None:
    results = repo.find_by_capabilities(["encrypted-ebs", "monitoring"])
    names = {m.module_name for m in results}
    assert "ec2" in names


def test_find_by_capabilities_no_match_returns_empty(repo: ModuleRegistryRepository) -> None:
    # No approved module currently claims Kubernetes/EKS capability.
    results = repo.find_by_capabilities(["eks-cluster"])
    assert results == []


def test_nonexistent_modules_path_returns_empty_list() -> None:
    repo = ModuleRegistryRepository("/nonexistent/path")
    assert repo.list_modules() == []
