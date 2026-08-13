"""
Tracks per-request lifecycle status in memory (Phase 1 only — a later phase
persists this to the Deployments/DeploymentRequests DynamoDB tables per
Section 33 and drives it from real approval/Jenkins events).
"""
from enum import Enum


class RequestStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    TERRAFORM_GENERATED = "TERRAFORM_GENERATED"
    PLAN_PASSED = "PLAN_PASSED"
    PLAN_FAILED = "PLAN_FAILED"


class StatusTracker:
    def __init__(self) -> None:
        self._store: dict[str, RequestStatus] = {}

    def set(self, request_id: str, status: RequestStatus) -> None:
        self._store[request_id] = status

    def get(self, request_id: str) -> RequestStatus | None:
        return self._store.get(request_id)


_tracker = StatusTracker()


def get_status_tracker() -> StatusTracker:
    return _tracker
