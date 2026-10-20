# backend/app/triage/priority.py
# Priority scoring algorithm for sorting and prioritizing findings.
# Implements multi-factor weighting: severity, age, fix availability, and auto-fix tier.

from __future__ import annotations

from app.models import SeverityEnum, TierEnum

SEVERITY_WEIGHTS: dict[SeverityEnum | str, float] = {
    SeverityEnum.CRITICAL: 100.0,
    "CRITICAL": 100.0,
    SeverityEnum.HIGH: 75.0,
    "HIGH": 75.0,
    SeverityEnum.MEDIUM: 50.0,
    "MEDIUM": 50.0,
    SeverityEnum.LOW: 25.0,
    "LOW": 25.0,
}


def calculate_priority_score(
    severity: SeverityEnum | str,
    days_open: int,
    suggested_fix_available: bool = False,
    tier: TierEnum | str = TierEnum.UNSUPPORTED_LANG,
    source_available: bool = False,
) -> float:
    """Calculate a priority score between 0.0 and 100.0.

    Weights:
    - Severity: 40% (CRITICAL=100, HIGH=75, MEDIUM=50, LOW=25)
    - Days open: 25% (normalized up to 180 days)
    - Suggested fix available: 15% (100 if true else 0)
    - Auto-fix tier: 20% (100 if tier == AUTO_FIX else 0)
    """
    # 1. Severity component (0..100) * 0.40
    sev_key = severity if isinstance(severity, SeverityEnum) else str(severity).upper()
    sev_base = SEVERITY_WEIGHTS.get(sev_key, 25.0)
    sev_component = sev_base * 0.40

    # 2. Days open component (0..100) * 0.25
    days_norm = min(max(days_open, 0) / 180.0, 1.0) * 100.0
    age_component = days_norm * 0.25

    # 3. Suggested fix component (0 or 100) * 0.15
    sugg_component = (100.0 if suggested_fix_available else 0.0) * 0.15

    # 4. Auto-fix tier component (0 or 100) * 0.20
    is_auto = tier == TierEnum.AUTO_FIX or tier == "AUTO_FIX"
    tier_component = (100.0 if is_auto else 0.0) * 0.20

    score = sev_component + age_component + sugg_component + tier_component
    return round(score, 2)
