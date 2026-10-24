"""Unit tests for GitHub API utilities and URL parsing."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from github_utils import (
    build_github_file_url,
    filter_valid_files,
    get_file_tree,
    get_issue,
    get_readme,
    github_get,
    normalize_path,
    parse_issue_url,
    select_candidate_files,
)


def test_parse_issue_url_valid():
    """Test valid GitHub issue URLs with various standard formats."""
    # Standard URL
    owner, repo, number = parse_issue_url("https://github.com/owner/repo/issues/42")
    assert owner == "owner"
    assert repo == "repo"
    assert number == 42

    # Trailing slash
    owner, repo, number = parse_issue_url("https://github.com/fastapi/fastapi/issues/1000/")
    assert owner == "fastapi"
    assert repo == "fastapi"
    assert number == 1000

    # With query params and fragment
    owner, repo, number = parse_issue_url(
        "https://github.com/psf/requests/issues/555?notification_referrer_id=123#issuecomment-999"
    )
    assert owner == "psf"
    assert repo == "requests"
    assert number == 555

    # With www
    owner, repo, number = parse_issue_url("https://www.github.com/pallets/flask/issues/123")
    assert owner == "pallets"
    assert repo == "flask"
    assert number == 123


def test_parse_issue_url_invalid():
    """Test that malformed or non-GitHub URLs raise ValueError with helpful messages."""
    with pytest.raises(ValueError, match="Please provide a valid GitHub issue URL"):
        parse_issue_url("")

    with pytest.raises(ValueError, match="Invalid host"):
        parse_issue_url("https://gitlab.com/owner/repo/issues/123")

    with pytest.raises(ValueError, match="Invalid host"):
        parse_issue_url("not a url at all")

    with pytest.raises(ValueError, match="Invalid GitHub issue URL format"):
        parse_issue_url("https://github.com/owner/repo")

    with pytest.raises(ValueError, match="Invalid GitHub issue URL format"):
        parse_issue_url("https://github.com/owner/repo/issues")

    with pytest.raises(ValueError, match="Invalid GitHub issue URL format"):
        parse_issue_url("https://github.com/owner/repo/issues/notanumber")


def test_parse_issue_url_pull_request_rejection():
    """Test that pull request URLs are explicitly rejected."""
    with pytest.raises(ValueError, match="points to a pull request"):
        parse_issue_url("https://github.com/owner/repo/pull/123")

    with pytest.raises(ValueError, match="points to a pull request"):
        parse_issue_url("https://github.com/owner/repo/pull/456#issuecomment-789")


@patch("github_utils.requests.get")
def test_github_get_404(mock_get):
    """Test handling of 404 Not Found error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.ok = False
    mock_get.return_value = mock_resp

    with pytest.raises(RuntimeError, match="GitHub resource not found"):
        github_get("repos/unknown/unknown/issues/1")


@patch("github_utils.requests.get")
def test_github_get_rate_limit(mock_get):
    """Test handling of GitHub 403 / 429 rate limit exceeded."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.ok = False
    mock_resp.headers = {"x-ratelimit-remaining": "0"}
    mock_get.return_value = mock_resp

    with pytest.raises(RuntimeError, match="rate limit exceeded"):
        github_get("repos/owner/repo/issues/1")

    # 429 Too Many Requests
    mock_resp.status_code = 429
    mock_resp.headers = {}
    with pytest.raises(RuntimeError, match="rate limit exceeded"):
        github_get("repos/owner/repo/issues/1")


@patch("github_utils.requests.get")
def test_github_get_timeout(mock_get):
    """Test handling of network timeouts."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    with pytest.raises(RuntimeError, match="timed out"):
        github_get("repos/owner/repo/issues/1")


@patch("github_utils.github_get")
def test_get_issue_success(mock_github_get):
    """Test successful retrieval and structuring of issue metadata."""
    mock_github_get.return_value = {
        "title": "Bug in query parser",
        "body": "When passing special characters, parser crashes.",
        "state": "open",
        "html_url": "https://github.com/owner/repo/issues/42",
        "labels": [{"name": "bug"}, {"name": "good first issue"}],
    }

    issue = get_issue("https://github.com/owner/repo/issues/42")

    assert issue["owner"] == "owner"
    assert issue["repo"] == "repo"
    assert issue["number"] == 42
    assert issue["title"] == "Bug in query parser"
    assert issue["body"] == "When passing special characters, parser crashes."
    assert issue["state"] == "open"
    assert issue["labels"] == ["bug", "good first issue"]


@patch("github_utils.github_get")
def test_get_issue_rejects_pr_from_api(mock_github_get):
    """Test that if the GitHub API returns a pull_request key, get_issue rejects it."""
    mock_github_get.return_value = {
        "title": "A PR disguised as an issue",
        "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/42"},
    }

    with pytest.raises(ValueError, match="points to a pull request"):
        get_issue("https://github.com/owner/repo/issues/42")


@patch("github_utils.github_get")
def test_get_readme_success(mock_github_get):
    """Test successfully fetching and decoding a base64 README."""
    import base64

    readme_content = "# Welcome to the Repo\nThis is a cool project."
    encoded = base64.b64encode(readme_content.encode("utf-8")).decode("utf-8")
    mock_github_get.return_value = {"content": encoded}

    content = get_readme("owner", "repo")
    assert content == readme_content


@patch("github_utils.github_get")
def test_get_readme_missing(mock_github_get):
    """Test graceful fallback when README is missing (e.g. 404)."""
    mock_github_get.side_effect = RuntimeError("Not found")

    content = get_readme("owner", "repo")
    assert content == "README unavailable."


@patch("github_utils.github_get")
def test_get_file_tree(mock_github_get):
    """Test fetching repository file tree and default branch."""
    def side_effect(endpoint, **kwargs):
        if endpoint == "repos/owner/repo":
            return {"default_branch": "develop"}
        if endpoint == "repos/owner/repo/branches/develop":
            return {"commit": {"sha": "abc123sha"}}
        if endpoint == "repos/owner/repo/git/trees/abc123sha?recursive=1":
            return {
                "truncated": False,
                "tree": [
                    {"path": "src/main.py", "type": "blob"},
                    {"path": "src/parser.py", "type": "blob"},
                    {"path": "src", "type": "tree"},  # directory
                    {"path": "README.md", "type": "blob"},
                ],
            }
        raise ValueError(f"Unexpected endpoint: {endpoint}")

    mock_github_get.side_effect = side_effect

    paths, default_branch = get_file_tree("owner", "repo")
    assert default_branch == "develop"
    assert "src/main.py" in paths
    assert "src/parser.py" in paths
    assert "README.md" in paths
    assert "src" not in paths  # tree should be excluded, only blobs


def test_filter_valid_files():
    """Test that model-suggested paths are strictly verified against actual repository files."""
    repo_files = [
        "src/auth/login.py",
        "src/auth/tokens.py",
        "src/utils.py",
        "tests/test_login.py",
    ]

    suggested = [
        {"path": "src/auth/login.py", "reason": "Contains authentication logic"},
        {"path": "./src/utils.py", "reason": "Helper functions"},
        {"path": "src/auth/nonexistent.py", "reason": "Hallucinated file"},
        {"path": "totally/fake/path.js", "reason": "Another hallucination"},
    ]

    verified = filter_valid_files(suggested, repo_files)

    assert len(verified) == 2
    paths = [item["path"] for item in verified]
    assert "src/auth/login.py" in paths
    assert "src/utils.py" in paths
    assert "src/auth/nonexistent.py" not in paths
    assert "totally/fake/path.js" not in paths


def test_filter_valid_files_empty():
    """Test edge cases with empty files or no suggestions."""
    assert filter_valid_files([], ["a.py"]) == []
    assert filter_valid_files([{"path": "a.py"}], []) == []


def test_select_candidate_files():
    """Test candidate selection prioritizes relevant files and excludes junk."""
    all_files = [
        ".git/HEAD",
        "node_modules/pkg/index.js",
        "dist/bundle.js",
        "assets/logo.png",
        "src/auth/jwt.py",
        "src/database/models.py",
        "README.md",
        "package-lock.json",
    ]

    candidates = select_candidate_files(
        all_files,
        issue_title="JWT authentication token expired error",
        issue_body="The auth token crashes on decode",
        max_files=5,
    )

    # Should exclude noise
    assert ".git/HEAD" not in candidates
    assert "assets/logo.png" not in candidates
    assert "package-lock.json" not in candidates
    # Should include jwt.py
    assert "src/auth/jwt.py" in candidates


def test_build_github_file_url():
    """Test constructing direct GitHub file URL."""
    url = build_github_file_url("owner", "repo", "main", "src/core/app.py")
    assert url == "https://github.com/owner/repo/blob/main/src/core/app.py"


def test_normalize_path():
    """Test path normalization."""
    assert normalize_path("./src\\module/file.py") == "src/module/file.py"
    assert normalize_path("/deep/path.ts") == "deep/path.ts"
