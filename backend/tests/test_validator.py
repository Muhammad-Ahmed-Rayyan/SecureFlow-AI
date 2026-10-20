# backend/tests/test_validator.py
# Unit tests for the Validator agent.

import pytest

from app.agents.validator import validate_patch
from app.models import Finding, SeverityEnum, TierEnum


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        id="VULN-0169",
        repository="notification-svc",
        file_path="src/main/service/File2.py",
        vuln_type="SQL Injection",
        severity=SeverityEnum.CRITICAL,
        line_reported=248,
        tier=TierEnum.AUTO_FIX,
    )


def test_validator_passes_known_good_patch(sample_finding):
    """A clean parameterized query patch passes the validator pipeline."""
    orig = '''
def get_notifications_for_user(conn, username):
    query = f"SELECT * FROM notifications WHERE username = '{username}'"
    return conn.execute(query).fetchall()
'''
    good_patch = '''
def get_notifications_for_user(conn, username):
    query = "SELECT * FROM notifications WHERE username = ?"
    return conn.execute(query, (username,)).fetchall()
'''
    evidence = validate_patch(
        run_id="test-run-good",
        finding=sample_finding,
        original_source=orig,
        new_source=good_patch,
    )
    assert evidence.policy is True
    assert evidence.passed is True


def test_validator_fails_known_bad_patch_with_os_system(sample_finding):
    """A patch introducing dangerous os.system calls fails the policy gate."""
    orig = '''
def get_notifications_for_user(conn, username):
    return conn.execute(f"SELECT * FROM notifications WHERE username = '{username}'").fetchall()
'''
    bad_patch = '''
import os
def get_notifications_for_user(conn, username):
    os.system("echo hacked")
    return conn.execute("SELECT * FROM notifications WHERE username = ?", (username,)).fetchall()
'''
    evidence = validate_patch(
        run_id="test-run-bad",
        finding=sample_finding,
        original_source=orig,
        new_source=bad_patch,
    )
    assert evidence.policy is False
    assert evidence.passed is False
    assert "os.system" in evidence.log_tail


def test_validator_fails_syntax_error(sample_finding):
    """A patch with invalid Python syntax fails before test execution."""
    orig = "def foo(): pass"
    bad_syntax = "def foo(): return pass ("

    evidence = validate_patch(
        run_id="test-run-syntax",
        finding=sample_finding,
        original_source=orig,
        new_source=bad_syntax,
    )
    assert evidence.passed is False
