# models.py — all Pydantic models and enums for the SecureFlow AI project.
# These are the canonical data shapes used across the API, store and agents.

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, computed_field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceEnum(str, Enum):
    csv = "csv"
    sarif = "sarif"
    json = "json"


class SeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TierEnum(str, Enum):
    AUTO_FIX = "AUTO_FIX"
    DEPENDENCY = "DEPENDENCY"
    ESCALATE = "ESCALATE"
    UNSUPPORTED_LANG = "UNSUPPORTED_LANG"


class RemediationStatus(str, Enum):
    NEW = "NEW"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PR_OPEN = "PR_OPEN"
    MERGED = "MERGED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    FAILED = "FAILED"


# Backward-compatible and UI type aliases
FindingStatus = RemediationStatus
RemediationTier = TierEnum


class RunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PR_OPEN = "PR_OPEN"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"


class EventLevel(str, Enum):
    info = "info"
    warn = "warn"
    error = "error"
    success = "success"


class DQFlag(str, Enum):
    LANG_MISMATCH = "LANG_MISMATCH"
    DESC_MISMATCH = "DESC_MISMATCH"
    DUP_CVE = "DUP_CVE"
    DUP_FILE = "DUP_FILE"
    MISSING_FIX_TIME = "MISSING_FIX_TIME"


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    id: str
    source: SourceEnum = SourceEnum.csv
    scan_tool: str = ""
    repository: str = ""
    language_reported: str = ""
    language_detected: str = ""
    severity: SeverityEnum = SeverityEnum.LOW
    cve_id: str = ""
    vuln_type: str = ""
    file_path: str = ""
    line_reported: int = 0
    description: str = ""
    suggested_fix_available: bool = False
    status_source: str = "Open"          # raw CSV current_status
    days_open: int = 0
    developer: str = ""
    baseline_hours: Optional[float] = None
    baseline_hours_effective: float = 0.0
    dq_flags: list[str] = Field(default_factory=list)
    cwe: str = ""
    tier: TierEnum = TierEnum.UNSUPPORTED_LANG
    tier_reason: str = ""
    priority_score: float = 0.0
    source_available: bool = False
    remediation_status: RemediationStatus = RemediationStatus.NEW
    status: RemediationStatus = RemediationStatus.NEW
    is_fix_ready: bool = False
    run_id: Optional[str] = None

    @computed_field
    @property
    def in_backlog(self) -> bool:
        return (
            self.status_source in ("Open", "In Progress")
            and self.remediation_status != RemediationStatus.MERGED
        )

    @computed_field
    @property
    def fix_ready(self) -> bool:
        return (
            self.tier == TierEnum.AUTO_FIX
            and self.source_available
            and self.language_detected == "py"   # only Python supported in MVP
        )


# ---------------------------------------------------------------------------
# Run sub-objects
# ---------------------------------------------------------------------------

class PatchInfo(BaseModel):
    explanation: str = ""
    change_summary: str = ""
    confidence: float = 0.0
    risk: str = "medium"
    diff: str = ""
    new_content: str = ""


class ValidationCheck(BaseModel):
    functional: int = 0
    exploit: int = 0


class ValidationEvidence(BaseModel):
    policy: bool = False
    before: ValidationCheck = Field(default_factory=ValidationCheck)
    after: ValidationCheck = Field(default_factory=ValidationCheck)
    bandit_before_ids: list[str] = Field(default_factory=list)
    bandit_after_ids: list[str] = Field(default_factory=list)
    bandit_applicable: bool = True
    passed: bool = False
    log_tail: str = ""
    baseline_not_reproduced: bool = False


class PRInfo(BaseModel):
    number: int = 0
    url: str = ""
    branch: str = ""
    state: str = "draft"
    merged: bool = False
    created_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


PullRequestInfo = PRInfo


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0


TokenUsage = UsageInfo


class TimingsInfo(BaseModel):
    triage_s: float = 0.0
    analyze_s: float = 0.0
    fix_s: float = 0.0
    validate_s: float = 0.0
    pr_s: float = 0.0
    total_s: float = 0.0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

class Run(BaseModel):
    id: str
    finding_id: str
    status: RunStatus = RunStatus.QUEUED
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    current_agent: str = ""
    attempts: int = 0
    analysis: dict[str, Any] = Field(default_factory=dict)
    patch: PatchInfo = Field(default_factory=PatchInfo)
    validation: ValidationEvidence = Field(default_factory=ValidationEvidence)
    pr: Optional[PRInfo] = None
    usage: UsageInfo = Field(default_factory=UsageInfo)
    timings: TimingsInfo = Field(default_factory=TimingsInfo)
    error: str = ""


# ---------------------------------------------------------------------------
# Event (live agent trace)
# ---------------------------------------------------------------------------

class Event(BaseModel):
    run_id: str
    seq: int
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent: str = "system"          # triage|analyzer|fixer|validator|pr|system
    level: EventLevel = EventLevel.info
    message: str = ""
    data: Optional[dict[str, Any]] = None
