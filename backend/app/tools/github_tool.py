# backend/app/tools/github_tool.py
# PyGithub and requests client for repository trees, file access, zipballs, and draft PRs.
# Uses fine-grained credentials scoped strictly to secureflow-demo-target.

from __future__ import annotations

import base64
import time
from datetime import datetime, timezone
from typing import Any

import requests
from github import Auth, Github, GithubException

from app.config import settings

_tree_cache: dict[str, tuple[float, set[str]]] = {}


def _get_github() -> Github:
    """Return authenticated PyGithub instance."""
    token = settings.github_token
    if token:
        auth = Auth.Token(token)
        return Github(auth=auth)
    return Github()


def _get_repo(gh: Github | None = None):
    """Return the target repository instance."""
    client = gh or _get_github()
    full_name = f"{settings.github_owner}/{settings.target_repo}"
    return client.get_repo(full_name)


def get_repo_tree(ref: str | None = None, force_refresh: bool = False) -> set[str]:
    """Fetch all file paths in the target repository. Cached for 60 seconds."""
    branch = ref or settings.target_base_branch
    now = time.time()

    if not force_refresh and branch in _tree_cache:
        cached_time, cached_set = _tree_cache[branch]
        if now - cached_time < 60:
            return cached_set

    # If no token is provided, return empty set (or known paths)
    if not settings.github_token:
        return set()

    try:
        repo = _get_repo()
        git_tree = repo.get_git_tree(branch, recursive=True)
        paths = {element.path for element in git_tree.tree if element.type == "blob"}
        _tree_cache[branch] = (now, paths)
        return paths
    except Exception:
        return set()


def get_file(path: str, ref: str | None = None) -> tuple[str, str]:
    """Retrieve decoded file content and sha for a file in the target repository."""
    branch = ref or settings.target_base_branch
    repo = _get_repo()
    content_file = repo.get_contents(path, ref=branch)
    if isinstance(content_file, list):
        raise ValueError(f"Path '{path}' is a directory, not a file")

    raw_bytes = base64.b64decode(content_file.content)
    text = raw_bytes.decode("utf-8")
    return text, content_file.sha


def download_zipball(ref: str | None = None) -> bytes:
    """Download the repository zipball as raw bytes using the GitHub API."""
    branch = ref or settings.target_base_branch
    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.target_repo}/zipball/{branch}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    res = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
    res.raise_for_status()
    return res.content


def create_branch(name: str, base: str | None = None) -> bool:
    """Create a new branch from base branch. Idempotent if already exists."""
    base_branch = base or settings.target_base_branch
    repo = _get_repo()
    base_ref = repo.get_git_ref(f"heads/{base_branch}")
    sha = base_ref.object.sha

    try:
        repo.create_git_ref(f"refs/heads/{name}", sha)
        return True
    except GithubException as e:
        if e.status == 422:  # Reference already exists
            return False
        raise


def commit_file(
    branch: str,
    path: str,
    content: str,
    message: str,
    sha: str | None = None,
) -> str:
    """Create or update a file on the specified branch and return the new commit sha."""
    repo = _get_repo()
    current_sha = sha
    if not current_sha:
        try:
            cf = repo.get_contents(path, ref=branch)
            if not isinstance(cf, list):
                current_sha = cf.sha
        except GithubException:
            current_sha = None

    if current_sha:
        res = repo.update_file(
            path=path,
            message=message,
            content=content,
            sha=current_sha,
            branch=branch,
        )
    else:
        res = repo.create_file(
            path=path,
            message=message,
            content=content,
            branch=branch,
        )
    return res["commit"].sha


def open_draft_pr(
    branch: str,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Open a DRAFT pull request with labels security, auto-generated, needs-review.

    Hard rule: agents open draft PRs only, never merge.
    """
    repo = _get_repo()
    base = settings.target_base_branch
    pr_labels = labels or ["security", "auto-generated", "needs-review"]

    pr = repo.create_pull(
        title=title,
        body=body,
        base=base,
        head=branch,
        draft=True,
    )

    try:
        pr.add_to_labels(*pr_labels)
    except Exception:
        pass

    return {
        "number": pr.number,
        "url": pr.html_url,
        "branch": branch,
        "state": "open",
        "created_at": pr.created_at or datetime.now(timezone.utc),
    }


def get_pr_state(number: int) -> dict[str, Any]:
    """Retrieve live pull request status (merged, open, or closed)."""
    repo = _get_repo()
    pr = repo.get_pull(number)
    state = "merged" if pr.is_merged() else pr.state

    return {
        "number": pr.number,
        "state": state,
        "merged": pr.is_merged(),
        "created_at": pr.created_at,
        "merged_at": pr.merged_at,
        "closed_at": pr.closed_at,
    }
