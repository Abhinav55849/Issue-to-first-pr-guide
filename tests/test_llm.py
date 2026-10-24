"""Unit tests for Gemma AI integration, prompt construction, and response validation."""

import json
from unittest.mock import MagicMock, patch

import pytest

from llm import (
    DEFAULT_GEMMA_MODEL,
    build_guide_prompt,
    extract_json_str,
    generate_contribution_guide,
    get_api_key,
    get_configured_model,
    get_gemma_client,
    parse_and_validate_response,
    verify_model_availability,
)


def test_get_api_key_missing(monkeypatch):
    """Test that missing GEMMA_API_KEY raises a descriptive ValueError."""
    monkeypatch.delenv("GEMMA_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Gemma API key is not configured"):
        get_api_key(None)


def test_get_api_key_from_env(monkeypatch):
    """Test retrieving API key from environment variable."""
    monkeypatch.setenv("GEMMA_API_KEY", "test-gemma-key-12345")
    assert get_api_key(None) == "test-gemma-key-12345"


def test_get_api_key_from_arg():
    """Test retrieving API key passed directly as argument."""
    assert get_api_key("custom-key-789") == "custom-key-789"


def test_get_configured_model(monkeypatch):
    """Test model configuration resolution."""
    monkeypatch.delenv("GEMMA_MODEL", raising=False)
    assert get_configured_model(None) == DEFAULT_GEMMA_MODEL
    assert get_configured_model("gemma-2-27b-it") == "gemma-2-27b-it"

    monkeypatch.setenv("GEMMA_MODEL", "custom-gemma")
    assert get_configured_model(None) == "custom-gemma"


def test_build_guide_prompt_sanitization():
    """Test prompt construction includes isolated untrusted sections and candidate files."""
    issue_data = {
        "owner": "owner",
        "repo": "repo",
        "number": 99,
        "title": "Fix crash on null input",
        "body": "When input is null, it throws NullPointerException.",
        "state": "open",
        "labels": ["bug", "help wanted"],
    }
    readme = "# My Project\nUseful docs"
    candidates = ["src/core.py", "src/parser.py", "tests/test_core.py"]

    prompt = build_guide_prompt(issue_data, readme, candidates)

    assert "<untrusted_issue_data>" in prompt
    assert "</untrusted_issue_data>" in prompt
    assert "Issue #99: Fix crash on null input" in prompt
    assert "When input is null, it throws NullPointerException." in prompt
    assert "<untrusted_readme>" in prompt
    assert "<candidate_file_paths>" in prompt
    assert "- src/core.py" in prompt
    assert "- src/parser.py" in prompt


def test_extract_json_str_variations():
    """Test JSON string extraction from raw text and markdown fences."""
    # Plain JSON
    plain = '{"key": "value"}'
    assert extract_json_str(plain) == plain

    # Inside ```json block
    with_fence = 'Here is the guide:\n```json\n{"key": "value"}\n```\nHope it helps!'
    assert extract_json_str(with_fence) == '{"key": "value"}'

    # Inside ``` block without json specifier
    with_fence_no_lang = '```\n{"key": "value"}\n```'
    assert extract_json_str(with_fence_no_lang) == '{"key": "value"}'

    # With surrounding commentary and no backticks
    commentary = 'Certainly! The answer is: {"key": "value"} - thank you!'
    assert extract_json_str(commentary) == '{"key": "value"}'


def test_parse_and_validate_response_valid():
    """Test successful parsing and validation of a compliant model response."""
    raw_payload = {
        "summary": "This issue is about handling null values gracefully in the parser.",
        "likely_files": [
            {"path": "src/parser.py", "reason": "Contains parse_input where null check is missing"},
            {"path": "tests/test_parser.py", "reason": "Add test case for null input"},
        ],
        "steps": [
            "Fork and clone repository",
            "Reproduce null input crash in tests/test_parser.py",
            "Add if val is None guard in src/parser.py",
            "Run test suite",
        ],
        "pr_title": "fix(parser): prevent crash on null input",
        "pr_description": "## Problem\nNull inputs caused crash.\n\n## Solution\nAdded check.",
    }

    result = parse_and_validate_response(json.dumps(raw_payload))

    assert result["summary"] == raw_payload["summary"]
    assert len(result["likely_files"]) == 2
    assert result["likely_files"][0]["path"] == "src/parser.py"
    assert len(result["steps"]) == 4
    assert result["pr_title"] == "fix(parser): prevent crash on null input"
    assert "## Problem" in result["pr_description"]


def test_parse_and_validate_response_empty():
    """Test that empty or whitespace responses raise ValueError."""
    with pytest.raises(ValueError, match="empty or blank response"):
        parse_and_validate_response("")

    with pytest.raises(ValueError, match="empty or blank response"):
        parse_and_validate_response("   \n\t  ")


def test_parse_and_validate_response_malformed_json():
    """Test that malformed JSON raises ValueError."""
    with pytest.raises(ValueError, match="Failed to parse model response as JSON"):
        parse_and_validate_response("{broken: json, missing quotes}")


def test_parse_and_validate_response_missing_fields():
    """Test that missing required fields raise ValueError."""
    incomplete = {
        "summary": "Some summary",
        # missing likely_files, steps, pr_title, pr_description
    }
    with pytest.raises(ValueError, match="missing required fields"):
        parse_and_validate_response(json.dumps(incomplete))


def test_parse_and_validate_response_empty_steps():
    """Test that an empty steps list is rejected."""
    bad_steps = {
        "summary": "Some summary",
        "likely_files": [],
        "steps": [],
        "pr_title": "fix: some bug",
        "pr_description": "some desc",
    }
    with pytest.raises(ValueError, match="must be a non-empty list"):
        parse_and_validate_response(json.dumps(bad_steps))


def test_verify_model_availability_success():
    """Test successful model verification."""
    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.name = "models/gemma-2-9b-it"
    mock_client.models.get.return_value = mock_model

    is_avail, msg = verify_model_availability(mock_client, "gemma-2-9b-it")
    assert is_avail is True
    assert "verified and ready" in msg


def test_verify_model_availability_not_found():
    """Test model verification when model is unavailable."""
    mock_client = MagicMock()
    mock_client.models.get.side_effect = Exception("404 Model not_found")

    is_avail, msg = verify_model_availability(mock_client, "nonexistent-model")
    assert is_avail is False
    assert "was not found" in msg


def test_verify_model_availability_permission_denied():
    """Test model verification with permission denied."""
    mock_client = MagicMock()
    mock_client.models.get.side_effect = Exception("403 Permission_denied")

    is_avail, msg = verify_model_availability(mock_client, "restricted-model")
    assert is_avail is False
    assert "Access denied" in msg


@patch("llm.get_gemma_client")
def test_generate_contribution_guide_success(mock_get_client):
    """Test end-to-end generate_contribution_guide with mock client response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "summary": "Fix broken query validation.",
        "likely_files": [{"path": "src/query.py", "reason": "Logic error in validation"}],
        "steps": ["Step 1: Check query.py", "Step 2: Run pytest"],
        "pr_title": "fix: query validation logic",
        "pr_description": "Fixes query validation bug.",
    })
    mock_client.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_client

    issue_data = {
        "owner": "owner",
        "repo": "repo",
        "number": 1,
        "title": "Bug",
        "body": "Crash",
        "state": "open",
        "labels": [],
    }

    result = generate_contribution_guide(
        issue_data,
        "README",
        ["src/query.py"],
        api_key="valid-mock-key",
    )

    assert result["summary"] == "Fix broken query validation."
    assert result["pr_title"] == "fix: query validation logic"
    assert len(result["likely_files"]) == 1


@patch("llm.get_gemma_client")
def test_generate_contribution_guide_quota_error(mock_get_client):
    """Test error handling when quota limit is hit."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("429 ResourceExhausted quota exceeded")
    mock_get_client.return_value = mock_client

    issue_data = {"owner": "owner", "repo": "repo", "number": 1, "title": "t", "body": "b"}

    with pytest.raises(RuntimeError, match="rate limit or quota exceeded"):
        generate_contribution_guide(issue_data, "README", ["src/a.py"], api_key="test-key")


@patch("llm.get_gemma_client")
def test_generate_contribution_guide_empty_response(mock_get_client):
    """Test handling when model returns an empty text response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = None
    mock_client.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_client

    issue_data = {"owner": "owner", "repo": "repo", "number": 1, "title": "t", "body": "b"}

    with pytest.raises(RuntimeError, match="empty response"):
        generate_contribution_guide(issue_data, "README", ["src/a.py"], api_key="test-key")
