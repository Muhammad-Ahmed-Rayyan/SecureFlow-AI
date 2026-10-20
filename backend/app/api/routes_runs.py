# backend/app/api/routes_runs.py
# Runs API: triggering remediations, listing run history, polling run details, and live trace streaming.

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.models import Event, Run
from app.services.runs import start_run
from app.store import get_store

router = APIRouter(tags=["runs"])


class RemediateResponse(BaseModel):
    run_id: str
    finding_id: str
    status: str


@router.post("/findings/{finding_id}/remediate", status_code=status.HTTP_202_ACCEPTED, response_model=RemediateResponse)
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
def get_run_events(run_id: str, after: int = Query(0, ge=0, description="Return events with seq > after")):
    """Incremental event stream polling endpoint for live agent trace visualization."""
    store = get_store()
    return store.list_events(run_id, after_seq=after)
