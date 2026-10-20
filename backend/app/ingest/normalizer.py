# backend/app/ingest/normalizer.py
# Normalization pipeline for security scanner findings.
# Implements language detection by extension, median imputation, tiering, and priority scoring.

from __future__ import annotations

import statistics
from typing import Any, Iterable, Sequence

from app.ingest.quality import compute_quality_flags
from app.models import Finding, RemediationStatus, SeverityEnum, SourceEnum
from app.triage.priority import calculate_priority_score
from app.triage.rules import evaluate_tier

EXTENSION_LANG_MAP: dict[str, str] = {
    "py": "py",
    "js": "js",
    "ts": "ts",
    "java": "java",
    "cs": "cs",
    "go": "go",
    "rb": "rb",
    "php": "php",
}

KNOWN_VULN_TYPES: set[str] = {
    "SQL Injection",
    "Command Injection",
    "Path Traversal",
    "Hardcoded Secret",
    "Open Redirect",
    "XSS",
    "Insecure Deserialization",
    "Insecure TLS",
    "CSRF",
    "Buffer Overflow",
    "Outdated Dependency",
    "Dependency Vulnerability",
}

# The 8 vulnerable files built in secureflow-demo-target (TAD section 16.3)
DEMO_TARGET_FILES: set[tuple[str, str]] = {
    ("notification-svc", "src/main/service/File2.py"),
    ("data-pipeline", "src/main/service/File4.py"),
    ("analytics-engine", "src/main/service/File16.py"),
    ("search-indexer", "src/main/service/File43.py"),
    ("admin-dashboard", "src/main/service/File47.py"),
    ("data-pipeline", "src/main/service/File20.py"),
    ("admin-dashboard", "src/main/service/File36.py"),
    ("payment-api", "src/main/service/File34.py"),
}

DEMO_FINDING_IDS: set[str] = {
    "VULN-0169",
    "VULN-0145",
    "VULN-0028",
    "VULN-0110",
    "VULN-0198",
    "VULN-0139",
    "VULN-0106",
    "VULN-0023",
}

DEFAULT_MEDIANS: dict[str, float] = {
    "CRITICAL": 6.0,
    "HIGH": 8.25,
    "MEDIUM": 6.95,
    "LOW": 7.15,
}


def detect_language_from_path(file_path: str) -> str:
    """Extract language identifier from file extension (extension is ground truth)."""
    clean = file_path.replace("\\", "/").strip()
    if "." not in clean:
        return "unknown"
    ext = clean.rsplit(".", 1)[-1].lower()
    return EXTENSION_LANG_MAP.get(ext, ext)


def normalize_severity(severity_raw: str) -> SeverityEnum:
    """Normalize raw severity text into canonical SeverityEnum."""
    s = (severity_raw or "MEDIUM").strip().upper()
    try:
        return SeverityEnum[s]
    except KeyError:
        return SeverityEnum.MEDIUM


def normalize_vuln_type(raw_type: str) -> str:
    """Map raw vulnerability string to one of the 10 known types or Other."""
    clean = raw_type.strip()
    for known in KNOWN_VULN_TYPES:
        if clean.lower() == known.lower():
            return known
    return "Other"


def compute_severity_medians(raw_rows: Iterable[dict[str, Any]]) -> dict[str, float]:
    """Compute per-severity median of fix_time_hours for non-null rows."""
    groups: dict[str, list[float]] = {}
    for r in raw_rows:
        ft = r.get("baseline_hours")
        if ft is not None and isinstance(ft, (int, float)) and ft > 0:
            sev = str(r.get("severity", "MEDIUM")).upper()
            groups.setdefault(sev, []).append(float(ft))

    medians = dict(DEFAULT_MEDIANS)
    for sev, vals in groups.items():
        if vals:
            medians[sev] = round(statistics.median(vals), 2)
    return medians


def normalize_findings(
    raw_rows: Sequence[dict[str, Any]],
    available_tree_paths: set[str] | None = None,
) -> list[Finding]:
    """Normalize a batch of raw finding dictionaries into canonical Finding models."""
    if not raw_rows:
        return []

    # 1. First pass: detect language for all rows to feed quality checker
    lang_detected_lookup: dict[str, str] = {}
    for r in raw_rows:
        fid = str(r.get("id", ""))
        fpath = str(r.get("file_path", ""))
        lang_detected_lookup[fid] = detect_language_from_path(fpath)

    # 2. Compute data-quality flags across the entire batch
    dq_flags_by_id = compute_quality_flags(list(raw_rows), lang_detected_lookup)

    # 3. Compute per-severity medians for baseline_hours_effective imputation
    medians = compute_severity_medians(raw_rows)

    # 4. Normalize and create Finding objects
    findings: list[Finding] = []
    for r in raw_rows:
        fid = str(r.get("id", ""))
        fpath = str(r.get("file_path", ""))
        repo = str(r.get("repository", "secureflow-demo-target"))
        det_lang = lang_detected_lookup.get(fid, detect_language_from_path(fpath))
        sev = normalize_severity(str(r.get("severity", "MEDIUM")))
        vtype = normalize_vuln_type(str(r.get("vuln_type", "Other")))

        # Source availability
        source_avail = False
        if available_tree_paths is not None:
            source_avail = f"{repo}/{fpath}" in available_tree_paths or fpath in available_tree_paths
        else:
            source_avail = (repo, fpath) in DEMO_TARGET_FILES or fid in DEMO_FINDING_IDS

        # Baseline hours and effective median imputation
        raw_hours = r.get("baseline_hours")
        baseline_hours: float | None = None
        if raw_hours is not None and raw_hours != "":
            try:
                baseline_hours = float(raw_hours)
            except (ValueError, TypeError):
                baseline_hours = None

        if baseline_hours is not None:
            effective_hours = baseline_hours
        else:
            effective_hours = medians.get(sev.value, 6.82)

        # Tier and CWE evaluation
        tier, tier_reason, cwe = evaluate_tier(vtype, det_lang)

        # Priority scoring
        days_open = int(r.get("days_open", 0) or 0)
        suggested = bool(r.get("suggested_fix_available", False))
        score = calculate_priority_score(
            severity=sev,
            days_open=days_open,
            suggested_fix_available=suggested,
            tier=tier,
            source_available=source_avail,
        )

        source_val = r.get("source", "csv")
        try:
            source_enum = SourceEnum(source_val)
        except ValueError:
            source_enum = SourceEnum.csv

        finding = Finding(
            id=fid,
            source=source_enum,
            scan_tool=str(r.get("scan_tool", "")),
            repository=repo,
            language_reported=str(r.get("language_reported", "")),
            language_detected=det_lang,
            severity=sev,
            cve_id=str(r.get("cve_id", "")),
            vuln_type=vtype,
            file_path=fpath,
            line_reported=int(r.get("line_reported", 0) or 0),
            description=str(r.get("description", "")),
            suggested_fix_available=suggested,
            status_source=str(r.get("status_source", "Open")),
            days_open=days_open,
            developer=str(r.get("developer", "")),
            baseline_hours=baseline_hours,
            baseline_hours_effective=effective_hours,
            dq_flags=dq_flags_by_id.get(fid, []),
            cwe=cwe,
            tier=tier,
            tier_reason=tier_reason,
            priority_score=score,
            source_available=source_avail,
            remediation_status=RemediationStatus.NEW,
            run_id=None,
        )
        findings.append(finding)

    return findings
