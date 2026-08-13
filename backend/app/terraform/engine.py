"""
Whitelisted Terraform execution engine.

Section 17: create a Terraform service supporting fmt/init/validate/plan/
apply/destroy, but `apply` and `destroy` must only run through the
authorized deployment workflow — not exposed here. This engine intentionally
implements only fmt, init, and validate/plan; there is no method that can
apply or destroy, so the API surface itself makes those operations
unreachable from the portal or the AI.
"""
import logging
import shutil
import subprocess
from pathlib import Path

from app.models.terraform import TerraformStepResult, TerraformStepStatus

logger = logging.getLogger(__name__)

_TERRAFORM_BIN = "terraform"
_TIMEOUT_SECONDS = 120


class TerraformEngine:
    def __init__(self, working_dir: Path):
        self._cwd = working_dir

    def _binary_available(self) -> bool:
        return shutil.which(_TERRAFORM_BIN) is not None

    def _run(self, *args: str) -> TerraformStepResult:
        step_name = " ".join(args)
        if not self._binary_available():
            return TerraformStepResult(
                step=step_name,
                status=TerraformStepStatus.SKIPPED,
                detail="terraform binary not available in this environment",
            )
        try:
            result = subprocess.run(
                [_TERRAFORM_BIN, *args],
                cwd=self._cwd,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return TerraformStepResult(step=step_name, status=TerraformStepStatus.FAIL, detail="timed out")
        except OSError as exc:
            return TerraformStepResult(step=step_name, status=TerraformStepStatus.FAIL, detail=str(exc))

        status = TerraformStepStatus.PASS if result.returncode == 0 else TerraformStepStatus.FAIL
        detail = (result.stdout + result.stderr).strip()[-4000:]  # cap detail size
        return TerraformStepResult(step=step_name, status=status, detail=detail)

    def fmt(self) -> TerraformStepResult:
        return self._run("fmt", "-check")

    def init(self) -> TerraformStepResult:
        return self._run("init", "-backend=false", "-input=false")

    def validate(self) -> TerraformStepResult:
        return self._run("validate")

    def plan(self) -> TerraformStepResult:
        return self._run("plan", "-input=false", "-out=plan.tfplan")

    # NOTE: intentionally no apply() / destroy() methods on this class.
