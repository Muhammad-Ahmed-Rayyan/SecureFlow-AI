# backend/tests/test_sandbox.py
# Unit tests for sandbox isolation, scrubbed environment, and zip validation.

import io
import os
import sys
import tempfile
import zipfile
import pytest

from app.tools.sandbox import extract_zipball, get_scrubbed_env, run_cmd


def test_scrubbed_env_excludes_secrets(monkeypatch):
    """The scrubbed environment must never contain API keys or tokens."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-12345")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret_67890")
    monkeypatch.setenv("API_KEY", "my-secret-key")
    monkeypatch.setenv("MY_APP_PASS", "password123")

    env = get_scrubbed_env()
    assert "OPENAI_API_KEY" not in env
    assert "GITHUB_TOKEN" not in env
    assert "API_KEY" not in env
    assert "MY_APP_PASS" not in env


def test_zip_traversal_rejected():
    """Zip slip traversal attempts must raise ValueError."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../escape.txt", "malicious payload")
    zip_bytes = buf.getvalue()

    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(ValueError, match="Zip traversal detected"):
            extract_zipball(zip_bytes, td)


def test_sandbox_run_cmd_basic():
    """Basic command execution in child process."""
    code, stdout, stderr = run_cmd([sys.executable, "-c", "print('hello from sandbox')"], cwd=".")
    assert code == 0
    assert "hello from sandbox" in stdout


def test_sandbox_run_cmd_timeout():
    """Timeout is enforced if command hangs."""
    code, stdout, stderr = run_cmd([sys.executable, "-c", "import time; time.sleep(10)"], cwd=".", timeout=0.5)
    assert code == -1
    assert "timed out" in stderr.lower()
