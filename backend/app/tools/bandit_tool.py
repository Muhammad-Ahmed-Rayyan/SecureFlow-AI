# backend/app/tools/bandit_tool.py
# Bandit security linter integration. Runs inside sandboxed environment.
# Parses rule IDs, severities, and generates SARIF reports for repo scans.

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.tools.sandbox import run_cmd


def run_bandit_on_file(file_path: str, cwd: str | Path) -> tuple[list[str], list[str]]:
    """Run bandit on a single file inside cwd.

    Returns:
        tuple of (rule_ids: list[str], severities: list[str])
    """
    cmd = [sys.executable, "-m", "bandit", "-f", "json", "-q", str(file_path)]
    code, stdout, stderr = run_cmd(cmd, cwd=cwd, timeout=30)

    rule_ids: list[str] = []
    severities: list[str] = []

    if not stdout.strip():
        return rule_ids, severities

    try:
        data = json.loads(stdout)
        results = data.get("results", [])
        for r in results:
            test_id = r.get("test_id")
            sev = r.get("issue_severity", "MEDIUM")
            if test_id:
                rule_ids.append(test_id)
                severities.append(sev)
    except json.JSONDecodeError:
        pass

    return rule_ids, severities


def run_bandit_sarif(directory: str | Path) -> str:
    """Run bandit recursively on a directory and return raw SARIF report text."""
    cmd = [sys.executable, "-m", "bandit", "-r", ".", "-f", "sarif", "-q"]
    code, stdout, stderr = run_cmd(cmd, cwd=directory, timeout=60)
    return stdout if stdout.strip() else "{}"
