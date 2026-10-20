# backend/tests/test_policy_gate.py
# Unit tests verifying policy gate enforcement.

import pytest
from app.tools.policy_gate import check_patch


def test_policy_gate_accepts_clean_patch():
    """A clean parameterized SQL query fix must pass all checks."""
    orig = '''
def get_user(conn, username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return conn.execute(query).fetchall()
'''
    patched = '''
def get_user(conn, username):
    query = "SELECT * FROM users WHERE username = ?"
    return conn.execute(query, (username,)).fetchall()
'''
    res = check_patch(orig, patched, changed_paths=["service.py"], vuln_type="SQL Injection")
    assert res["passed"] is True
    assert len(res["reasons"]) == 0


def test_policy_gate_rejects_syntax_error():
    """Syntax errors must fail the policy gate immediately."""
    orig = "def foo(): pass"
    bad_syntax = "def foo(): return pass ("
    res = check_patch(orig, bad_syntax)
    assert res["passed"] is False
    assert any("syntax error" in r.lower() for r in res["reasons"])


def test_policy_gate_rejects_introduced_os_system():
    """Newly introduced dangerous calls (os.system) must be rejected."""
    orig = '''
def greet(name):
    return f"Hello {name}"
'''
    malicious = '''
import os

def greet(name):
    os.system("whoami")
    return f"Hello {name}"
'''
    res = check_patch(orig, malicious)
    assert res["passed"] is False
    assert any("os.system" in r for r in res["reasons"])


def test_policy_gate_rejects_introduced_subprocess():
    """Newly introduced subprocess calls must be rejected."""
    orig = "def run(): return True"
    bad = '''
import subprocess
def run():
    subprocess.run(["ls"])
    return True
'''
    res = check_patch(orig, bad)
    assert res["passed"] is False
    assert any("subprocess" in r for r in res["reasons"])


def test_policy_gate_rejects_disallowed_import():
    """Imports outside the allowlist must be rejected."""
    orig = "def compute(): pass"
    bad = '''
import pty
def compute(): pass
'''
    res = check_patch(orig, bad)
    assert res["passed"] is False
    assert any("disallowed new import" in r.lower() for r in res["reasons"])


def test_policy_gate_rejects_multi_file_and_test_touch():
    """Touching tests or multiple files must be rejected."""
    orig = "x = 1"
    new = "x = 2"
    res1 = check_patch(orig, new, tests_touched=True)
    assert res1["passed"] is False
    assert any("touches test files" in r.lower() for r in res1["reasons"])

    res2 = check_patch(orig, new, changed_paths=["file1.py", "file2.py"])
    assert res2["passed"] is False
    assert any("multi-file" in r.lower() for r in res2["reasons"])


def test_policy_gate_rejects_oversized_patch():
    """Patches exceeding line change limits must be rejected."""
    orig = "x = 1\n"
    # Create 100 added lines
    new = "x = 1\n" + "\n".join(f"y_{i} = {i}" for i in range(100)) + "\n"
    res = check_patch(orig, new, max_changed_lines=80)
    assert res["passed"] is False
    assert any("exceeding the limit" in r.lower() for r in res["reasons"])


def test_policy_gate_rejects_remaining_pickle_loads():
    """For Insecure Deserialization, pickle.loads must not remain in the patched code."""
    orig = '''
import pickle
def load(data):
    return pickle.loads(data)
'''
    bad_fix = '''
import pickle
def load(data):
    # bad fix that keeps pickle
    if data:
        return pickle.loads(data)
    return None
'''
    res = check_patch(orig, bad_fix, vuln_type="Insecure Deserialization")
    assert res["passed"] is False
    assert any("pickle.loads" in r for r in res["reasons"])
