"""API-level tests for the /api/v1/terraform/plan endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_PAYLOAD = {
    "request_id": "REQ-TF-API-001",
    "source": "self_service",
    "user_id": "tester",
    "application": "payment",
    "environment": "dev",
    "region": "ap-south-1",
    "resources": [
        {"type": "vpc", "module": "vpc", "version": "1.0.0", "action": "reuse", "configuration": {}},
        {
            "type": "ec2",
            "module": "ec2",
            "version": "1.0.0",
            "action": "reuse",
            "configuration": {"instance_type": "t3.medium", "instance_count": 1},
        },
    ],
}


def test_plan_requires_existing_request() -> None:
    resp = client.post("/api/v1/terraform/plan", json={"request_id": "REQ-DOES-NOT-EXIST"})
    assert resp.status_code == 404


def test_plan_generates_config_for_existing_request() -> None:
    assert client.post("/api/v1/requests", json=_PAYLOAD).status_code == 201

    resp = client.post("/api/v1/terraform/plan", json={"request_id": "REQ-TF-API-001"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["request_id"] == "REQ-TF-API-001"
    assert len(body["generated_files"]) == 2
    # terraform binary is not installed in CI-less/offline environments —
    # SKIPPED is an acceptable, non-fatal outcome here.
    assert body["overall_status"] in ("PASS", "SKIPPED")

    status_resp = client.get("/api/v1/requests/REQ-TF-API-001/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("TERRAFORM_GENERATED", "PLAN_PASSED")


def test_get_plan_after_creation() -> None:
    get_resp = client.get("/api/v1/terraform/plan/REQ-TF-API-001")
    assert get_resp.status_code == 200
