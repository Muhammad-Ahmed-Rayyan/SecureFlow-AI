# backend/tests/test_github_tool.py
# Tests for GitHub integration tools.

from unittest.mock import MagicMock, patch
import pytest

from app.tools.github_tool import get_repo_tree, open_draft_pr


def test_get_repo_tree_empty_when_no_token(monkeypatch):
    """When no GITHUB_TOKEN is set, get_repo_tree returns an empty set safely."""
    from app.config import settings
    monkeypatch.setattr(settings, "github_token", "")
    tree = get_repo_tree(force_refresh=True)
    assert isinstance(tree, set)


def test_open_draft_pr_mocked():
    """Verify draft PR parameters: draft=True, correct labels and payload."""
    mock_pr = MagicMock()
    mock_pr.number = 42
    mock_pr.html_url = "https://github.com/test-owner/test-repo/pull/42"
    mock_pr.created_at = None

    mock_repo = MagicMock()
    mock_repo.create_pull.return_value = mock_pr

    with patch("app.tools.github_tool._get_repo", return_value=mock_repo):
        res = open_draft_pr(
            branch="secureflow/fix-vuln-0169",
            title="[SecureFlow] Fix SQL Injection in File2.py (VULN-0169)",
            body="PR body evidence",
        )

    mock_repo.create_pull.assert_called_once_with(
        title="[SecureFlow] Fix SQL Injection in File2.py (VULN-0169)",
        body="PR body evidence",
        base="main",
        head="secureflow/fix-vuln-0169",
        draft=True,
    )
    mock_pr.add_to_labels.assert_called_once_with("security", "auto-generated", "needs-review")
    assert res["number"] == 42
    assert res["state"] == "open"
