# backend/app/agents/state.py
# State definition for LangGraph agent pipeline.

from __future__ import annotations

from typing import Any, Optional, TypedDict


class RunState(TypedDict, total=False):
    run_id: str
    finding_id: str
    finding: dict[str, Any]
    file_path: str
    original_content: str
    analysis: dict[str, Any]
    patch: dict[str, Any]
    validation: dict[str, Any]
    attempts: int
    last_error: Optional[str]
    pr: dict[str, Any]
    status: str
    timings: dict[str, float]
    usage: dict[str, int]
    error: Optional[str]
