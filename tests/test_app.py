"""Unit tests for Streamlit UI helper functions and rendering logic."""

from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

import app


def test_init_session_state():
    """Test initializing default session state."""
    # Clear session state
    for k in list(st.session_state.keys()):
        del st.session_state[k]

    app.init_session_state()

    assert st.session_state.guide_data is None
    assert st.session_state.issue_meta is None
    assert st.session_state.repo_files == []
    assert st.session_state.default_branch == "main"
    assert st.session_state.verified_files == []
    assert st.session_state.url_input == ""


def test_handle_example_click():
    """Test populating example URL into session state."""
    app.handle_example_click("https://github.com/pallets/flask/issues/5000")
    assert st.session_state.url_input == "https://github.com/pallets/flask/issues/5000"


@patch("app.st.markdown")
def test_render_header(mock_markdown):
    """Test header rendering with configured vs unconfigured API key."""
    app.render_header(api_key_configured=True)
    assert mock_markdown.called
    html_arg = mock_markdown.call_args[0][0]
    assert "Issue-to-First-PR Guide" in html_arg
    assert "Ready" in html_arg

    app.render_header(api_key_configured=False)
    html_arg = mock_markdown.call_args[0][0]
    assert "API Key Needed" in html_arg


@patch("app.st.markdown")
def test_render_issue_summary(mock_markdown):
    """Test rendering repository and issue summary card."""
    issue_meta = {
        "owner": "pallets",
        "repo": "flask",
        "number": 5000,
        "title": "Fix routing bug",
        "state": "open",
        "html_url": "https://github.com/pallets/flask/issues/5000",
        "labels": ["bug", "routing"],
    }
    app.render_issue_summary(issue_meta)
    assert mock_markdown.called
    html_arg = mock_markdown.call_args[0][0]
    assert "pallets" in html_arg
    assert "flask" in html_arg
    assert "Fix routing bug" in html_arg
    assert "#5000" in html_arg
    assert "Open" in html_arg
    assert "routing" in html_arg


@patch("app.st.code")
@patch("app.st.markdown")
def test_render_guide_sections(mock_markdown, mock_code):
    """Test rendering the 4 contribution guide sections."""
    guide = {
        "summary": "This is a detailed overview of the issue for beginners.",
        "likely_files": [{"path": "src/flask/app.py", "reason": "Routing logic is here"}],
        "steps": ["Step 1: Inspect app.py", "Step 2: Add test in tests/test_app.py"],
        "pr_title": "fix(routing): resolve edge-case in route matching",
        "pr_description": "## Problem\nRouting fails.\n\n## Solution\nFix logic.",
    }
    verified_files = [
        {"path": "src/flask/app.py", "reason": "Routing logic is here"}
    ]

    app.render_guide_sections(
        guide=guide,
        verified_files=verified_files,
        owner="pallets",
        repo="flask",
        branch="main",
    )

    assert mock_markdown.called
    assert mock_code.called
    # Check that PR title and PR description were rendered in code blocks
    code_calls = [c[0][0] for c in mock_code.call_args_list]
    assert guide["pr_title"] in code_calls
    assert guide["pr_description"] in code_calls
