# backend/app/api/routes_findings.py
# Findings API: listing, filtering, pagination, search, and detail endpoints.

from __future__ import annotations

import math
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.main import get_store
from app.models import Finding

router = APIRouter(prefix="/findings", tags=["findings"])


class FindingsListResponse(BaseModel):
    items: list[Finding]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=FindingsListResponse)
def list_findings(
    severity: Optional[str] = Query(None, description="CRITICAL, HIGH, MEDIUM, LOW"),
    type: Optional[str] = Query(None, description="Vulnerability type (e.g. SQL Injection)"),
    vuln_type: Optional[str] = Query(None, description="Alias for type"),
    repo: Optional[str] = Query(None, description="Repository filter"),
    repository: Optional[str] = Query(None, description="Alias for repo"),
    tier: Optional[str] = Query(None, description="AUTO_FIX, DEPENDENCY, ESCALATE, UNSUPPORTED_LANG"),
    status: Optional[str] = Query(None, description="Remediation status (NEW, QUEUED, PR_OPEN, etc.)"),
    status_source: Optional[str] = Query(None, description="Source status (Open, In Progress, Fixed, Verified)"),
    language: Optional[str] = Query(None, description="Detected language (py, js, ts, java)"),
    fix_ready: Optional[bool] = Query(None, description="Only fix-ready findings"),
    q: Optional[str] = Query(None, description="Free text search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
):
    """List findings with multi-criteria filtering, search, and pagination."""
    store = get_store()

    target_type = type or vuln_type
    target_repo = repo or repository

    filters: dict[str, Any] = {
        "page": page,
        "page_size": page_size,
    }
    if severity:
        filters["severity"] = severity
    if target_type:
        filters["type"] = target_type
    if target_repo:
        filters["repo"] = target_repo
    if tier:
        filters["tier"] = tier
    if status:
        filters["status"] = status
    if status_source:
        filters["status_source"] = status_source
    if language:
        filters["language"] = language
    if fix_ready is not None:
        filters["fix_ready"] = fix_ready
    if q:
        filters["q"] = q

    items = store.list_findings(filters)
    total = store.count_findings(filters)
    total_pages = max(1, math.ceil(total / page_size))

    return FindingsListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{finding_id}", response_model=Finding)
def get_finding_by_id(finding_id: str):
    """Retrieve full finding detail by ID."""
    store = get_store()
    f = store.get_finding(finding_id)
    if not f:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found")
    return f
