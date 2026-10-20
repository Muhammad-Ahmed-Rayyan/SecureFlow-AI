# backend/app/ingest/quality.py
# Data-quality flagging engine.
# Detects inconsistencies, duplicate CVEs/files, and missing metrics in raw findings.

from __future__ import annotations

import re
from typing import Any

LANG_CODE_MAP: dict[str, str] = {
    "python": "py",
    "py": "py",
    "javascript": "js",
    "js": "js",
    "typescript": "ts",
    "ts": "ts",
    "java": "java",
    "c#": "cs",
    "csharp": "cs",
    "cs": "cs",
    "go": "go",
    "golang": "go",
    "ruby": "rb",
    "rb": "rb",
    "php": "php",
}

DESC_REGEX = re.compile(r"Sample vulnerability description for\s+(.*)", re.IGNORECASE)


def compute_quality_flags(
    findings: list[dict[str, Any]],
    lang_detected_lookup: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    """Compute data-quality flags for a collection of findings.

    Returns a dict mapping finding ID to its list of DQ flags:
    - LANG_MISMATCH: reported language differs from detected language
    - DESC_MISMATCH: phrase in description contradicts vulnerability_type
    - DUP_CVE: cve_id appears on multiple findings
    - DUP_FILE: same (repository, file_path) appears on multiple findings
    - MISSING_FIX_TIME: fix_time_hours is null or missing
    """
    # 1. Count CVE occurrences
    cve_counts: dict[str, int] = {}
    for f in findings:
        cve = (f.get("cve_id") or "").strip()
        if cve:
            cve_counts[cve] = cve_counts.get(cve, 0) + 1

    # 2. Count repository + file_path occurrences
    file_counts: dict[tuple[str, str], int] = {}
    for f in findings:
        repo = (f.get("repository") or "").strip()
        path = (f.get("file_path") or "").strip()
        if repo and path:
            pair = (repo, path)
            file_counts[pair] = file_counts.get(pair, 0) + 1

    # 3. Assess each finding
    flags_by_id: dict[str, list[str]] = {}

    for f in findings:
        fid = str(f.get("id", ""))
        flags: list[str] = []

        # LANG_MISMATCH
        rep_lang = (f.get("language_reported") or "").strip().lower()
        rep_norm = LANG_CODE_MAP.get(rep_lang, rep_lang)

        det_lang = ""
        if lang_detected_lookup and fid in lang_detected_lookup:
            det_lang = lang_detected_lookup[fid]
        else:
            # Fallback to extension of file_path
            path = f.get("file_path", "")
            ext = path.split(".")[-1].lower() if "." in path else ""
            det_lang = "py" if ext == "py" else ("js" if ext == "js" else ("ts" if ext == "ts" else ("java" if ext == "java" else ext)))

        if rep_norm and det_lang and rep_norm != det_lang:
            flags.append("LANG_MISMATCH")

        # DESC_MISMATCH
        desc = f.get("description", "")
        vuln_type = (f.get("vuln_type") or "").strip().lower()
        m = DESC_REGEX.search(desc)
        if m:
            phrase = m.group(1).strip().lower()
            if phrase != vuln_type:
                flags.append("DESC_MISMATCH")

        # DUP_CVE
        cve = (f.get("cve_id") or "").strip()
        if cve and cve_counts.get(cve, 0) > 1:
            flags.append("DUP_CVE")

        # DUP_FILE
        repo = (f.get("repository") or "").strip()
        path = (f.get("file_path") or "").strip()
        if repo and path and file_counts.get((repo, path), 0) > 1:
            flags.append("DUP_FILE")

        # MISSING_FIX_TIME
        bh = f.get("baseline_hours")
        if bh is None or bh == "":
            flags.append("MISSING_FIX_TIME")

        flags_by_id[fid] = flags

    return flags_by_id
