# backend/app/services/scan.py
# Scans the target repository using Bandit in a scrubbed sandbox,
# parses the generated SARIF report, normalizes and triages findings into the store.

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings
from app.ingest.normalizer import normalize_findings
from app.ingest.sarif_parser import parse_sarif_content
from app.store import get_store
from app.tools.sandbox import repo_sandbox

logger = logging.getLogger("secureflow.services.scan")


def scan_target_repository(
    repository: str | None = None,
    ref: str | None = None,
) -> dict[str, Any]:
    """Download repo zipball, execute bandit SARIF scan in sandbox, and ingest findings."""
    target_repo = repository or settings.target_repo
    target_branch = ref or settings.target_base_branch
    store = get_store()

    try:
        with repo_sandbox(target_repo, target_branch) as box:
            # Run bandit outputting SARIF format
            cmd = ["bandit", "-r", ".", "-f", "sarif", "-o", "bandit.sarif", "-q"]
            res = box.run_command(cmd, timeout_s=60)
            logger.info("Bandit scan exited with code %s", res.returncode)

            sarif_file = box.workdir / "bandit.sarif"
            if not sarif_file.exists():
                # If file not written, check if stdout contains SARIF JSON
                sarif_text = res.stdout.strip()
                if not sarif_text or not sarif_text.startswith("{"):
                    return {
                        "status": "completed",
                        "repository": target_repo,
                        "findings_found": 0,
                        "findings": [],
                        "message": "No issues detected or no python source files found.",
                    }
            else:
                sarif_text = sarif_file.read_text(encoding="utf-8")

            raw_rows = parse_sarif_content(sarif_text, id_prefix="BANDIT-")
            for r in raw_rows:
                r["repository"] = target_repo

            findings = normalize_findings(raw_rows)
            for f in findings:
                store.save_finding(f)

            return {
                "status": "completed",
                "repository": target_repo,
                "findings_found": len(findings),
                "findings": [f.id for f in findings],
                "message": f"Successfully ingested {len(findings)} findings from live repo scan.",
            }

    except Exception as exc:
        logger.error("Repository scan failed for %s: %s", target_repo, exc)
        return {
            "status": "error",
            "repository": target_repo,
            "findings_found": 0,
            "findings": [],
            "error": str(exc),
        }
