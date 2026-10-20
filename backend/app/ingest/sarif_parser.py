# backend/app/ingest/sarif_parser.py
# SARIF 2.1.0 parser for static security analysis reports (Bandit, Snyk, Semgrep, Trivy).
# Maps results to normalized raw finding dictionaries.

from __future__ import annotations

import json
from typing import Any


def _map_sarif_level(level: str | None) -> str:
    """Map SARIF level (error, warning, note) to SeverityEnum string."""
    lvl = (level or "").lower()
    if lvl == "error":
        return "HIGH"
    elif lvl == "warning":
        return "MEDIUM"
    elif lvl == "note":
        return "LOW"
    return "MEDIUM"


def parse_sarif_content(content: str | dict[str, Any], id_prefix: str = "SARIF-") -> list[dict[str, Any]]:
    """Parse SARIF 2.1.0 JSON text or dict into raw finding dictionaries.

    Derives repository from the first path segment if applicable, and assigns
    monotonic finding IDs prefixed with id_prefix (e.g. SARIF-0001).
    """
    if isinstance(content, str):
        data = json.loads(content)
    else:
        data = content

    runs = data.get("runs", [])
    findings: list[dict[str, Any]] = []
    counter = 1

    for run in runs:
        tool_driver = run.get("tool", {}).get("driver", {})
        tool_name = tool_driver.get("name", "SARIF")

        # Optional rule map for looking up descriptions or fallback severity
        rules_map: dict[str, dict[str, Any]] = {}
        for r in tool_driver.get("rules", []):
            rid = r.get("id")
            if rid:
                rules_map[rid] = r

        results = run.get("results", [])
        for res in results:
            rule_id = res.get("ruleId", "")
            rule_info = rules_map.get(rule_id, {})

            # Message
            msg = res.get("message", {}).get("text", "")
            if not msg and "shortDescription" in rule_info:
                msg = rule_info.get("shortDescription", {}).get("text", "")

            # Severity level
            level = res.get("level")
            if not level:
                level = rule_info.get("defaultConfiguration", {}).get("level", "warning")
            severity = _map_sarif_level(level)

            # Location
            locations = res.get("locations", [])
            uri = ""
            start_line = 0
            if locations:
                phys = locations[0].get("physicalLocation", {})
                uri = phys.get("artifactLocation", {}).get("uri", "")
                start_line = phys.get("region", {}).get("startLine", 0)

            # Clean uri and derive repository if present as first path segment
            clean_uri = uri.replace("\\", "/").lstrip("/")
            parts = clean_uri.split("/", 1)
            if len(parts) == 2 and any(clean_uri.startswith(r + "/") for r in (
                "admin-dashboard", "auth-service", "billing-svc", "data-pipeline",
                "identity-hub", "notification-svc", "order-processor", "user-portal"
            )):
                repository = parts[0]
                file_path = parts[1]
            else:
                repository = "secureflow-demo-target"
                file_path = clean_uri

            vuln_id = f"{id_prefix}{counter:04d}"
            counter += 1

            findings.append({
                "id": vuln_id,
                "source": "sarif",
                "scan_tool": tool_name,
                "repository": repository,
                "language_reported": "",
                "severity": severity,
                "cve_id": rule_id if rule_id.startswith("CVE-") else "",
                "vuln_type": rule_id,
                "file_path": file_path,
                "line_reported": start_line,
                "description": msg,
                "suggested_fix_available": False,
                "status_source": "Open",
                "days_open": 1,
                "developer": "unassigned",
                "baseline_hours": None,
            })

    return findings
