# store/memory.py — thread-safe in-memory Store implementation.
# Used for local development and unit tests; no external dependencies.

import threading
from copy import deepcopy
from typing import Any, Optional

from app.models import Event, Finding, Run
from app.store.base import Store


class MemoryStore(Store):
    """In-memory store backed by plain dicts, protected by an RLock."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._findings: dict[str, Finding] = {}
        self._runs: dict[str, Run] = {}
        self._events: dict[str, list[Event]] = {}   # run_id -> sorted list
        self._counters: dict[str, int] = {}

    def clear(self) -> None:
        with self._lock:
            self._findings.clear()
            self._runs.clear()
            self._events.clear()
            self._counters.clear()

    # --- Findings ---

    def upsert_finding(self, finding: Finding) -> None:
        with self._lock:
            self._findings[finding.id] = deepcopy(finding)

    save_finding = upsert_finding

    def get_finding(self, finding_id: str) -> Optional[Finding]:
        with self._lock:
            f = self._findings.get(finding_id)
            return deepcopy(f) if f else None

    def update_finding(self, finding_id: str, **fields: Any) -> None:
        with self._lock:
            f = self._findings.get(finding_id)
            if f is None:
                raise KeyError(f"Finding {finding_id} not found")
            updated = f.model_copy(update=fields)
            self._findings[finding_id] = updated

    def list_findings(self, filters: dict[str, Any]) -> list[Finding]:
        with self._lock:
            results: list[Finding] = list(self._findings.values())

        # Apply filters
        severity = filters.get("severity")
        if severity:
            results = [f for f in results if f.severity.value == severity.upper()]

        vuln_type = filters.get("type")
        if vuln_type:
            results = [f for f in results if f.vuln_type.lower() == vuln_type.lower()]

        repo = filters.get("repo")
        if repo:
            results = [f for f in results if f.repository == repo]

        tier = filters.get("tier")
        if tier:
            results = [f for f in results if f.tier.value == tier.upper()]

        status = filters.get("status")
        if status:
            results = [f for f in results if f.remediation_status.value == status.upper()]

        status_source = filters.get("status_source")
        if status_source:
            results = [f for f in results if f.status_source.lower() == status_source.lower()]

        language = filters.get("language")
        if language:
            results = [f for f in results if f.language_detected.lower() == language.lower()]

        fix_ready = filters.get("fix_ready")
        if fix_ready is True or fix_ready == "true":
            results = [f for f in results if f.fix_ready]

        q = filters.get("q", "").strip().lower()
        if q:
            results = [
                f for f in results
                if q in f.id.lower() or q in f.vuln_type.lower() or q in f.file_path.lower()
            ]

        # Sort by priority_score descending
        results.sort(key=lambda f: f.priority_score, reverse=True)

        # Pagination
        page = int(filters.get("page", 1))
        page_size = int(filters.get("page_size", 50))
        start = (page - 1) * page_size
        return results[start : start + page_size]

    def count_findings(self, filters: dict[str, Any]) -> int:
        """Return total count matching filters (ignores pagination)."""
        no_page = {k: v for k, v in filters.items() if k not in ("page", "page_size")}
        no_page["page"] = 1
        no_page["page_size"] = 999_999
        return len(self.list_findings(no_page))

    # --- Runs ---

    def create_run(self, run: Run) -> None:
        with self._lock:
            self._runs[run.id] = deepcopy(run)
            self._events.setdefault(run.id, [])

    def upsert_run(self, run: Run) -> None:
        with self._lock:
            self._runs[run.id] = deepcopy(run)
            self._events.setdefault(run.id, [])

    save_run = upsert_run

    def get_run(self, run_id: str) -> Optional[Run]:
        with self._lock:
            r = self._runs.get(run_id)
            return deepcopy(r) if r else None

    def update_run(self, run_id: str, **fields: Any) -> None:
        with self._lock:
            r = self._runs.get(run_id)
            if r is None:
                raise KeyError(f"Run {run_id} not found")
            self._runs[run_id] = r.model_copy(update=fields)

    def list_runs(self) -> list[Run]:
        with self._lock:
            runs = list(self._runs.values())
        runs.sort(key=lambda r: r.started_at or r.id, reverse=True)
        return deepcopy(runs)

    # --- Events ---

    def append_event(self, event: Event) -> None:
        with self._lock:
            self._events.setdefault(event.run_id, []).append(deepcopy(event))

    def list_events(self, run_id: str, after_seq: int = 0) -> list[Event]:
        with self._lock:
            all_events = self._events.get(run_id, [])
            return [deepcopy(e) for e in all_events if e.seq > after_seq]

    # --- Counters ---

    def incr_counter(self, name: str, amount: int = 1) -> int:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount
            return self._counters[name]

    def get_counter(self, name: str) -> int:
        with self._lock:
            return self._counters.get(name, 0)
