# backend/app/tools/policy_gate.py
# AST-based patch policy gate. Enforces strict safety rules before any execution.
# Implements TAD section 7 step 1 and Security.md section 6.2.

from __future__ import annotations

import ast
import difflib
from typing import Any

from app.config import settings

FORBIDDEN_CALL_PATTERNS: set[str] = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "os.system",
    "os.popen",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "socket.socket",
    "shutil.rmtree",
}

SAFE_IMPORT_ALLOWLIST: set[str] = {
    "math", "re", "json", "sqlite3", "html", "urllib", "datetime", "typing",
    "copy", "os", "sys", "pathlib", "collections", "enum", "time", "uuid",
    "hashlib", "secrets", "dataclasses", "functools", "itertools", "requests",
    "pydantic", "abc", "contextlib", "logging", "string",
}

DESERIALIZATION_FORBIDDEN: set[str] = {
    "pickle.load",
    "pickle.loads",
    "marshal.loads",
    "yaml.load",
}


def _get_call_names(tree: ast.AST) -> set[str]:
    """Extract all function/method call names from an AST."""
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                # E.g. os.system -> "os.system"
                parts: list[str] = [func.attr]
                curr = func.value
                while isinstance(curr, ast.Attribute):
                    parts.append(curr.attr)
                    curr = curr.value
                if isinstance(curr, ast.Name):
                    parts.append(curr.id)
                calls.add(".".join(reversed(parts)))
    return calls


def _get_imports(tree: ast.AST) -> set[str]:
    """Extract top-level module names of all imports in an AST."""
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def count_diff_lines(original: str, modified: str) -> int:
    """Count total added and removed lines between original and modified text."""
    diff = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            n=0,
        )
    )
    changed = sum(
        1 for line in diff if (line.startswith("+") or line.startswith("-"))
        and not (line.startswith("+++") or line.startswith("---"))
    )
    return changed


def check_patch(
    original_source: str,
    new_source: str,
    changed_paths: list[str] | set[str] | None = None,
    tests_touched: bool = False,
    max_changed_lines: int | None = None,
    vuln_type: str = "",
) -> dict[str, Any]:
    """Execute AST and structural policy gate checks on a proposed patch.

    Returns:
        dict with {"passed": bool, "reasons": list[str]}
    """
    reasons: list[str] = []
    max_lines = max_changed_lines or settings.max_patch_changed_lines

    # Rule 1: Tests must never be touched by agents
    if tests_touched:
        reasons.append("Patch touches test files (disallowed)")

    # Rule 2: Single-file edit boundary
    if changed_paths and len(changed_paths) > 1:
        reasons.append(f"Multi-file edit detected ({len(changed_paths)} files); only single-file patches allowed")

    # Rule 3: Valid Python AST syntax
    try:
        new_tree = ast.parse(new_source)
    except SyntaxError as e:
        reasons.append(f"Patched file has Python syntax error: {str(e)}")
        return {"passed": False, "reasons": reasons}

    try:
        orig_tree = ast.parse(original_source)
    except Exception:
        orig_tree = None

    # Rule 4: Patch size budget
    changed_lines = count_diff_lines(original_source, new_source)
    if changed_lines > max_lines:
        reasons.append(f"Patch changes {changed_lines} lines, exceeding the limit of {max_lines}")

    # Rule 5: No newly introduced dangerous calls
    orig_calls = _get_call_names(orig_tree) if orig_tree else set()
    new_calls = _get_call_names(new_tree)
    introduced_calls = new_calls - orig_calls

    for bad in FORBIDDEN_CALL_PATTERNS:
        # Match exact call or prefix
        for call in introduced_calls:
            if call == bad or call.startswith(bad + ".") or (bad.endswith("*") and call.startswith(bad[:-1])):
                reasons.append(f"Newly introduced dangerous call detected: '{call}'")

    # Rule 6: Import allowlist (new imports must be in allowlist or previously present)
    orig_imports = _get_imports(orig_tree) if orig_tree else set()
    new_imports = _get_imports(new_tree)
    introduced_imports = new_imports - orig_imports

    for imp in introduced_imports:
        if imp not in SAFE_IMPORT_ALLOWLIST:
            reasons.append(f"Disallowed new import detected: '{imp}'")

    # Rule 7: Insecure Deserialization remediation verification
    if vuln_type.strip().lower() in ("insecure deserialization", "deserialization"):
        for call in new_calls:
            if call in DESERIALIZATION_FORBIDDEN:
                reasons.append(f"Insecure deserialization call '{call}' remains in patched code")

    passed = len(reasons) == 0
    return {"passed": passed, "reasons": reasons}
