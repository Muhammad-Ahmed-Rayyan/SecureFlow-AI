# backend/tests/test_triage.py
# Unit tests for triage tiering rules, CWE mappings, and priority scoring.

import pytest

from app.models import SeverityEnum, TierEnum
from app.triage.priority import calculate_priority_score
from app.triage.rules import evaluate_tier, get_cwe_for_vuln_type


def test_cwe_mappings():
    """Verify standard CWE identifiers for vulnerability types."""
    assert get_cwe_for_vuln_type("SQL Injection") == "CWE-89"
    assert get_cwe_for_vuln_type("Hardcoded Secret") == "CWE-798"
    assert get_cwe_for_vuln_type("Path Traversal") == "CWE-22"
    assert get_cwe_for_vuln_type("Insecure Deserialization") == "CWE-502"
    assert get_cwe_for_vuln_type("Open Redirect") == "CWE-601"
    assert get_cwe_for_vuln_type("XSS") == "CWE-79"
    assert get_cwe_for_vuln_type("Insecure TLS") == "CWE-295"
    assert get_cwe_for_vuln_type("CSRF") == "CWE-352"
    assert get_cwe_for_vuln_type("Buffer Overflow") == "CWE-120"
    assert get_cwe_for_vuln_type("Outdated Dependency") == "CWE-1104"
    assert get_cwe_for_vuln_type("Unknown Novel Issue") == "CWE-Other"


def test_tier_escalate_buffer_overflow_and_csrf():
    """Buffer Overflow and CSRF must always escalate regardless of language."""
    tier1, reason1, _ = evaluate_tier("Buffer Overflow", "py")
    assert tier1 == TierEnum.ESCALATE
    assert "Buffer Overflow" in reason1

    tier2, reason2, _ = evaluate_tier("CSRF", "py")
    assert tier2 == TierEnum.ESCALATE
    assert "CSRF" in reason2


def test_tier_dependency():
    """Dependency issues must be marked DEPENDENCY."""
    tier, reason, _ = evaluate_tier("Outdated Dependency", "py")
    assert tier == TierEnum.DEPENDENCY
    assert "upgrade" in reason.lower()


def test_tier_unsupported_language():
    """Non-Python languages are marked UNSUPPORTED_LANG in MVP."""
    tier_js, _, _ = evaluate_tier("SQL Injection", "js")
    assert tier_js == TierEnum.UNSUPPORTED_LANG

    tier_ts, _, _ = evaluate_tier("XSS", "ts")
    assert tier_ts == TierEnum.UNSUPPORTED_LANG

    tier_java, _, _ = evaluate_tier("Path Traversal", "java")
    assert tier_java == TierEnum.UNSUPPORTED_LANG


def test_tier_autofix_python():
    """Auto-fixable types in Python receive TierEnum.AUTO_FIX."""
    for vt in ("SQL Injection", "Hardcoded Secret", "Path Traversal", "Open Redirect", "XSS"):
        tier, _, cwe = evaluate_tier(vt, "py")
        assert tier == TierEnum.AUTO_FIX
        assert cwe.startswith("CWE-")


def test_priority_score_monotonicity():
    """Higher severity and older findings must receive higher priority scores."""
    score_crit = calculate_priority_score(SeverityEnum.CRITICAL, days_open=100)
    score_high = calculate_priority_score(SeverityEnum.HIGH, days_open=100)
    score_med = calculate_priority_score(SeverityEnum.MEDIUM, days_open=100)
    score_low = calculate_priority_score(SeverityEnum.LOW, days_open=100)

    assert score_crit > score_high > score_med > score_low

    score_older = calculate_priority_score(SeverityEnum.HIGH, days_open=180)
    score_newer = calculate_priority_score(SeverityEnum.HIGH, days_open=10)
    assert score_older > score_newer

    score_autofix = calculate_priority_score(SeverityEnum.HIGH, days_open=50, tier=TierEnum.AUTO_FIX)
    score_unsupp = calculate_priority_score(SeverityEnum.HIGH, days_open=50, tier=TierEnum.UNSUPPORTED_LANG)
    assert score_autofix > score_unsupp
