"""API-level tests using FastAPI's TestClient (no network, no AWS)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "ai-cloud-self-service-backend"


def test_list_modules_returns_approved_modules() -> None:
    resp = client.get("/api/v1/modules")
    assert resp.status_code == 200
    names = {m["module_name"] for m in resp.json()}
    assert "ec2" in names
    assert "vpc" in names


def test_get_module_not_found() -> None:
    resp = client.get("/api/v1/modules/eks")
    assert resp.status_code == 404


def test_search_modules_by_capability() -> None:
    resp = client.post("/api/v1/modules/search", json={"capabilities": ["encrypted-ebs"]})
    assert resp.status_code == 200
    names = {m["module_name"] for m in resp.json()}
    assert "ec2" in names


def test_create_and_get_request() -> None:
    payload = {
        "request_id": "REQ-TEST-001",
        "source": "self_service",
        "user_id": "tester",
        "application": "payment",
        "environment": "dev",
        "region": "ap-south-1",
        "resources": [
            {
                "type": "ec2",
                "module": "ec2",
                "version": "1.0.0",
                "action": "reuse",
                "configuration": {"instance_type": "t3.medium", "instance_count": 2},
            }
        ],
    }
    create_resp = client.post("/api/v1/requests", json=payload)
    assert create_resp.status_code == 201

    get_resp = client.get("/api/v1/requests/REQ-TEST-001")
    assert get_resp.status_code == 200
    assert get_resp.json()["application"] == "payment"


def test_duplicate_request_id_conflicts() -> None:
    payload = {
        "request_id": "REQ-TEST-DUP",
        "source": "self_service",
        "user_id": "tester",
        "application": "payment",
        "environment": "dev",
        "region": "ap-south-1",
        "resources": [
            {"type": "s3", "module": "s3", "version": "1.0.0", "action": "reuse", "configuration": {}}
        ],
    }
    assert client.post("/api/v1/requests", json=payload).status_code == 201
    assert client.post("/api/v1/requests", json=payload).status_code == 409
