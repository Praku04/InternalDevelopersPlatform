"""
In-memory deployment-request store for Phase 1 local development only.

This is explicitly NOT the production repository — Section 33 calls for a
DynamoDB-backed DeploymentRequests table. This in-memory implementation
exists so the API contract and request lifecycle can be exercised end to
end before AWS wiring lands, and is swapped out (behind the same method
signatures) in a later phase.
"""
from app.models.deployment import DeploymentSpecification


class InMemoryRequestRepository:
    def __init__(self) -> None:
        self._store: dict[str, DeploymentSpecification] = {}

    def create(self, spec: DeploymentSpecification) -> DeploymentSpecification:
        if spec.request_id in self._store:
            raise ValueError(f"request_id '{spec.request_id}' already exists")
        self._store[spec.request_id] = spec
        return spec

    def get(self, request_id: str) -> DeploymentSpecification | None:
        return self._store.get(request_id)

    def list(self) -> list[DeploymentSpecification]:
        return list(self._store.values())


# Process-lifetime singleton for Phase 1 (no persistence across restarts).
_repository = InMemoryRequestRepository()


def get_request_repository() -> InMemoryRequestRepository:
    return _repository
