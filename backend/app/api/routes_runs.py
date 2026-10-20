# backend/app/api/routes_runs.py
# Runs API: triggering remediations, listing run history, polling run details, and live trace streaming.

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.models import Event, RemediationStatus, Run, RunStatus
from app.services.runs import start_run
from app.store import get_store

router = APIRouter(tags=["runs"])


class RemediateResponse(BaseModel):
    run_id: str
    finding_id: str
    status: str


class BatchRemediateRequest(BaseModel):
    finding_ids: Optional[list[str]] = None
    top_n: int = 3
    severity: Optional[str] = None
    fix_ready_only: bool = True


class BatchRemediateResponse(BaseModel):
    runs: list[RemediateResponse]
    count: int
    skipped: list[str] = []


@router.post(
    "/findings/{finding_id}/remediate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RemediateResponse,
)
def trigger_remediation(finding_id: str):
    """Start an autonomous remediation run for a finding (202 Accepted).

    Enforces guards:
    - 404 if finding not found
    - 409 if run or PR already active
    - 429 if total runs cap reached
    """
    run = start_run(finding_id)
    return RemediateResponse(
        run_id=run.id,
        finding_id=finding_id,
        status=run.status.value,
    )


@router.post(
    "/remediate/batch",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BatchRemediateResponse,
)
def trigger_batch_remediation(req: BatchRemediateRequest | None = None):
    """Batch trigger remediation for top priority fix-ready findings."""
    store = get_store()
    params = req or BatchRemediateRequest()

    candidates = []
    if params.finding_ids:
        for fid in params.finding_ids:
            f = store.get_finding(fid)
            if f and (not params.fix_ready_only or f.fix_ready):
                candidates.append(f)
    else:
        all_f = store.list_findings({"page": 1, "page_size": 999_999})
        for f in all_f:
            if params.fix_ready_only and not f.fix_ready:
                continue
            if params.severity and f.severity.value != params.severity.upper():
                continue
            if f.remediation_status in (
                RemediationStatus.RUNNING,
                RemediationStatus.PR_OPEN,
                RemediationStatus.MERGED,
            ):
                continue
            candidates.append(f)

    # Sort candidates strictly by priority_score descending
    candidates.sort(key=lambda f: f.priority_score, reverse=True)
    selected = candidates[: params.top_n]

    results: list[RemediateResponse] = []
    skipped: list[str] = []

    for f in selected:
        try:
            run = start_run(f.id)
            results.append(
                RemediateResponse(
                    run_id=run.id, finding_id=f.id, status=run.status.value
                )
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                raise
            skipped.append(f"{f.id}: {exc.detail}")
        except Exception as exc:
            skipped.append(f"{f.id}: {str(exc)}")

    return BatchRemediateResponse(runs=results, count=len(results), skipped=skipped)


@router.get("/runs", response_model=list[Run])
def list_runs():
    """List all remediation runs, ordered newest first."""
    store = get_store()
    return store.list_runs()


@router.get("/runs/{run_id}", response_model=Run)
def get_run_by_id(run_id: str):
    """Retrieve full run document including patch, validation evidence, PR details, and timings."""
    store = get_store()
    r = store.get_run(run_id)
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )
    return r


@router.get("/runs/{run_id}/events", response_model=list[Event])
def get_run_events(
    run_id: str,
    after: int = Query(0, ge=0, description="Return events with seq > after"),
):
    """Incremental event stream polling endpoint for live agent trace visualization."""
    store = get_store()
    return store.list_events(run_id, after_seq=after)
