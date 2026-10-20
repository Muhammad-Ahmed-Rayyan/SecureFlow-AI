# tests/test_store_memory.py — contract tests for the in-memory store.
# These same assertions will be re-run against FirestoreStore in Phase 5.

import pytest
from datetime import datetime, timezone

from app.models import (
    Event, EventLevel, Finding, RemediationStatus, Run, RunStatus, SeverityEnum,
    TierEnum,
)
from app.store.memory import MemoryStore


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


def _make_finding(id: str = "VULN-0001", severity: SeverityEnum = SeverityEnum.HIGH) -> Finding:
    return Finding(
        id=id,
        severity=severity,
        vuln_type="SQL Injection",
        repository="notification-svc",
        file_path="src/main/service/File2.py",
        tier=TierEnum.AUTO_FIX,
        priority_score=90.0,
        source_available=True,
        language_detected="py",
    )


def _make_run(run_id: str = "run-001", finding_id: str = "VULN-0001") -> Run:
    return Run(id=run_id, finding_id=finding_id, started_at=datetime.now(timezone.utc))


# --- Finding contract ---

def test_upsert_and_get_finding(store):
    f = _make_finding()
    store.upsert_finding(f)
    got = store.get_finding(f.id)
    assert got is not None
    assert got.id == f.id
    assert got.severity == SeverityEnum.HIGH


def test_get_missing_finding_returns_none(store):
    assert store.get_finding("VULN-9999") is None


def test_update_finding_patches_fields(store):
    f = _make_finding()
    store.upsert_finding(f)
    store.update_finding(f.id, remediation_status=RemediationStatus.QUEUED)
    got = store.get_finding(f.id)
    assert got.remediation_status == RemediationStatus.QUEUED


def test_update_missing_finding_raises(store):
    with pytest.raises(KeyError):
        store.update_finding("VULN-MISSING", remediation_status=RemediationStatus.QUEUED)


def test_list_findings_returns_sorted(store):
    f_low = Finding(id="LOW-1", severity=SeverityEnum.LOW, priority_score=10.0)
    f_crit = Finding(id="CRIT-1", severity=SeverityEnum.CRITICAL, priority_score=120.0)
    store.upsert_finding(f_low)
    store.upsert_finding(f_crit)
    results = store.list_findings({})
    assert results[0].id == "CRIT-1"


def test_list_findings_filter_severity(store):
    store.upsert_finding(_make_finding("V1", SeverityEnum.HIGH))
    store.upsert_finding(_make_finding("V2", SeverityEnum.LOW))
    results = store.list_findings({"severity": "HIGH"})
    assert all(f.severity == SeverityEnum.HIGH for f in results)


def test_list_findings_filter_fix_ready(store):
    ready = _make_finding("READY-1")
    not_ready = Finding(
        id="NOT-READY-1",
        tier=TierEnum.ESCALATE,
        source_available=False,
        language_detected="js",
    )
    store.upsert_finding(ready)
    store.upsert_finding(not_ready)
    results = store.list_findings({"fix_ready": True})
    ids = [f.id for f in results]
    assert "READY-1" in ids
    assert "NOT-READY-1" not in ids


# --- Run contract ---

def test_create_and_get_run(store):
    r = _make_run()
    store.create_run(r)
    got = store.get_run(r.id)
    assert got is not None
    assert got.id == r.id


def test_get_missing_run_returns_none(store):
    assert store.get_run("run-missing") is None


def test_update_run_patches_fields(store):
    r = _make_run()
    store.create_run(r)
    store.update_run(r.id, status=RunStatus.RUNNING, current_agent="analyzer")
    got = store.get_run(r.id)
    assert got.status == RunStatus.RUNNING
    assert got.current_agent == "analyzer"


def test_list_runs_newest_first(store):
    r1 = Run(id="run-1", finding_id="F1", started_at=datetime(2026, 10, 20, 9, 0, 0))
    r2 = Run(id="run-2", finding_id="F2", started_at=datetime(2026, 10, 20, 10, 0, 0))
    store.create_run(r1)
    store.create_run(r2)
    runs = store.list_runs()
    assert runs[0].id == "run-2"


# --- Event contract ---

def test_append_and_list_events(store):
    store.create_run(_make_run())
    e1 = Event(run_id="run-001", seq=1, agent="triage", message="Starting triage")
    e2 = Event(run_id="run-001", seq=2, agent="analyzer", message="Analyzing")
    store.append_event(e1)
    store.append_event(e2)
    events = store.list_events("run-001", after_seq=0)
    assert len(events) == 2
    assert events[0].seq == 1


def test_list_events_after_seq(store):
    store.create_run(_make_run())
    for i in range(1, 6):
        store.append_event(Event(run_id="run-001", seq=i, message=f"event {i}"))
    events = store.list_events("run-001", after_seq=3)
    assert [e.seq for e in events] == [4, 5]


# --- Counter contract ---

def test_incr_counter(store):
    val = store.incr_counter("total_runs")
    assert val == 1
    val = store.incr_counter("total_runs")
    assert val == 2


def test_get_counter_missing_returns_zero(store):
    assert store.get_counter("nonexistent") == 0
