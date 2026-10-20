# backend/app/agents/graph.py
# LangGraph state graph orchestrating the 5 security agents with a validation retry loop.
# Implements TAD section 6.2 state graph and conditional routing.

from __future__ import annotations

import time
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.analyzer import analyze_vulnerability
from app.agents.events import emit
from app.agents.fixer import generate_patch
from app.agents.pr_agent import create_remediation_pr
from app.agents.state import RunState
from app.agents.validator import validate_patch
from app.config import settings
from app.models import EventLevel, RunStatus, TierEnum


def triage_gate_node(state: RunState) -> dict[str, Any]:
    """Verify tiering and source code availability before invoking generative agents."""
    t0 = time.time()
    run_id = state["run_id"]
    finding = state["finding"]

    tier = finding.get("tier")
    source_avail = finding.get("source_available", False)

    emit(run_id, "triage", f"Evaluating triage gate for {finding.get('id')} ({finding.get('vuln_type')})", EventLevel.info)

    # Convert tier enum if needed
    tier_val = tier.value if hasattr(tier, "value") else str(tier)

    if tier_val != TierEnum.AUTO_FIX.value and tier_val != "AUTO_FIX":
        reason = finding.get("tier_reason", "Finding tier is not eligible for auto-fix")
        timings = dict(state.get("timings") or {})
        return {
            "status": RunStatus.ESCALATED.value,
            "error": reason,
            "timings": {**timings, "triage_s": round(time.time() - t0, 2)},
        }

    if not source_avail:
        reason = f"Source code for '{finding.get('file_path')}' is not available in target repository"
        emit(run_id, "triage", f"Triage gate rejected: {reason}", EventLevel.warn)
        timings = dict(state.get("timings") or {})
        return {
            "status": RunStatus.ESCALATED.value,
            "error": reason,
            "timings": {**timings, "triage_s": round(time.time() - t0, 2)},
        }

    emit(run_id, "triage", "Triage gate passed: finding is fix-ready in target repository", EventLevel.success)
    timings = dict(state.get("timings") or {})
    return {
        "status": RunStatus.RUNNING.value,
        "timings": {**timings, "triage_s": round(time.time() - t0, 2)},
    }


def analyze_node(state: RunState) -> dict[str, Any]:
    """Execute vulnerability analyzer agent."""
    t0 = time.time()
    run_id = state["run_id"]
    finding = state["finding"]
    orig_content = state.get("original_content", "")

    analysis, usage = analyze_vulnerability(run_id, finding, orig_content)

    prev_usage = dict(state.get("usage") or {"prompt_tokens": 0, "completion_tokens": 0})
    new_usage = {
        "prompt_tokens": prev_usage.get("prompt_tokens", 0) + usage.get("prompt_tokens", 0),
        "completion_tokens": prev_usage.get("completion_tokens", 0) + usage.get("completion_tokens", 0),
    }

    timings = dict(state.get("timings") or {})
    return {
        "analysis": analysis,
        "usage": new_usage,
        "timings": {**timings, "analyze_s": round(time.time() - t0, 2)},
    }


def fix_node(state: RunState) -> dict[str, Any]:
    """Execute patch synthesizer agent with optional retry error context."""
    t0 = time.time()
    run_id = state["run_id"]
    orig_content = state.get("original_content", "")
    analysis = state.get("analysis", {})
    last_error = state.get("last_error")
    attempts = state.get("attempts", 0) + 1

    patch, usage = generate_patch(run_id, orig_content, analysis, last_error=last_error)

    prev_usage = dict(state.get("usage") or {"prompt_tokens": 0, "completion_tokens": 0})
    new_usage = {
        "prompt_tokens": prev_usage.get("prompt_tokens", 0) + usage.get("prompt_tokens", 0),
        "completion_tokens": prev_usage.get("completion_tokens", 0) + usage.get("completion_tokens", 0),
    }

    timings = dict(state.get("timings") or {})
    return {
        "patch": patch,
        "attempts": attempts,
        "usage": new_usage,
        "timings": {**timings, "fix_s": round(time.time() - t0, 2)},
    }


def validate_node(state: RunState) -> dict[str, Any]:
    """Execute multi-gate validation pipeline on the proposed patch."""
    t0 = time.time()
    run_id = state["run_id"]
    finding = state["finding"]
    orig_content = state.get("original_content", "")
    patch = state.get("patch", {})
    new_content = patch.get("new_content", "")

    evidence = validate_patch(
        run_id=run_id,
        finding=finding,
        original_source=orig_content,
        new_source=new_content,
    )

    last_error = evidence.log_tail if not evidence.passed else None

    timings = dict(state.get("timings") or {})
    return {
        "validation": evidence.model_dump(),
        "last_error": last_error,
        "timings": {**timings, "validate_s": round(time.time() - t0, 2)},
    }


def open_pr_node(state: RunState) -> dict[str, Any]:
    """Execute PR agent to open draft pull request with validation evidence."""
    t0 = time.time()
    run_id = state["run_id"]
    finding = state["finding"]
    analysis = state.get("analysis", {})
    patch = state.get("patch", {})
    validation = state.get("validation", {})

    pr_info = create_remediation_pr(run_id, finding, analysis, patch, validation)

    timings = dict(state.get("timings") or {})
    return {
        "pr": pr_info,
        "status": RunStatus.PR_OPEN.value,
        "timings": {**timings, "pr_s": round(time.time() - t0, 2)},
    }


def decide_after_triage(state: RunState) -> str:
    """Route to analyze if triage passed; otherwise end with escalation."""
    if state.get("status") == RunStatus.ESCALATED.value:
        return END
    return "analyze"


def decide_after_validate(state: RunState) -> str:
    """Route to PR if passed; retry fix if attempts remain; else end FAILED."""
    val = state.get("validation", {})
    if val.get("passed") is True:
        return "open_pr"

    attempts = state.get("attempts", 1)
    if attempts < settings.max_fix_attempts:
        emit(
            state["run_id"],
            "validator",
            f"Validation failed (attempt {attempts}/{settings.max_fix_attempts}). Routing back to Fixer agent with error feedback.",
            EventLevel.warn,
        )
        return "fix"

    emit(
        state["run_id"],
        "validator",
        f"Validation failed after reaching max attempts ({attempts}). Run marked FAILED.",
        EventLevel.error,
    )
    return "mark_failed"


def mark_failed_node(state: RunState) -> dict[str, Any]:
    """Final node for unresolvable validation errors."""
    return {"status": RunStatus.FAILED.value}


def build_remediation_graph():
    """Construct and compile the LangGraph StateGraph workflow."""
    builder = StateGraph(RunState)

    builder.add_node("triage_gate", triage_gate_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("fix", fix_node)
    builder.add_node("validate", validate_node)
    builder.add_node("open_pr", open_pr_node)
    builder.add_node("mark_failed", mark_failed_node)

    builder.set_entry_point("triage_gate")

    builder.add_conditional_edges("triage_gate", decide_after_triage)
    builder.add_edge("analyze", "fix")
    builder.add_edge("fix", "validate")
    builder.add_conditional_edges(
        "validate",
        decide_after_validate,
        {
            "open_pr": "open_pr",
            "fix": "fix",
            "mark_failed": "mark_failed",
        },
    )
    builder.add_edge("open_pr", END)
    builder.add_edge("mark_failed", END)

    return builder.compile()


workflow = build_remediation_graph()
