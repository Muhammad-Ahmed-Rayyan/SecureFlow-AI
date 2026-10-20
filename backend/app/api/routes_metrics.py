# backend/app/api/routes_metrics.py
# Metrics API: headline summary, backlog breakdown, MTTR benchmarks, and remediation funnel.

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.metrics import (
    compute_backlog_breakdown,
    compute_funnel,
    compute_metrics_summary,
    compute_mttr,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
def get_metrics_summary() -> dict[str, Any]:
    """Headline metrics matching TAD section 8.1 data contract and UI consumption."""
    return compute_metrics_summary()


@router.get("/backlog")
def get_backlog_breakdown() -> dict[str, Any]:
    """Detailed breakdown of backlog by severity, language, age buckets, and live timeline."""
    return compute_backlog_breakdown()


@router.get("/funnel")
def get_funnel_metrics() -> dict[str, Any]:
    """Remediation funnel from raw backlog to merged pull requests."""
    return compute_funnel()


@router.get("/mttr")
def get_mttr_metrics() -> dict[str, Any]:
    """MTTR comparison between manual developer baseline and SecureFlow AI pipeline."""
    return compute_mttr()
