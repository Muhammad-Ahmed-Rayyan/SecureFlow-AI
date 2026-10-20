# backend/tests/test_api_findings.py
# Integration tests for ingestion, findings querying, and metrics endpoints.

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.api_key}


def test_seed_and_list_findings():
    """Seed the dataset via /api/ingest/seed and verify findings querying."""
    # 1. Seed dataset
    res_seed = client.post("/api/ingest/seed", headers=AUTH_HEADERS)
    assert res_seed.status_code == 200
    data = res_seed.json()
    assert data["status"] == "ok"
    assert data["count"] == 200
    assert data["backlog_count"] == 96

    # 2. List all findings (default pagination)
    res_list = client.get("/api/findings", headers=AUTH_HEADERS)
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] == 200
    assert len(list_data["items"]) == 50  # default page_size
    assert list_data["total_pages"] == 4

    # 3. Filter by severity
    res_crit = client.get("/api/findings?severity=CRITICAL", headers=AUTH_HEADERS)
    assert res_crit.status_code == 200
    crit_data = res_crit.json()
    assert all(item["severity"] == "CRITICAL" for item in crit_data["items"])

    # 4. Filter by fix_ready
    res_fix_ready = client.get("/api/findings?fix_ready=true", headers=AUTH_HEADERS)
    assert res_fix_ready.status_code == 200
    fr_data = res_fix_ready.json()
    assert fr_data["total"] == 8
    assert all(item["fix_ready"] is True for item in fr_data["items"])

    # 5. Filter by language
    res_py = client.get("/api/findings?language=py", headers=AUTH_HEADERS)
    assert res_py.status_code == 200
    py_data = res_py.json()
    assert all(item["language_detected"] == "py" for item in py_data["items"])

    # 6. Search query
    res_search = client.get("/api/findings?q=VULN-0169", headers=AUTH_HEADERS)
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] == 1
    assert search_data["items"][0]["id"] == "VULN-0169"


def test_get_finding_detail():
    """Verify single finding detail retrieval and 404 behavior."""
    # Ensure seeded
    client.post("/api/ingest/seed", headers=AUTH_HEADERS)

    # Valid finding
    res_valid = client.get("/api/findings/VULN-0169", headers=AUTH_HEADERS)
    assert res_valid.status_code == 200
    item = res_valid.json()
    assert item["id"] == "VULN-0169"
    assert item["severity"] == "CRITICAL"
    assert item["vuln_type"] == "SQL Injection"
    assert item["cwe"] == "CWE-89"
    assert item["fix_ready"] is True

    # Unknown finding
    res_unknown = client.get("/api/findings/VULN-UNKNOWN-9999", headers=AUTH_HEADERS)
    assert res_unknown.status_code == 404


def test_metrics_endpoints():
    """Verify metrics summary, backlog breakdown, and funnel endpoints."""
    # Ensure seeded
    client.post("/api/ingest/seed", headers=AUTH_HEADERS)

    # Summary
    res_summary = client.get("/api/metrics/summary", headers=AUTH_HEADERS)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["backlog"]["total_findings"] == 200
    assert summary["backlog"]["open"] == 96
    assert summary["backlog"]["critical_high"] == 39
    assert summary["baseline"]["effort_hours_mean"] == 6.82
    assert summary["baseline"]["exposure_days_mean"] == 90.4

    # Backlog breakdown
    res_backlog = client.get("/api/metrics/backlog", headers=AUTH_HEADERS)
    assert res_backlog.status_code == 200
    backlog_data = res_backlog.json()
    assert backlog_data["total_backlog"] == 96
    assert "by_severity" in backlog_data
    assert "by_language" in backlog_data
    assert "by_age_bucket" in backlog_data

    # Funnel
    res_funnel = client.get("/api/metrics/funnel", headers=AUTH_HEADERS)
    assert res_funnel.status_code == 200
    funnel = res_funnel.json()["funnel"]
    assert len(funnel) == 6
    assert funnel[0]["step"] == "Total Backlog"
    assert funnel[0]["count"] == 96
    assert funnel[1]["step"] == "Auto-Fix Types"
    assert funnel[1]["count"] == 70
    assert funnel[3]["step"] == "Fix Ready (Demo Target Match)"
    assert funnel[3]["count"] == 8
