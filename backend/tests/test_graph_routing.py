# backend/tests/test_graph_routing.py
# Unit tests verifying LangGraph conditional routing, retry loop, and run API endpoints.

import time
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agents.graph import workflow
from app.agents.state import RunState
from app.config import settings
from app.main import app
from app.models import Finding, RemediationStatus, RunStatus, SeverityEnum, TierEnum

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.api_key}


def test_routing_escalation_path():
    """Findings that are not AUTO_FIX or have no source available are escalated immediately."""
    finding = {
        "id": "VULN-0108",
        "vuln_type": "CSRF",
        "tier": TierEnum.ESCALATE.value,
        "source_available": False,
        "file_path": "src/main/service/File45.py",
    }
    state: RunState = {
        "run_id": "test-escalate-run",
        "finding_id": "VULN-0108",
        "finding": finding,
        "original_content": "def foo(): pass",
        "status": RunStatus.RUNNING.value,
        "attempts": 0,
    }

    final_state = workflow.invoke(state)
    assert final_state["status"] == RunStatus.ESCALATED.value


def test_routing_happy_path(monkeypatch):
    """Happy path: analyze -> fix -> validate (passed) -> open_pr -> END (PR_OPEN)."""
    finding = {
        "id": "VULN-0169",
        "vuln_type": "SQL Injection",
        "tier": TierEnum.AUTO_FIX.value,
        "source_available": True,
        "file_path": "src/main/service/File2.py",
        "cwe": "CWE-89",
    }

    mock_analysis = {
        "vulnerable_function": "get_user",
        "start_line": 20,
        "end_line": 25,
        "line_reported": 200,
        "drift": -180,
        "root_cause": "f-string query",
        "attack_scenario": "' OR 1=1 --",
        "cwe": "CWE-89",
        "fix_strategy": "parameterized query",
    }
    mock_patch = {
        "new_content": "def get_user(conn, u): return conn.execute('?', (u,))",
        "explanation": "parameterized query applied",
        "change_summary": "fixed SQLi",
        "confidence": 0.98,
        "risk": "low",
        "diff": "+ parameterized",
    }
    mock_evidence = {
        "policy": True,
        "before": {"functional": 2, "exploit": 1},
        "after": {"functional": 2, "exploit": 1},
        "bandit_before_ids": ["B608"],
        "bandit_after_ids": [],
        "bandit_applicable": True,
        "passed": True,
        "log_tail": "all tests passed",
    }
    mock_pr = {
        "number": 55,
        "url": "https://github.com/owner/repo/pull/55",
        "branch": "secureflow/fix-vuln-0169-sql-injection",
        "state": "open",
    }

    with patch("app.agents.graph.analyze_vulnerability", return_value=(mock_analysis, {"prompt_tokens": 10, "completion_tokens": 10})), \
         patch("app.agents.graph.generate_patch", return_value=(mock_patch, {"prompt_tokens": 20, "completion_tokens": 20})), \
         patch("app.agents.graph.create_remediation_pr", return_value=mock_pr):

        # Mock validate_patch returning an object with model_dump
        mock_val_obj = MagicMock()
        mock_val_obj.model_dump.return_value = mock_evidence
        mock_val_obj.passed = True
        mock_val_obj.log_tail = ""

        with patch("app.agents.graph.validate_patch", return_value=mock_val_obj):
            state: RunState = {
                "run_id": "test-happy-run",
                "finding_id": "VULN-0169",
                "finding": finding,
                "original_content": "def get_user(conn, u): pass",
                "status": RunStatus.RUNNING.value,
                "attempts": 0,
            }
            final_state = workflow.invoke(state)
            assert final_state["status"] == RunStatus.PR_OPEN.value
            assert final_state["pr"]["number"] == 55


def test_routing_retry_then_pass():
    """Retry loop: validator fails on attempt 1, fixer is called with last_error, passes on attempt 2."""
    finding = {
        "id": "VULN-0169",
        "vuln_type": "SQL Injection",
        "tier": TierEnum.AUTO_FIX.value,
        "source_available": True,
        "file_path": "src/main/service/File2.py",
    }

    call_count = {"validate": 0}

    def mock_validate(*args, **kwargs):
        call_count["validate"] += 1
        m = MagicMock()
        if call_count["validate"] == 1:
            m.passed = False
            m.log_tail = "syntax error near line 4"
            m.model_dump.return_value = {"passed": False, "log_tail": "syntax error near line 4"}
        else:
            m.passed = True
            m.log_tail = "all tests passed"
            m.model_dump.return_value = {"passed": True, "log_tail": "all tests passed"}
        return m

    mock_analysis = {"vulnerable_function": "query"}
    mock_patch = {"new_content": "code", "explanation": "fix"}
    mock_pr = {"number": 56, "url": "http://pr", "state": "open"}

    with patch("app.agents.graph.analyze_vulnerability", return_value=(mock_analysis, {})), \
         patch("app.agents.graph.generate_patch", return_value=(mock_patch, {})), \
         patch("app.agents.graph.validate_patch", side_effect=mock_validate), \
         patch("app.agents.graph.create_remediation_pr", return_value=mock_pr):

        state: RunState = {
            "run_id": "test-retry-run",
            "finding_id": "VULN-0169",
            "finding": finding,
            "original_content": "code",
            "status": RunStatus.RUNNING.value,
            "attempts": 0,
        }
        final_state = workflow.invoke(state)
        assert final_state["status"] == RunStatus.PR_OPEN.value
        assert final_state["attempts"] == 2
        assert call_count["validate"] == 2


def test_remediate_api_endpoint():
    """Triggering remediation via POST /api/findings/{id}/remediate returns 202 and creates Run."""
    # Ensure seeded
    client.post("/api/ingest/seed", headers=AUTH_HEADERS)

    print("ROUTES IN PYTEST:", [r.path for r in app.routes])
    res = client.post("/api/findings/VULN-0169/remediate", headers=AUTH_HEADERS)
    print("REMEDIATE RESPONSE:", res.status_code, res.text)
    assert res.status_code == 202
    data = res.json()
    assert "run_id" in data
    assert data["status"] in ("QUEUED", "RUNNING", "PR_OPEN")

    run_id = data["run_id"]

    # Poll run
    res_run = client.get(f"/api/runs/{run_id}", headers=AUTH_HEADERS)
    assert res_run.status_code == 200
    assert res_run.json()["id"] == run_id

    # Check events
    res_events = client.get(f"/api/runs/{run_id}/events?after=0", headers=AUTH_HEADERS)
    assert res_events.status_code == 200
    assert isinstance(res_events.json(), list)
