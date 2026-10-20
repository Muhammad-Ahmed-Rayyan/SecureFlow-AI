# backend/tests/test_ingest_golden.py
# Tests asserting every single golden number from Context.md section 10 and TAD section 5.6.

from pathlib import Path
import statistics
import pytest

from app.ingest.csv_parser import parse_csv_content
from app.ingest.normalizer import normalize_findings
from app.models import RemediationStatus, SeverityEnum, TierEnum


@pytest.fixture(scope="module")
def golden_dataset():
    """Load and normalize the official ps09_vulnerability_scans.csv dataset."""
    csv_path = Path(__file__).resolve().parent.parent / "data" / "ps09_vulnerability_scans.csv"
    assert csv_path.exists(), f"Golden CSV dataset missing at {csv_path}"
    content = csv_path.read_text(encoding="utf-8")
    raw_rows = parse_csv_content(content)
    findings = normalize_findings(raw_rows)
    return findings


def test_golden_total_rows(golden_dataset):
    """Exactly 200 findings in the dataset."""
    assert len(golden_dataset) == 200


def test_golden_data_quality_flags(golden_dataset):
    """Golden data quality counts: 161 LANG_MISMATCH, 54 MISSING_FIX_TIME."""
    lang_mismatches = sum(1 for f in golden_dataset if "LANG_MISMATCH" in f.dq_flags)
    missing_fix_times = sum(1 for f in golden_dataset if "MISSING_FIX_TIME" in f.dq_flags)

    assert lang_mismatches == 161
    assert missing_fix_times == 54


def test_golden_baseline_fix_hours(golden_dataset):
    """Baseline mean fix hours for non-null rows is 6.82 over n=146."""
    non_null_hours = [f.baseline_hours for f in golden_dataset if f.baseline_hours is not None]
    assert len(non_null_hours) == 146
    mean_hours = statistics.mean(non_null_hours)
    assert round(mean_hours, 2) == 6.82


def test_golden_backlog_counts_and_severities(golden_dataset):
    """Backlog (Open + In Progress) is 96 findings: 12 Critical, 27 High, 46 Medium, 11 Low."""
    backlog = [f for f in golden_dataset if f.in_backlog]
    assert len(backlog) == 96

    crit = sum(1 for f in backlog if f.severity == SeverityEnum.CRITICAL)
    high = sum(1 for f in backlog if f.severity == SeverityEnum.HIGH)
    med = sum(1 for f in backlog if f.severity == SeverityEnum.MEDIUM)
    low = sum(1 for f in backlog if f.severity == SeverityEnum.LOW)

    assert crit == 12
    assert high == 27
    assert med == 46
    assert low == 11


def test_golden_backlog_older_than_90_days(golden_dataset):
    """42 findings in backlog have days_open > 90."""
    backlog = [f for f in golden_dataset if f.in_backlog]
    older_90 = sum(1 for f in backlog if f.days_open > 90)
    assert older_90 == 42


def test_golden_backlog_effort_imputation(golden_dataset):
    """Backlog effort with median imputation is ≈ 653.95 hours."""
    backlog = [f for f in golden_dataset if f.in_backlog]
    total_effort = sum(f.baseline_hours_effective for f in backlog)
    assert round(total_effort, 1) == 654.0 or round(total_effort, 2) == 653.95


def test_golden_backlog_by_detected_language(golden_dataset):
    """Backlog by detected language: py 26, js 27, ts 22, java 21."""
    backlog = [f for f in golden_dataset if f.in_backlog]
    py_count = sum(1 for f in backlog if f.language_detected == "py")
    js_count = sum(1 for f in backlog if f.language_detected == "js")
    ts_count = sum(1 for f in backlog if f.language_detected == "ts")
    java_count = sum(1 for f in backlog if f.language_detected == "java")

    assert py_count == 26
    assert js_count == 27
    assert ts_count == 22
    assert java_count == 21


def test_golden_backlog_autofix_types(golden_dataset):
    """Backlog auto-fix types across any language is 70."""
    backlog = [f for f in golden_dataset if f.in_backlog]
    autofix_types = {
        "SQL Injection", "Path Traversal", "Hardcoded Secret", "Open Redirect",
        "XSS", "Insecure Deserialization", "Insecure TLS", "Command Injection",
    }
    autofix_count = sum(1 for f in backlog if f.vuln_type in autofix_types)
    assert autofix_count == 70


def test_golden_backlog_python_tiers(golden_dataset):
    """Python backlog breakdown: 21 AUTO_FIX, 3 DEPENDENCY, 2 ESCALATE."""
    py_backlog = [f for f in golden_dataset if f.in_backlog and f.language_detected == "py"]
    assert len(py_backlog) == 26

    autofix = sum(1 for f in py_backlog if f.tier == TierEnum.AUTO_FIX)
    dep = sum(1 for f in py_backlog if f.tier == TierEnum.DEPENDENCY)
    esc = sum(1 for f in py_backlog if f.tier == TierEnum.ESCALATE)

    assert autofix == 21
    assert dep == 3
    assert esc == 2


def test_golden_resolved_exposure_days(golden_dataset):
    """Fixed + Verified mean days_open is ≈ 90.4."""
    resolved = [f for f in golden_dataset if f.status_source in ("Fixed", "Verified")]
    assert len(resolved) == 104  # 200 - 96
    mean_days = statistics.mean(f.days_open for f in resolved)
    assert round(mean_days, 1) == 90.4


def test_golden_demo_fix_ready_findings(golden_dataset):
    """8 demo fix-ready findings: VULN-0169, 0145, 0028, 0110, 0198, 0139, 0106, 0023."""
    expected_demo_ids = {
        "VULN-0169", "VULN-0145", "VULN-0028", "VULN-0110",
        "VULN-0198", "VULN-0139", "VULN-0106", "VULN-0023",
    }
    fix_ready = {f.id for f in golden_dataset if f.fix_ready}
    assert fix_ready == expected_demo_ids


def test_golden_escalation_demos(golden_dataset):
    """Escalation findings: VULN-0174 (Buffer Overflow) and VULN-0108 (CSRF) must be ESCALATE."""
    by_id = {f.id: f for f in golden_dataset}
    assert by_id["VULN-0174"].tier == TierEnum.ESCALATE
    assert by_id["VULN-0174"].vuln_type == "Buffer Overflow"
    assert by_id["VULN-0108"].tier == TierEnum.ESCALATE
    assert by_id["VULN-0108"].vuln_type == "CSRF"
