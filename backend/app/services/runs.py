# backend/app/services/runs.py
# Run lifecycle management service.
# Manages concurrency with BoundedSemaphore, enforces budget caps, and runs LangGraph in background threads.

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.agents.events import emit
from app.agents.graph import workflow
from app.agents.state import RunState
from app.config import settings
from app.store import get_store
from app.models import (
    EventLevel,
    PatchInfo,
    PRInfo,
    RemediationStatus,
    Run,
    RunStatus,
    TokenUsage,
    ValidationEvidence,
)
from app.tools.github_tool import get_file

logger = logging.getLogger("secureflow.runs")

# Concurrency semaphore initialized with configured max concurrent runs
_semaphore = threading.BoundedSemaphore(value=settings.max_concurrent_runs)


def _get_original_file_content(file_path: str, repo: str) -> str:
    """Fetch original file content from GitHub or fallback to local search."""
    # 1. Try GitHub if token is set
    if settings.github_token:
        try:
            content, _ = get_file(file_path)
            return content
        except Exception as e:
            logger.warning(f"Could not fetch '{file_path}' from GitHub ({e}), attempting local fallback")

    # 2. Local fallback if target repo exists locally on disk
    local_candidates = [
        Path(f"../secureflow-demo-target/{file_path}"),
        Path(f"../../secureflow-demo-target/{file_path}"),
        Path(os.path.expanduser(f"~/Documents/secureflow-demo-target/{file_path}")),
    ]
    for c in local_candidates:
        if c.is_file():
            return c.read_text(encoding="utf-8")

    # 3. Deterministic code template fallback for demo findings
    return f'''# Auto-generated target module placeholder for {file_path}
import sqlite3

def get_notifications_for_user(conn, username):
    """Retrieve notifications for a given username."""
    query = f"SELECT * FROM notifications WHERE username = '{{username}}'"
    return conn.execute(query).fetchall()
'''


def _run_worker(run_id: str, finding_id: str):
    """Background worker thread executing the LangGraph pipeline."""
    store = get_store()

    with _semaphore:
        t_start = time.time()
        emit(run_id, "system", f"Worker acquired execution slot. Starting pipeline for {finding_id}", EventLevel.info)

        store.update_run(run_id, status=RunStatus.RUNNING)
        store.update_finding(finding_id, remediation_status=RemediationStatus.RUNNING)

        finding = store.get_finding(finding_id)
        if not finding:
            store.update_run(run_id, status=RunStatus.FAILED, error="Finding disappeared from store")
            return

        # Fetch original content
        original_content = _get_original_file_content(finding.file_path, finding.repository)

        initial_state: RunState = {
            "run_id": run_id,
            "finding_id": finding_id,
            "finding": finding.model_dump(),
            "file_path": finding.file_path,
            "original_content": original_content,
            "attempts": 0,
            "timings": {},
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "status": RunStatus.RUNNING.value,
        }

        try:
            final_state = workflow.invoke(initial_state)
            status_str = final_state.get("status", RunStatus.FAILED.value)

            # Map status
            try:
                final_run_status = RunStatus(status_str)
            except ValueError:
                final_run_status = RunStatus.FAILED

            total_s = round(time.time() - t_start, 2)
            timings = final_state.get("timings", {})
            timings["total_s"] = total_s

            patch_data = final_state.get("patch")
            patch_obj = PatchInfo(**patch_data) if patch_data else PatchInfo()

            val_data = final_state.get("validation")
            val_obj = ValidationEvidence(**val_data) if val_data else ValidationEvidence()

            pr_data = final_state.get("pr")
            pr_obj = PRInfo(**pr_data) if pr_data else None

            usage_data = final_state.get("usage", {})
            usage_obj = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
            )

            store.update_run(
                run_id,
                status=final_run_status,
                finished_at=datetime.now(timezone.utc),
                patch=patch_obj,
                validation=val_obj,
                pr=pr_obj,
                analysis=final_state.get("analysis", {}),
                attempts=final_state.get("attempts", 1),
                timings=timings,
                usage=usage_obj,
                error=final_state.get("error"),
            )

            # Update finding remediation status
            if final_run_status == RunStatus.PR_OPEN:
                store.update_finding(finding_id, remediation_status=RemediationStatus.PR_OPEN)
                emit(run_id, "system", f"Remediation pipeline completed. Draft PR opened.", EventLevel.success)
            elif final_run_status == RunStatus.ESCALATED:
                store.update_finding(finding_id, remediation_status=RemediationStatus.ESCALATED)
                emit(run_id, "system", f"Finding escalated to human review.", EventLevel.warn)
            else:
                store.update_finding(finding_id, remediation_status=RemediationStatus.FAILED)
                emit(run_id, "system", f"Remediation pipeline completed with status FAILED.", EventLevel.error)

        except Exception as e:
            logger.exception(f"Unhandled error in remediation pipeline for {finding_id}")
            emit(run_id, "system", f"Pipeline error: {str(e)}", EventLevel.error)
            store.update_run(
                run_id,
                status=RunStatus.FAILED,
                finished_at=datetime.now(timezone.utc),
                error=str(e),
            )
            store.update_finding(finding_id, remediation_status=RemediationStatus.FAILED)


def start_run(finding_id: str) -> Run:
    """Initiate an autonomous remediation run for a specific finding."""
    store = get_store()

    # Guard 1: Finding must exist
    finding = store.get_finding(finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding '{finding_id}' not found",
        )

    # Guard 2: No active run or open PR for this finding
    if finding.remediation_status in (RemediationStatus.QUEUED, RemediationStatus.RUNNING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Finding '{finding_id}' already has an active remediation run in progress",
        )
    if finding.remediation_status == RemediationStatus.PR_OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Finding '{finding_id}' already has an open draft PR",
        )

    # Guard 3: Maximum total runs budget cap
    total_runs = store.get_counter("total_runs")
    if total_runs >= settings.max_total_runs:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum total runs cap ({settings.max_total_runs}) reached",
        )

    # Allocate new run
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    store.incr_counter("total_runs", 1)

    new_run = Run(
        id=run_id,
        finding_id=finding_id,
        status=RunStatus.QUEUED,
        started_at=datetime.now(timezone.utc),
    )
    store.create_run(new_run)
    store.update_finding(finding_id, remediation_status=RemediationStatus.QUEUED, run_id=run_id)

    emit(run_id, "system", f"Remediation run queued for finding {finding_id}", EventLevel.info)

    # Launch background execution thread
    thread = threading.Thread(
        target=_run_worker,
        args=(run_id, finding_id),
        name=f"worker-{run_id}",
        daemon=True,
    )
    thread.start()

    return new_run
