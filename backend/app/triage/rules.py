# backend/app/triage/rules.py
# Deterministic tiering and CWE mapping rules for security findings.
# Implements TAD section 5.4 order of evaluation and rationale generation.

from __future__ import annotations

from app.models import TierEnum

# Canonical CWE mapping per TAD section 5.4
CWE_MAP: dict[str, str] = {
    "SQL Injection": "CWE-89",
    "Hardcoded Secret": "CWE-798",
    "Path Traversal": "CWE-22",
    "Insecure Deserialization": "CWE-502",
    "Open Redirect": "CWE-601",
    "XSS": "CWE-79",
    "Insecure TLS": "CWE-295",
    "CSRF": "CWE-352",
    "Buffer Overflow": "CWE-120",
    "Outdated Dependency": "CWE-1104",
    "Dependency Vulnerability": "CWE-1104",
    "Command Injection": "CWE-78",
}


def get_cwe_for_vuln_type(vuln_type: str) -> str:
    """Return canonical CWE identifier for a given vulnerability type."""
    return CWE_MAP.get(vuln_type.strip(), "CWE-Other")


def evaluate_tier(
    vuln_type: str,
    language_detected: str,
    supported_languages: set[str] | list[str] | None = None,
) -> tuple[TierEnum, str, str]:
    """Evaluate tier, rationale, and CWE according to TAD section 5.4.

    Order of evaluation:
    1. Buffer Overflow, CSRF -> ESCALATE
    2. Outdated Dependency / Dependency Vulnerability -> DEPENDENCY
    3. language not in supported_languages (default 'py') -> UNSUPPORTED_LANG
    4. otherwise -> AUTO_FIX

    Returns:
        tuple of (TierEnum, tier_reason: str, cwe: str)
    """
    if supported_languages is None:
        supported_languages = {"py"}
    else:
        supported_languages = set(supported_languages)

    v_clean = vuln_type.strip()
    cwe = get_cwe_for_vuln_type(v_clean)

    # 1. Architectural & false positive risk -> ESCALATE
    if v_clean in ("Buffer Overflow", "CSRF"):
        if v_clean == "Buffer Overflow":
            reason = "Buffer Overflow in memory-safe language indicates false positive or binary extension requiring manual review"
        else:
            reason = "CSRF protection requires framework-level architectural changes, not single-file patch"
        return TierEnum.ESCALATE, reason, cwe

    # 2. Dependency issues -> DEPENDENCY
    if v_clean in ("Outdated Dependency", "Dependency Vulnerability"):
        return (
            TierEnum.DEPENDENCY,
            "Requires package dependency upgrade, not safe source code modification",
            cwe,
        )

    # 3. Language adapter check -> UNSUPPORTED_LANG
    if language_detected.lower() not in supported_languages:
        return (
            TierEnum.UNSUPPORTED_LANG,
            f"Adapter not enabled for language '{language_detected}' (only Python auto-fix enabled in MVP)",
            cwe,
        )

    # 4. Standard auto-fixable finding
    return (
        TierEnum.AUTO_FIX,
        f"Valid vulnerability pattern ({v_clean}) with auto-remediation capability",
        cwe,
    )
