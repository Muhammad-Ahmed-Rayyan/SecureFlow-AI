# backend/app/ingest/json_parser.py
# JSON parser accepting bare arrays or {"findings": [...]} with alias support.

from __future__ import annotations

import json
from typing import Any


def parse_json_content(content: str | list[Any] | dict[str, Any]) -> list[dict[str, Any]]:
    """Parse JSON payload into raw finding dictionaries.

    Supports either a bare array [ {...}, {...} ] or an object { "findings": [ ... ] }.
    Maps common field aliases to normalized keys.
    """
    if isinstance(content, str):
        data = json.loads(content)
    else:
        data = content

    if isinstance(data, dict):
        raw_list = data.get("findings", [])
    elif isinstance(data, list):
        raw_list = data
    else:
        raise ValueError("Invalid JSON format: expected list or object with 'findings' key")

    findings: list[dict[str, Any]] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue

        # Map common field aliases
        vuln_id = item.get("id") or item.get("vuln_id") or ""
        file_path = item.get("file_path") or item.get("affected_file") or ""
        vuln_type = item.get("vuln_type") or item.get("vulnerability_type") or "Other"
        line_reported = item.get("line_reported") or item.get("affected_line") or 0
        developer = item.get("developer") or item.get("developer_assigned") or ""
        baseline_hours = item.get("baseline_hours") or item.get("fix_time_hours")
        status_source = item.get("status_source") or item.get("current_status") or "Open"
        suggested = item.get("suggested_fix_available", False)

        try:
            line_int = int(line_reported)
        except (ValueError, TypeError):
            line_int = 0

        try:
            days_open_int = int(item.get("days_open", 0))
        except (ValueError, TypeError):
            days_open_int = 0

        bh_float: float | None = None
        if baseline_hours is not None and baseline_hours != "":
            try:
                bh_float = float(baseline_hours)
            except (ValueError, TypeError):
                bh_float = None

        findings.append({
            "id": str(vuln_id),
            "source": item.get("source", "json"),
            "scan_tool": item.get("scan_tool", "Custom"),
            "repository": item.get("repository", "secureflow-demo-target"),
            "language_reported": item.get("language_reported") or item.get("language") or "",
            "severity": str(item.get("severity", "MEDIUM")).upper(),
            "cve_id": item.get("cve_id", ""),
            "vuln_type": vuln_type,
            "file_path": file_path,
            "line_reported": line_int,
            "description": item.get("description", ""),
            "suggested_fix_available": bool(suggested),
            "status_source": status_source,
            "days_open": days_open_int,
            "developer": developer,
            "baseline_hours": bh_float,
        })

    return findings
