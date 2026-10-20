# backend/app/tools/sandbox.py
# Sandboxed execution environment for testing patches and running security tools.
# Enforces strict zip validation, scrubbed child environment, and non-shell execution.

from __future__ import annotations

import io
import os
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from app.config import settings

# Maximum captured log output per stream (4 KB)
MAX_CAPTURE_BYTES = 4096


def get_scrubbed_env(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build a sanitized environment containing only essential OS variables.

    Explicitly excludes OPENAI_API_KEY, GITHUB_TOKEN, API_KEY, and cloud credentials.
    """
    allowlist = {"PATH", "SYSTEMROOT", "PYTHONPATH", "TEMP", "TMP", "COMSPEC", "PATHEXT"}
    scrubbed: dict[str, str] = {
        k: v for k, v in os.environ.items() if k.upper() in allowlist
    }
    if extra_env:
        for k, v in extra_env.items():
            if not any(secret in k.upper() for secret in ("KEY", "TOKEN", "SECRET", "AUTH", "PASS")):
                scrubbed[k] = v
    return scrubbed


def extract_zipball(zip_bytes: bytes, target_dir: str | Path) -> Path:
    """Extract repository zipball safely into target_dir.

    Protects against Zip Slip directory traversal attacks.
    If the zip archive has a single top-level directory (standard GitHub zipball format),
    returns the path to that inner directory.
    """
    dest = Path(target_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.infolist():
            # Resolve target path and assert it stays inside dest
            target_path = (dest / member.filename).resolve()
            try:
                target_path.relative_to(dest)
            except ValueError:
                raise ValueError(f"Zip traversal detected: '{member.filename}' escapes target directory")

        zf.extractall(dest)

    # Check if archive extracted into a single top-level directory
    children = list(dest.iterdir())
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return dest


def run_cmd(
    args: list[str],
    cwd: str | Path,
    timeout: float | None = None,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Execute a command inside the sandbox with strict isolation.

    - shell=False strictly enforced
    - Scrubbed environment (no keys or tokens)
    - Timeout enforced (defaults to SANDBOX_TIMEOUT_SECONDS)
    - Stdout and stderr capped to the last 4 KB
    """
    run_timeout = timeout or float(settings.sandbox_timeout_seconds)
    env = get_scrubbed_env(extra_env)

    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            shell=False,
            capture_output=True,
            timeout=run_timeout,
            env=env,
            text=True,
            errors="replace",
        )
        stdout = proc.stdout[-MAX_CAPTURE_BYTES:] if len(proc.stdout) > MAX_CAPTURE_BYTES else proc.stdout
        stderr = proc.stderr[-MAX_CAPTURE_BYTES:] if len(proc.stderr) > MAX_CAPTURE_BYTES else proc.stderr
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired as e:
        stdout_raw = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode("utf-8", "replace") if e.stdout else "")
        stderr_raw = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode("utf-8", "replace") if e.stderr else "")
        return -1, stdout_raw[-MAX_CAPTURE_BYTES:], f"Command timed out after {run_timeout} seconds\n" + stderr_raw[-MAX_CAPTURE_BYTES:]
