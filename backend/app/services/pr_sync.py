# backend/app/services/pr_sync.py
# Syncs live GitHub pull request states (open, merged, closed) into run and finding records.
# Automatically updates finding remediation_status to MERGED or REJECTED.
# Throttled to at most once per 15 seconds unless forced.

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from app.models import FindingStatus, RemediationStatus, RunStatus
from app.store import get_store
from app.tools.github_tool import get_pr_state

logger = logging.getLogger("secureflow.services.pr_sync")

_last_sync_time: float = 0.0
_cached_sync_result: dict[str, Any] = {"synced": 0, "merged": 0, "closed": 0, "skipped": False}


def sync_prs(force: bool = False) -> dict[str, Any]:
    """Sync live GitHub pull request state for all runs with an open PR."""
    global _last_sync_time, _cached_sync_result
    now = time.time()

    if not force and (now - _last_sync_time < 15.0):
        return {**_cached_sync_result, "skipped": True}

    store = get_store()
    all_runs = store.list_runs()
    synced_count = 0
    merged_count = 0
    closed_count = 0

    for r in all_runs:
        if not r.pr or not r.pr.number:
            continue

        # If already terminal and recorded, skip polling GitHub
        if r.pr.state in ("merged", "closed") and r.pr.closed_at:
            continue

        try:
            live = get_pr_state(r.pr.number)
            live_state = live.get("state", "open")
            is_merged = bool(live.get("merged", False))

            r.pr.state = live_state
            r.pr.merged = is_merged
            if live.get("merged_at"):
                r.pr.merged_at = live["merged_at"]
            if live.get("closed_at"):
                r.pr.closed_at = live["closed_at"]

            synced_count += 1

            # Finding sync
            finding = store.get_finding(r.finding_id)
            if finding:
                if is_merged or live_state == "merged":
                    merged_count += 1
                    finding.status = FindingStatus.MERGED
                    finding.remediation_status = RemediationStatus.MERGED
                    store.save_finding(finding)
                elif live_state == "closed":
                    closed_count += 1
                    finding.status = FindingStatus.REJECTED
                    finding.remediation_status = RemediationStatus.REJECTED
                    store.save_finding(finding)

            store.save_run(r)
        except Exception as exc:
            logger.warning("Failed to sync PR #%s for run %s: %s", r.pr.number, r.id, exc)

    _last_sync_time = now
    _cached_sync_result = {
        "synced": synced_count,
        "merged": merged_count,
        "closed": closed_count,
        "skipped": False,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    return _cached_sync_result
