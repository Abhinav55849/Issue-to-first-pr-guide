"""GitHub API integration utilities for Issue-to-First-PR Guide.

Handles safe URL parsing, issue metadata retrieval, README fetching,
file tree exploration, candidate file selection, and path verification.
"""

from __future__ import annotations

import base64
import os
import re
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 20


def parse_issue_url(issue_url: str) -> tuple[str, str, int]:
    """Extract owner, repository name, and issue number from a GitHub issue URL.

    Safely handles trailing slashes, URL query parameters, and fragments.
    Explicitly rejects pull request URLs and invalid formats with clear error messages.
    """
    if not issue_url or not isinstance(issue_url, str):
        raise ValueError("Please provide a valid GitHub issue URL.")

    clean_url = issue_url.strip()
    parsed = urlparse(clean_url)

    # Validate hostname
    netloc = parsed.netloc.lower()
    if netloc not in ("github.com", "www.github.com"):
        raise ValueError(
            "Invalid host. Expected a GitHub URL (e.g., https://github.com/owner/repository/issues/123)."
        )

    # Clean path from leading/trailing slashes
    path = parsed.path.strip("/")
    parts = path.split("/")

    # Detect pull request URLs explicitly
    if len(parts) >= 4 and parts[2].lower() == "pull":
        raise ValueError(
            "The provided URL points to a pull request, not a regular issue. "
            "Please provide an issue URL (e.g., https://github.com/owner/repository/issues/123)."
        )

    # Expected pattern: {owner}/{repo}/issues/{issue_number}
    pattern = r"^([^/]+)/([^/]+)/issues/(\d+)$"
    match = re.match(pattern, path)

    if not match:
        raise ValueError(
            "Invalid GitHub issue URL format. "
            "Expected format: https://github.com/owner/repository/issues/123"
        )

    owner, repo, issue_number_str = match.groups()
    try:
        issue_number = int(issue_number_str)
    except ValueError as exc:
        raise ValueError(f"Invalid issue number: {issue_number_str}") from exc

    return owner, repo, issue_number


def get_headers(token: str | None = None) -> dict[str, str]:
    """Construct standard GitHub REST API headers with optional authentication."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Issue-to-First-PR-Guide",
    }

    auth_token = (token or os.getenv("GITHUB_TOKEN", "")).strip()
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    return headers


def github_get(
    endpoint: str,
    token: str | None = None,
    params: dict | None = None,
) -> dict | list:
    """Send a GET request to the GitHub REST API with error handling and timeouts."""
    clean_endpoint = endpoint.lstrip("/")
    url = f"{GITHUB_API}/{clean_endpoint}"
    headers = get_headers(token)

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "Request to GitHub API timed out. Please check your network connection and try again."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not connect to GitHub API: {exc}") from exc

    if response.status_code == 404:
        raise RuntimeError(
            "GitHub resource not found (HTTP 404). Check the repository and issue URL, "
            "and ensure the repository is public."
        )

    if response.status_code == 401:
        raise RuntimeError(
            "GitHub authentication failed (HTTP 401). Please verify your GITHUB_TOKEN."
        )

    if response.status_code in (403, 429):
        # Rate limit or forbidden
        rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
        if rate_limit_remaining == "0" or response.status_code == 429:
            raise RuntimeError(
                "GitHub API rate limit exceeded. "
                "Configure a personal GITHUB_TOKEN in your environment to increase rate limits."
            )
        raise RuntimeError(
            "GitHub API access was denied. Ensure the repository is public or provide a valid GITHUB_TOKEN."
        )

    if not response.ok:
        raise RuntimeError(
            f"GitHub API returned HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise RuntimeError("GitHub returned an invalid JSON response.") from exc


def get_issue(issue_url: str, token: str | None = None) -> dict:
    """Fetch an issue and return structured fields needed by the application."""
    owner, repo, issue_number = parse_issue_url(issue_url)

    data = github_get(f"repos/{owner}/{repo}/issues/{issue_number}", token=token)

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected response structure from GitHub issues API.")

    # GitHub issues API returns pull requests as issues with a 'pull_request' key
    if "pull_request" in data:
        raise ValueError(
            "The provided URL points to a pull request, not a regular issue."
        )

    labels = []
    for item in data.get("labels", []):
        if isinstance(item, dict) and "name" in item:
            labels.append(item["name"])
        elif isinstance(item, str):
            labels.append(item)

    body = data.get("body")
    if not body or not body.strip():
        body = "No issue description provided."

    return {
        "owner": owner,
        "repo": repo,
        "number": issue_number,
        "title": data.get("title", ""),
        "body": body,
        "state": data.get("state", "unknown"),
        "html_url": data.get("html_url", issue_url),
        "labels": labels,
    }


def get_readme(owner: str, repo: str, token: str | None = None) -> str:
    """Fetch the repository README content, returning a fallback string if unavailable."""
    try:
        data = github_get(f"repos/{owner}/{repo}/readme", token=token)
        if isinstance(data, dict) and "content" in data:
            content_encoded = data["content"]
            decoded_bytes = base64.b64decode(content_encoded)
            return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        # Gracefully fall back if README doesn't exist or decoding fails
        pass

    return "README unavailable."


def get_file_tree(
    owner: str,
    repo: str,
    token: str | None = None,
) -> tuple[list[str], str]:
    """Return all repository blob file paths and default branch name."""
    repo_data = github_get(f"repos/{owner}/{repo}", token=token)
    if not isinstance(repo_data, dict):
        raise RuntimeError("Failed to fetch repository information.")

    default_branch = repo_data.get("default_branch")
    if not default_branch:
        raise RuntimeError("Could not determine the repository's default branch.")

    branch_data = github_get(
        f"repos/{owner}/{repo}/branches/{default_branch}",
        token=token,
    )
    if not isinstance(branch_data, dict):
        raise RuntimeError("Failed to fetch default branch data.")

    commit_sha = branch_data.get("commit", {}).get("sha")
    if not commit_sha:
        raise RuntimeError("Could not determine latest commit SHA for default branch.")

    tree_data = github_get(
        f"repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1",
        token=token,
    )
    if not isinstance(tree_data, dict):
        raise RuntimeError("Failed to fetch repository file tree.")

    # Even if truncated, GitHub returns all entries parsed up to the limit
    tree_items = tree_data.get("tree", [])
    paths = [
        item["path"]
        for item in tree_items
        if isinstance(item, dict)
        and item.get("type") == "blob"
        and "path" in item
        and isinstance(item["path"], str)
    ]

    return paths, default_branch


def normalize_path(path: str) -> str:
    """Normalize file path for consistent matching across operating systems."""
    cleaned = path.strip().replace("\\", "/")
    # Remove leading ./ or /
    cleaned = re.sub(r"^\.?/+", "", cleaned)
    return cleaned


def filter_valid_files(
    suggested_files: list[dict],
    repo_files: list[str],
) -> list[dict]:
    """Filter AI-suggested files, preserving only those that actually exist in the repo file tree.

    Never trusts model-generated paths without strict verification against the repository tree.
    """
    if not suggested_files or not repo_files:
        return []

    # Build canonical lookup sets
    valid_exact = set(repo_files)
    valid_normalized = {normalize_path(p): p for p in repo_files}

    verified: list[dict] = []
    seen_paths: set[str] = set()

    for item in suggested_files:
        if not isinstance(item, dict):
            continue

        raw_path = item.get("path")
        reason = item.get("reason", "").strip()

        if not raw_path or not isinstance(raw_path, str):
            continue

        cleaned = normalize_path(raw_path)

        # Match exact or normalized
        matched_real_path = None
        if raw_path in valid_exact:
            matched_real_path = raw_path
        elif cleaned in valid_normalized:
            matched_real_path = valid_normalized[cleaned]

        if matched_real_path and matched_real_path not in seen_paths:
            seen_paths.add(matched_real_path)
            verified.append({
                "path": matched_real_path,
                "reason": reason or "Identified as relevant to the issue.",
            })

    return verified


# Extensions commonly associated with code/documentation for beginner PRs
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss",
    ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".rb",
    ".php", ".sh", ".bash", ".yml", ".yaml", ".json", ".toml", ".md",
    ".rst", ".txt", ".sql", ".dockerfile",
}

# Directories and files typically irrelevant for issue resolution
IGNORED_PATTERNS = [
    r"^\.git/",
    r"^\.github/workflows/",
    r"^node_modules/",
    r"^vendor/",
    r"^dist/",
    r"^build/",
    r"^__pycache__/",
    r"^\.pytest_cache/",
    r"\.egg-info/",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"poetry\.lock$",
    r"pnpm-lock\.yaml$",
    r"\.(png|jpg|jpeg|gif|svg|ico|webp|pdf|zip|tar|gz|exe|dll|so|dylib|woff|woff2|ttf|eot)$",
]


def select_candidate_files(
    all_files: list[str],
    issue_title: str = "",
    issue_body: str = "",
    max_files: int = 150,
) -> list[str]:
    """Select a clean, high-value candidate subset of repository files to feed to the LLM.

    Avoids blowing token context with binary/asset files while prioritizing
    files relevant to keywords in the issue title and description.
    """
    if len(all_files) <= max_files:
        # Check if we should still filter obvious noise
        cleaned = [
            f for f in all_files
            if not any(re.search(pat, f, re.IGNORECASE) for pat in IGNORED_PATTERNS)
        ]
        return cleaned if cleaned else all_files[:max_files]

    # Extract keywords from title and body
    combined_text = f"{issue_title} {issue_body}".lower()
    raw_tokens = re.findall(r"[a-z0-9_]{3,}", combined_text)
    keywords = set(raw_tokens) - {
        "the", "and", "this", "that", "with", "have", "from", "when", "then",
        "which", "what", "issue", "error", "problem", "please", "help", "repo",
    }

    scored_files: list[tuple[int, str]] = []

    for path in all_files:
        # Skip noise files
        if any(re.search(pat, path, re.IGNORECASE) for pat in IGNORED_PATTERNS):
            continue

        lower_path = path.lower()
        score = 0

        # Prioritize source extensions
        _, ext = os.path.splitext(lower_path)
        if ext in SOURCE_EXTENSIONS:
            score += 2

        # Keyword matching in filename or path components
        for kw in keywords:
            if kw in lower_path:
                score += 5

        # Root and shallow files often contain configs or core modules
        depth = path.count("/")
        if depth <= 2:
            score += 1

        scored_files.append((score, path))

    # Sort descending by score, tie-break by path length
    scored_files.sort(key=lambda x: (x[0], -len(x[1])), reverse=True)

    candidates = [path for _, path in scored_files[:max_files]]
    return candidates


def build_github_file_url(
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
) -> str:
    """Build a direct GitHub web link to a repository file on a specific branch."""
    clean_path = normalize_path(file_path)
    return f"https://github.com/{owner}/{repo}/blob/{branch}/{clean_path}"
