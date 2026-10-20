# backend/tests/test_metrics_and_sync.py
# Unit tests for metrics calculation, PR status synchronization, and batch remediation.

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models import (
    Finding,
    FindingStatus,
    PullRequestInfo,
    RemediationStatus,
    RemediationTier,
    Run,
    RunStatus,
    SeverityEnum,
    UsageInfo,
)
from app.services.metrics import (
    compute_backlog_breakdown,
    compute_funnel,
    compute_metrics_summary,
    compute_mttr,
)
from app.services.pr_sync import sync_prs
from app.store import get_store


@pytest.fixture(autouse=True)
def clean_store():
    store = get_store()
    store.clear()
    yield store


def test_metrics_empty_store():
    summary = compute_metrics_summary()
    assert summary["total_findings"] == 0
    assert summary["open_findings"] == 0
    assert summary["acceptance"]["rate"] is None

    funnel = compute_funnel()
    assert len(funnel["stages"]) == 6
    assert funnel["total_backlog"] == 0

    backlog = compute_backlog_breakdown()
    assert len(backlog["timeline"]) == 2
    assert backlog["total_backlog"] == 0

    mttr = compute_mttr()
    assert mttr["reduction_pct"] >= 0


def test_metrics_with_synthetic_runs(clean_store):
    store = clean_store
    now = datetime.now(timezone.utc)

    # 1. Create finding
    f = Finding(
        id="VULN-9999",
        repository="test-repo",
        scan_tool="bandit",
        language="python",
        severity=SeverityEnum.CRITICAL,
        vulnerability_type="SQL Injection",
        affected_file="src/db.py",
        affected_line=42,
        description="SQL injection vulnerability",
        suggested_fix_available=False,
        current_status="Open",
        days_open=45,
        baseline_hours_reported=10.0,
        baseline_hours_imputed=None,
        tier=RemediationTier.AUTO_FIX,
        tier_reason="Fix-ready finding",
        priority_score=95.0,
        is_fix_ready=True,
    )
    store.save_finding(f)

    # 2. Create completed run with PR
    pr = PullRequestInfo(
        number=101,
        url="https://github.com/test/pull/101",
        branch="secureflow/fix-vuln-9999",
        state="merged",
        merged=True,
        created_at=now,
        merged_at=now,
    )
    run = Run(
        id="run-9999",
        finding_id=f.id,
        status=RunStatus.PR_OPEN,
        agent_remediation_status="PR_OPENED",
        attempts=1,
        pr=pr,
        usage=UsageInfo(prompt_tokens=500, completion_tokens=150, total_tokens=650),
        started_at=now,
    )
    store.save_run(run)

    summary = compute_metrics_summary()
    assert summary["total_findings"] == 1
    assert summary["open_findings"] == 1
    assert summary["pipeline"]["runs_total"] == 1
    assert summary["acceptance"]["merged"] == 1
    assert summary["acceptance"]["rate"] == 1.0


@patch("app.services.pr_sync.get_pr_state")
def test_pr_sync_merges_finding(mock_get_pr_state, clean_store):
    store = clean_store
    now = datetime.now(timezone.utc)

    f = Finding(
        id="VULN-0001",
        repository="test-repo",
        scan_tool="bandit",
        language="python",
        severity=SeverityEnum.HIGH,
        vulnerability_type="Hardcoded Secret",
        affected_file="config.py",
        affected_line=10,
        description="Secret in file",
        suggested_fix_available=False,
        current_status="Open",
        days_open=15,
        tier=RemediationTier.AUTO_FIX,
        priority_score=80.0,
    )
    store.save_finding(f)

    run = Run(
        id="run-0001",
        finding_id=f.id,
        status=RunStatus.PR_OPEN,
        agent_remediation_status="PR_OPENED",
        attempts=1,
        pr=PullRequestInfo(
            number=42,
            url="https://github.com/test/pull/42",
            branch="secureflow/fix",
            state="open",
            merged=False,
        ),
        started_at=now,
    )
    store.save_run(run)

    # Mock PR state returned as merged
    mock_get_pr_state.return_value = {
        "number": 42,
        "state": "merged",
        "merged": True,
        "created_at": now,
        "merged_at": now,
        "closed_at": None,
    }

    res = sync_prs(force=True)
    assert res["synced"] == 1
    assert res["merged"] == 1

    updated_finding = store.get_finding(f.id)
    assert updated_finding.remediation_status == RemediationStatus.MERGED
    assert updated_finding.status == FindingStatus.MERGED


def test_batch_remediation_api(clean_store):
    store = clean_store
    client = TestClient(app)
    headers = {"X-API-Key": settings.api_key}

    # Add 3 findings, 2 fix-ready
    f1 = Finding(
        id="VULN-A",
        repository="test-repo",
        scan_tool="bandit",
        language="python",
        severity=SeverityEnum.CRITICAL,
        vulnerability_type="SQL Injection",
        affected_file="a.py",
        affected_line=1,
        description="SQL injection",
        suggested_fix_available=False,
        current_status="Open",
        days_open=10,
        tier=RemediationTier.AUTO_FIX,
        priority_score=90.0,
        source_available=True,
        language_detected="py",
        is_fix_ready=True,
    )
    f2 = Finding(
        id="VULN-B",
        repository="test-repo",
        scan_tool="bandit",
        language="python",
        severity=SeverityEnum.CRITICAL,
        vulnerability_type="XSS",
        affected_file="b.py",
        affected_line=2,
        description="XSS issue",
        suggested_fix_available=False,
        current_status="Open",
        days_open=12,
        tier=RemediationTier.AUTO_FIX,
        priority_score=85.0,
        source_available=True,
        language_detected="py",
        is_fix_ready=True,
    )
    f3 = Finding(
        id="VULN-C",
        repository="test-repo",
        scan_tool="bandit",
        language="python",
        severity=SeverityEnum.LOW,
        vulnerability_type="Info Leak",
        affected_file="c.py",
        affected_line=3,
        description="Info",
        suggested_fix_available=False,
        current_status="Open",
        days_open=5,
        tier=RemediationTier.AUTO_FIX,
        priority_score=40.0,
        source_available=False,
        language_detected="py",
        is_fix_ready=False,
    )
    store.save_finding(f1)
    store.save_finding(f2)
    store.save_finding(f3)

    with patch("app.api.routes_runs.start_run") as mock_start:
        mock_start.side_effect = lambda fid: Run(
            id=f"run-{fid}",
            finding_id=fid,
            status=RunStatus.QUEUED,
            agent_remediation_status="NOT_STARTED",
            attempts=0,
        )

        resp = client.post(
            "/api/remediate/batch",
            json={"top_n": 2, "severity": "CRITICAL", "fix_ready_only": True},
            headers=headers,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["count"] == 2
        assert [r["finding_id"] for r in data["runs"]] == ["VULN-A", "VULN-B"]
