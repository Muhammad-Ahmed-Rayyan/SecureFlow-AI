# backend/app/ingest/csv_parser.py
# Standard library CSV parser for scanner findings.
# Matches ps09_vulnerability_scans.csv column structure exactly.

from __future__ import annotations

import csv
import io
from typing import Any


def parse_csv_content(content: str) -> list[dict[str, Any]]:
    """Parse raw CSV text into a list of normalized row dictionaries.

    Expected columns:
    vuln_id,scan_tool,repository,language,severity,cve_id,vulnerability_type,
    affected_file,affected_line,description,suggested_fix_available,
    current_status,days_open,developer_assigned,fix_time_hours
    """
    f = io.StringIO(content.strip())
    reader = csv.DictReader(f)
    rows: list[dict[str, Any]] = []

    for r in reader:
        # Strip all keys and values
        clean: dict[str, Any] = {k.strip(): v.strip() for k, v in r.items() if k}

        # Parse boolean
        sugg_raw = clean.get("suggested_fix_available", "").lower()
        sugg = sugg_raw in ("true", "1", "yes", "t")

        # Parse line number
        try:
            line_reported = int(clean.get("affected_line", "0") or "0")
        except ValueError:
            line_reported = 0

        # Parse days_open
        try:
            days_open = int(clean.get("days_open", "0") or "0")
        except ValueError:
            days_open = 0

        # Parse fix_time_hours (can be empty/null)
        fix_time_raw = clean.get("fix_time_hours", "")
        baseline_hours: float | None = None
        if fix_time_raw:
            try:
                baseline_hours = float(fix_time_raw)
            except ValueError:
                baseline_hours = None

        rows.append({
            "id": clean.get("vuln_id", "").strip(),
            "source": "csv",
            "scan_tool": clean.get("scan_tool", "").strip(),
            "repository": clean.get("repository", "").strip(),
            "language_reported": clean.get("language", "").strip(),
            "severity": clean.get("severity", "").strip().upper(),
            "cve_id": clean.get("cve_id", "").strip(),
            "vuln_type": clean.get("vulnerability_type", "").strip(),
            "file_path": clean.get("affected_file", "").strip(),
            "line_reported": line_reported,
            "description": clean.get("description", "").strip(),
            "suggested_fix_available": sugg,
            "status_source": clean.get("current_status", "Open").strip(),
            "days_open": days_open,
            "developer": clean.get("developer_assigned", "").strip(),
            "baseline_hours": baseline_hours,
        })

    return rows
