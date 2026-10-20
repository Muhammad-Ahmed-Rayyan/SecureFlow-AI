# backend/app/api/routes_metrics.py
# Metrics API: headline summary, backlog breakdown, MTTR benchmarks, and remediation funnel.

from __future__ import annotations

import statistics
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.main import get_store
from app.models import RemediationStatus, RunStatus, SeverityEnum, TierEnum

router = APIRouter(prefix="/metrics", tags=["metrics"])


class BacklogMetric(BaseModel):
    total_findings: int = 0
    open: int = 0
    critical_high: int = 0
    older_than_90d: int = 0
    estimated_hours: float = 0.0


class BaselineMetric(BaseModel):
    effort_hours_mean: float = 0.0
    effort_hours_n: int = 0
    exposure_days_mean: float = 0.0


class PipelineMetric(BaseModel):
    runs_total: int = 0
    runs_failed: int = 0
    escalated: int = 0
    prs_open: int = 0
    prs_merged: int = 0
    prs_closed: int = 0


class MTTRMetric(BaseModel):
    time_to_draft_pr_s_mean: Optional[float] = None
    time_to_merge_s_mean: Optional[float] = None
    reduction_pct: Optional[float] = None


class AcceptanceMetric(BaseModel):
    merged: int = 0
    closed_unmerged: int = 0
    open: int = 0
    n_decided: int = 0
    rate: Optional[float] = None


class TokensMetric(BaseModel):
    mean_per_run: Optional[float] = None


class MetricsSummaryResponse(BaseModel):
    backlog: BacklogMetric
    baseline: BaselineMetric
    pipeline: PipelineMetric
    mttr: MTTRMetric
    acceptance: AcceptanceMetric
    hours_saved: float = 0.0
    tokens: TokensMetric


@router.get("/summary", response_model=MetricsSummaryResponse)
def get_metrics_summary():
    """Headline metrics matching TAD section 8.1 data contract."""
    store = get_store()
    all_findings = store.list_findings({"page": 1, "page_size": 999_999})
    all_runs = store.list_runs()

    # 1. Backlog calculations
    total_findings = len(all_findings)
    backlog_findings = [f for f in all_findings if f.in_backlog]
    open_count = len(backlog_findings)
    crit_high = sum(
        1 for f in backlog_findings if f.severity in (SeverityEnum.CRITICAL, SeverityEnum.HIGH)
    )
    older_90 = sum(1 for f in backlog_findings if f.days_open > 90)
    estimated_hours = sum(f.baseline_hours_effective for f in backlog_findings)

    # 2. Baseline stats from historical data
    non_null_hours = [f.baseline_hours for f in all_findings if f.baseline_hours is not None]
    effort_mean = (
        round(statistics.mean(non_null_hours), 2) if non_null_hours else 6.82
    )

    resolved_findings = [
        f for f in all_findings if f.status_source in ("Fixed", "Verified")
    ]
    resolved_days = [f.days_open for f in resolved_findings]
    exposure_mean = (
        round(statistics.mean(resolved_days), 1) if resolved_days else 90.4
    )

    # 3. Live pipeline stats from runs
    runs_total = len(all_runs)
    runs_failed = sum(1 for r in all_runs if r.status == RunStatus.FAILED)
    escalated = sum(1 for r in all_runs if r.status == RunStatus.ESCALATED)
    prs_open = sum(1 for r in all_runs if r.status == RunStatus.PR_OPEN and (not r.pr or r.pr.state == "open"))
    prs_merged = sum(1 for r in all_runs if r.pr and r.pr.state == "merged")
    prs_closed = sum(1 for r in all_runs if r.pr and r.pr.state == "closed")

    # 4. MTTR and hours saved
    draft_times: list[float] = []
    merge_times: list[float] = []
    hours_saved = sum(
        f.baseline_hours_effective for f in all_findings if f.remediation_status == RemediationStatus.MERGED
    )

    for r in all_runs:
        if r.pr and r.pr.created_at and r.started_at:
            delta = (r.pr.created_at - r.started_at).total_seconds()
            if delta > 0:
                draft_times.append(delta)
        if r.pr and r.pr.merged_at and r.pr.created_at:
            delta = (r.pr.merged_at - r.pr.created_at).total_seconds()
            if delta > 0:
                merge_times.append(delta)

    time_draft_mean = round(statistics.mean(draft_times), 1) if draft_times else None
    time_merge_mean = round(statistics.mean(merge_times), 1) if merge_times else None

    reduction_pct: float | None = None
    if time_draft_mean and effort_mean > 0:
        reduction_pct = round(1.0 - (time_draft_mean / (effort_mean * 3600.0)), 4)

    # 5. Acceptance rate (only from real decided PRs, n_decided > 0)
    n_decided = prs_merged + prs_closed
    acc_rate = round(prs_merged / n_decided, 4) if n_decided > 0 else None

    # 6. Tokens
    token_counts = [
        (r.usage.prompt_tokens + r.usage.completion_tokens)
        for r in all_runs
        if r.usage and (r.usage.prompt_tokens or r.usage.completion_tokens)
    ]
    mean_tokens = round(statistics.mean(token_counts), 1) if token_counts else None

    return MetricsSummaryResponse(
        backlog=BacklogMetric(
            total_findings=total_findings,
            open=open_count,
            critical_high=crit_high,
            older_than_90d=older_90,
            estimated_hours=round(estimated_hours, 2),
        ),
        baseline=BaselineMetric(
            effort_hours_mean=effort_mean,
            effort_hours_n=len(non_null_hours),
            exposure_days_mean=exposure_mean,
        ),
        pipeline=PipelineMetric(
            runs_total=runs_total,
            runs_failed=runs_failed,
            escalated=escalated,
            prs_open=prs_open,
            prs_merged=prs_merged,
            prs_closed=prs_closed,
        ),
        mttr=MTTRMetric(
            time_to_draft_pr_s_mean=time_draft_mean,
            time_to_merge_s_mean=time_merge_mean,
            reduction_pct=reduction_pct,
        ),
        acceptance=AcceptanceMetric(
            merged=prs_merged,
            closed_unmerged=prs_closed,
            open=prs_open,
            n_decided=n_decided,
            rate=acc_rate,
        ),
        hours_saved=round(hours_saved, 2),
        tokens=TokensMetric(mean_per_run=mean_tokens),
    )


@router.get("/backlog")
def get_backlog_breakdown():
    """Detailed breakdown of backlog by severity, language, and age buckets."""
    store = get_store()
    all_findings = store.list_findings({"page": 1, "page_size": 999_999})
    backlog = [f for f in all_findings if f.in_backlog]

    by_severity: dict[str, dict[str, Any]] = {}
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        matched = [f for f in backlog if f.severity.value == sev]
        by_severity[sev] = {
            "count": len(matched),
            "estimated_hours": round(sum(f.baseline_hours_effective for f in matched), 1),
        }

    by_language: dict[str, int] = {}
    for f in backlog:
        lang = f.language_detected
        by_language[lang] = by_language.get(lang, 0) + 1

    # Age buckets: <30d, 30-90d, >90d
    age_buckets = {
        "less_than_30d": sum(1 for f in backlog if f.days_open < 30),
        "30d_to_90d": sum(1 for f in backlog if 30 <= f.days_open <= 90),
        "greater_than_90d": sum(1 for f in backlog if f.days_open > 90),
    }

    by_tier: dict[str, int] = {}
    for f in backlog:
        t = f.tier.value
        by_tier[t] = by_tier.get(t, 0) + 1

    return {
        "total_backlog": len(backlog),
        "by_severity": by_severity,
        "by_language": by_language,
        "by_age_bucket": age_buckets,
        "by_tier": by_tier,
    }


@router.get("/funnel")
def get_funnel_metrics():
    """Remediation funnel from raw backlog to merged pull requests."""
    store = get_store()
    all_findings = store.list_findings({"page": 1, "page_size": 999_999})
    backlog = [f for f in all_findings if f.in_backlog]

    autofix_types = {
        "SQL Injection", "Path Traversal", "Hardcoded Secret", "Open Redirect",
        "XSS", "Insecure Deserialization", "Insecure TLS", "Command Injection",
    }

    step_backlog = len(backlog)
    step_autofix_types = sum(1 for f in backlog if f.vuln_type in autofix_types)
    step_supported_lang = sum(1 for f in backlog if f.vuln_type in autofix_types and f.language_detected == "py")
    step_fix_ready = sum(1 for f in backlog if f.fix_ready)

    all_runs = store.list_runs()
    step_prs_open = sum(1 for r in all_runs if r.status == RunStatus.PR_OPEN)
    step_merged = sum(1 for r in all_runs if r.pr and r.pr.state == "merged")

    return {
        "funnel": [
            {"step": "Total Backlog", "count": step_backlog},
            {"step": "Auto-Fix Types", "count": step_autofix_types},
            {"step": "Supported Language (Python)", "count": step_supported_lang},
            {"step": "Fix Ready (Demo Target Match)", "count": step_fix_ready},
            {"step": "Draft PRs Opened", "count": step_prs_open},
            {"step": "PRs Merged", "count": step_merged},
        ]
    }
