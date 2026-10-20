# tests/test_health_and_auth.py — Phase 0 smoke tests for health endpoint and API-key auth.

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_open():
    """Health endpoint must be reachable without any API key."""
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "store" in body
    assert "version" in body


def test_missing_key_returns_401():
    """Any protected endpoint must return 401 when the key is absent."""
    r = client.get("/api/findings")
    assert r.status_code == 401


def test_wrong_key_returns_401():
    """Wrong API key must also return 401."""
    r = client.get("/api/findings", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


def test_correct_key_does_not_return_401():
    """Correct API key must not return 401 (may return 200 or 404 depending on phase)."""
    from app.config import settings
    r = client.get("/api/findings", headers={"X-API-Key": settings.api_key})
    assert r.status_code != 401
