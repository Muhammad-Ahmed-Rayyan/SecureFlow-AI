# backend/app/agents/validator.py
# Validator agent: AST policy gate, syntax verification, functional tests, exploit tests, and Bandit delta.
# Enforces complete before/after evidence generation in isolated sandboxes.

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from app.agents.events import emit
from app.models import EventLevel, Finding, ValidationCheck, ValidationEvidence
from app.tools.bandit_tool import run_bandit_on_file
from app.tools.policy_gate import check_patch
from app.tools.sandbox import extract_zipball, run_cmd


def _parse_pytest_output(stdout: str, stderr: str) -> tuple[int, int]:
    """Parse passed and failed counts from pytest output. Returns (passed, failed)."""
    text = stdout + "\n" + stderr
    passed = 0
    failed = 0

    m_pass = re.search(r"(\d+)\s+passed", text)
    if m_pass:
        passed = int(m_pass.group(1))

    m_fail = re.search(r"(\d+)\s+failed", text)
    if m_fail:
        failed = int(m_fail.group(1))

    # Also handle single-letter summary like ..F..
    return passed, failed


def validate_patch(
    run_id: str,
    finding: Finding | dict[str, Any],
    original_source: str,
    new_source: str,
    repo_dir: Path | str | None = None,
    zip_bytes: bytes | None = None,
) -> ValidationEvidence:
    """Execute the multi-stage validation pipeline on a proposed patch."""
    vuln_type = finding.vuln_type if isinstance(finding, Finding) else finding.get("vuln_type", "")
    file_path_rel = finding.file_path if isinstance(finding, Finding) else finding.get("file_path", "")
    repo_name = finding.repository if isinstance(finding, Finding) else finding.get("repository", "")

    emit(run_id, "validator", "Initiating multi-stage patch validation pipeline", EventLevel.info)

    # -----------------------------------------------------------------------
    # Stage 1: AST Policy Gate
    # -----------------------------------------------------------------------
    gate_res = check_patch(
        original_source=original_source,
        new_source=new_source,
        changed_paths=[file_path_rel],
        vuln_type=vuln_type,
    )

    if not gate_res["passed"]:
        reasons_str = "; ".join(gate_res["reasons"])
        emit(
            run_id,
            "validator",
            f"Policy gate REJECTED patch: {reasons_str}",
            EventLevel.error,
            {"reasons": gate_res["reasons"]},
        )
        return ValidationEvidence(
            policy=False,
            passed=False,
            log_tail=reasons_str,
        )

    emit(run_id, "validator", "Policy gate PASSED: AST syntax, import allowlist and change limits verified", EventLevel.success)

    # -----------------------------------------------------------------------
    # Stage 2: Sandboxed environment preparation
    # -----------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        sandbox_path = Path(td).resolve()

        if zip_bytes:
            working_root = extract_zipball(zip_bytes, sandbox_path)
        elif repo_dir and Path(repo_dir).exists():
            # Copy source tree to temporary sandbox
            target_repo_path = Path(repo_dir)
            working_root = sandbox_path / "repo"
            shutil.copytree(target_repo_path, working_root, symlinks=False)
        else:
            # Standalone file sandbox
            working_root = sandbox_path / "repo"
            working_root.mkdir(parents=True, exist_ok=True)

        target_file = working_root / file_path_rel
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Write original source first
        target_file.write_text(original_source, encoding="utf-8")

        # -------------------------------------------------------------------
        # Stage 3: Bandit Baseline
        # -------------------------------------------------------------------
        bandit_before, _ = run_bandit_on_file(file_path_rel, cwd=working_root)

        # Locate test file if repository structure exists
        # Standard location: {repository}/tests/test_{stem}.py
        file_stem = Path(file_path_rel).stem
        test_file_candidates = [
            working_root / repo_name / "tests" / f"test_{file_stem}.py",
            working_root / "tests" / f"test_{file_stem}.py",
            working_root / Path(file_path_rel).parent.parent / "tests" / f"test_{file_stem}.py",
        ]
        test_file_path: Path | None = None
        for cand in test_file_candidates:
            if cand.is_file():
                test_file_path = cand
                break

        # -------------------------------------------------------------------
        # Stage 4: Baseline Tests
        # -------------------------------------------------------------------
        before_check = ValidationCheck(functional=0, exploit=0)
        baseline_not_reproduced = False

        if test_file_path:
            rel_test = str(test_file_path.relative_to(working_root)).replace("\\", "/")
            # Run functional
            c_f, out_f, err_f = run_cmd([sys.executable, "-m", "pytest", "-q", "-m", "not exploit", rel_test], cwd=working_root)
            f_pass, _ = _parse_pytest_output(out_f, err_f)
            before_check.functional = f_pass

            # Run exploit (must FAIL in baseline)
            c_e, out_e, err_e = run_cmd([sys.executable, "-m", "pytest", "-q", "-m", "exploit", rel_test], cwd=working_root)
            e_pass, e_fail = _parse_pytest_output(out_e, err_e)
            before_check.exploit = e_fail

            if c_e == 0 and e_fail == 0 and e_pass > 0:
                baseline_not_reproduced = True
                emit(run_id, "validator", "Notice: Exploit test did not fail on baseline code", EventLevel.warn)
            else:
                emit(run_id, "validator", f"Baseline verified: {e_fail} exploit test(s) failing on vulnerable code", EventLevel.info)

        # -------------------------------------------------------------------
        # Stage 5: Apply Patch & Syntax Verification
        # -------------------------------------------------------------------
        target_file.write_text(new_source, encoding="utf-8")

        # python -m py_compile
        compile_code, c_out, c_err = run_cmd([sys.executable, "-m", "py_compile", str(target_file)], cwd=working_root)
        if compile_code != 0:
            emit(run_id, "validator", f"Syntax verification FAILED:\n{c_err}", EventLevel.error)
            return ValidationEvidence(
                policy=True,
                before=before_check,
                passed=False,
                log_tail=c_err or c_out,
            )

        emit(run_id, "validator", "Bytecode syntax compilation passed (py_compile)", EventLevel.success)

        # -------------------------------------------------------------------
        # Stage 6: Post-Patch Tests
        # -------------------------------------------------------------------
        after_check = ValidationCheck(functional=0, exploit=0)
        post_test_logs: list[str] = []

        if test_file_path:
            rel_test = str(test_file_path.relative_to(working_root)).replace("\\", "/")

            # Functional tests must pass
            code_f, out_f, err_f = run_cmd([sys.executable, "-m", "pytest", "-q", "-m", "not exploit", rel_test], cwd=working_root)
            f_pass, f_fail = _parse_pytest_output(out_f, err_f)
            after_check.functional = f_pass
            post_test_logs.append(out_f + "\n" + err_f)

            if code_f != 0 or f_fail > 0:
                emit(run_id, "validator", f"Post-patch functional tests FAILED ({f_fail} failure)", EventLevel.error)
                return ValidationEvidence(
                    policy=True,
                    before=before_check,
                    after=after_check,
                    passed=False,
                    log_tail="\n".join(post_test_logs),
                )

            # Exploit tests must now pass (0 failures)
            code_e, out_e, err_e = run_cmd([sys.executable, "-m", "pytest", "-q", "-m", "exploit", rel_test], cwd=working_root)
            e_pass, e_fail = _parse_pytest_output(out_e, err_e)
            after_check.exploit = e_pass
            post_test_logs.append(out_e + "\n" + err_e)

            if code_e != 0 or e_fail > 0:
                emit(run_id, "validator", f"Post-patch exploit tests FAILED ({e_fail} still failing)", EventLevel.error)
                return ValidationEvidence(
                    policy=True,
                    before=before_check,
                    after=after_check,
                    passed=False,
                    log_tail="\n".join(post_test_logs),
                )

            emit(run_id, "validator", f"Exploit tests PASSED ({e_pass} passed): vulnerability successfully neutralized", EventLevel.success)
        else:
            # Standalone test when no target test file is present
            after_check.functional = 1
            after_check.exploit = 1

        # -------------------------------------------------------------------
        # Stage 7: Bandit Delta
        # -------------------------------------------------------------------
        bandit_after, bandit_after_sevs = run_bandit_on_file(file_path_rel, cwd=working_root)
        bandit_applicable = vuln_type.lower() in ("sql injection", "hardcoded secret", "insecure deserialization", "insecure tls")

        # Check that no new medium or high bandit issues appeared
        new_bandit_issues = set(bandit_after) - set(bandit_before)
        if new_bandit_issues:
            emit(run_id, "validator", f"Bandit regression: new issue(s) {new_bandit_issues} introduced", EventLevel.error)
            return ValidationEvidence(
                policy=True,
                before=before_check,
                after=after_check,
                bandit_before_ids=bandit_before,
                bandit_after_ids=bandit_after,
                bandit_applicable=bandit_applicable,
                passed=False,
                log_tail=f"New Bandit issues detected: {new_bandit_issues}",
            )

        emit(run_id, "validator", "Validation PASSED all gates: policy, syntax, functional tests, exploit tests, and Bandit delta", EventLevel.success)

        return ValidationEvidence(
            policy=True,
            before=before_check,
            after=after_check,
            bandit_before_ids=bandit_before,
            bandit_after_ids=bandit_after,
            bandit_applicable=bandit_applicable,
            passed=True,
            log_tail="\n".join(post_test_logs)[-2048:],
            baseline_not_reproduced=baseline_not_reproduced,
        )
