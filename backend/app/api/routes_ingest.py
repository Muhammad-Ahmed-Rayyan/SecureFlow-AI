# backend/app/api/routes_ingest.py
# Ingestion API endpoints for CSV, SARIF, JSON and bundled seed dataset.

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.ingest.csv_parser import parse_csv_content
from app.ingest.json_parser import parse_json_content
from app.ingest.normalizer import normalize_findings
from app.ingest.sarif_parser import parse_sarif_content
from app.main import get_store
from app.models import Finding

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestResponse(BaseModel):
    status: str = "ok"
    count: int
    source: str
    dq_flags_summary: dict[str, int]
    backlog_count: int


def _upsert_and_summarize(findings: list[Finding], source_name: str) -> dict[str, Any]:
    store = get_store()
    dq_counts: dict[str, int] = {}
    backlog = 0

    for f in findings:
        store.upsert_finding(f)
        if f.in_backlog:
            backlog += 1
        for flag in f.dq_flags:
            dq_counts[flag] = dq_counts.get(flag, 0) + 1

    return {
        "status": "ok",
        "count": len(findings),
        "source": source_name,
        "dq_flags_summary": dq_counts,
        "backlog_count": backlog,
    }


@router.post("/seed", response_model=IngestResponse)
def seed_dataset():
    """Load the bundled hackathon dataset (ps09_vulnerability_scans.csv).

    Parses, normalizes, applies quality flags, runs triage, and persists all findings.
    """
    # Locate data/ps09_vulnerability_scans.csv
    possible_paths = [
        Path("data/ps09_vulnerability_scans.csv"),
        Path("backend/data/ps09_vulnerability_scans.csv"),
        Path(__file__).resolve().parent.parent.parent / "data" / "ps09_vulnerability_scans.csv",
    ]

    target_path: Path | None = None
    for p in possible_paths:
        if p.is_file():
            target_path = p
            break

    if not target_path:
        raise HTTPException(
            status_code=404,
            detail="Bundled dataset ps09_vulnerability_scans.csv not found in data directory",
        )

    content = target_path.read_text(encoding="utf-8")
    raw_rows = parse_csv_content(content)
    findings = normalize_findings(raw_rows)
    return _upsert_and_summarize(findings, source_name="csv_seed")


@router.post("/csv", response_model=IngestResponse)
async def ingest_csv(file: UploadFile = File(...)):
    """Upload and ingest a CSV scanner findings export."""
    try:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8")
        raw_rows = parse_csv_content(content)
        findings = normalize_findings(raw_rows)
        return _upsert_and_summarize(findings, source_name="csv_upload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


@router.post("/sarif", response_model=IngestResponse)
async def ingest_sarif(payload: dict[str, Any] | None = None, file: UploadFile | None = None):
    """Ingest a SARIF 2.1.0 security report via JSON body or file upload."""
    try:
        if file is not None:
            raw_bytes = await file.read()
            raw_rows = parse_sarif_content(raw_bytes.decode("utf-8"))
        elif payload is not None:
            raw_rows = parse_sarif_content(payload)
        else:
            raise HTTPException(status_code=400, detail="Provide either a JSON body or SARIF file")

        findings = normalize_findings(raw_rows)
        return _upsert_and_summarize(findings, source_name="sarif")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse SARIF: {str(e)}")


@router.post("/json", response_model=IngestResponse)
def ingest_json(payload: list[dict[str, Any]] | dict[str, Any]):
    """Ingest JSON findings as an array or object with a findings key."""
    try:
        raw_rows = parse_json_content(payload)
        findings = normalize_findings(raw_rows)
        return _upsert_and_summarize(findings, source_name="json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse JSON: {str(e)}")


@router.post("", response_model=IngestResponse)
async def ingest_generic(
    file: UploadFile | None = None,
    format: str | None = Query(None, description="csv, sarif, or json"),
):
    """Generic multipart ingestion endpoint with format auto-detection."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    filename = (file.filename or "").lower()
    raw_bytes = await file.read()
    content = raw_bytes.decode("utf-8")

    fmt = (format or "").lower()
    if not fmt:
        if filename.endswith(".csv"):
            fmt = "csv"
        elif filename.endswith(".sarif") or filename.endswith(".sarif.json"):
            fmt = "sarif"
        elif filename.endswith(".json"):
            fmt = "json"
        else:
            fmt = "csv" if "," in content.splitlines()[0] else "json"

    if fmt == "csv":
        raw_rows = parse_csv_content(content)
    elif fmt == "sarif":
        raw_rows = parse_sarif_content(content)
    elif fmt == "json":
        raw_rows = parse_json_content(content)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    findings = normalize_findings(raw_rows)
    return _upsert_and_summarize(findings, source_name=fmt)
