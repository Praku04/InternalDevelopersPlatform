"""Tests for the whitelisted TerraformEngine. Verifies it degrades gracefully
when the terraform binary is unavailable, and — crucially — that it exposes
no apply/destroy capability at all."""
import tempfile
from pathlib import Path

from app.models.terraform import TerraformStepStatus
from app.terraform.engine import TerraformEngine


def test_engine_has_no_apply_or_destroy_methods() -> None:
    assert not hasattr(TerraformEngine, "apply")
    assert not hasattr(TerraformEngine, "destroy")


def test_steps_report_skipped_when_binary_missing(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = TerraformEngine(Path(tmp))
        monkeypatch.setattr(engine, "_binary_available", lambda: False)
        result = engine.plan()
        assert result.status == TerraformStepStatus.SKIPPED
