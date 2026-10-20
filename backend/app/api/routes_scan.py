# backend/app/api/routes_scan.py
# Endpoints for live repository security scanning and GitHub PR state synchronization.

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.pr_sync import sync_prs
from app.services.scan import scan_target_repository

router = APIRouter(tags=["scan_and_sync"])


class ScanRepoRequest(BaseModel):
    repository: Optional[str] = None
    ref: Optional[str] = None


@router.post("/scan/repo")
def scan_repository_endpoint(req: ScanRepoRequest | None = None) -> dict[str, Any]:
    """Trigger an autonomous Bandit security scan on the target repository."""
    repo = req.repository if req else None
    ref = req.ref if req else None
    return scan_target_repository(repo, ref)


@router.post("/prs/sync")
def sync_pull_requests_endpoint() -> dict[str, Any]:
    """Force a live synchronization of GitHub pull request statuses."""
    res = sync_prs(force=True)
    return {"status": "ok", **res}
