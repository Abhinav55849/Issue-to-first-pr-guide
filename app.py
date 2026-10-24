"""Issue-to-First-PR Guide

A professional developer tool that helps beginner open-source contributors
understand real GitHub issues and prepare to make their first pull request.
Built with Streamlit, GitHub REST API, and Gemma AI via google-genai.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import streamlit as st
from dotenv import load_dotenv

# Ensure local modules are accessible
sys.path.insert(0, os.path.dirname(__file__))

import github_utils
import llm

load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Issue-to-First-PR Guide",
    page_icon="🐙",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        div[data-testid="stToolbar"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# GitHub-inspired styling
GITHUB_CSS = """
<style>
/* Base Theme & Palette */
:root {
    --gh-bg: #0D1117;
    --gh-surface: #161B22;
    --gh-surface-subtle: #21262D;
    --gh-border: #30363D;
    --gh-text: #E6EDF3;
    --gh-text-secondary: #9198A1;
    --gh-green: #3FB950;
    --gh-green-bg: #238636;
    --gh-green-hover: #2EA043;
    --gh-blue: #58A6FF;
    --gh-purple: #8957E5;
    --gh-red: #F85149;
}

/* Background & Main Container */
.stApp {
    background-color: var(--gh-bg);
    color: var(--gh-text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
}

.block-container {
    max-width: 860px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
}

/* Header container */
.gh-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--gh-border);
    padding-bottom: 0.85rem;
    margin-bottom: 1.5rem;
}

.gh-header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.gh-header-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--gh-text);
    margin: 0;
    line-height: 1.2;
}

.gh-header-subtitle {
    font-size: 0.82rem;
    color: var(--gh-text-secondary);
    margin: 0;
}

.gh-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    background-color: rgba(63, 185, 80, 0.12);
    border: 1px solid rgba(63, 185, 80, 0.4);
    color: var(--gh-green);
    font-weight: 500;
}

.gh-status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--gh-green);
}

.gh-status-pill-warn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    background-color: rgba(210, 153, 34, 0.12);
    border: 1px solid rgba(210, 153, 34, 0.4);
    color: #D29922;
    font-weight: 500;
}

/* Surface Cards */
.gh-card {
    background-color: var(--gh-surface);
    border: 1px solid var(--gh-border);
    border-radius: 6px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
}

/* Issue Metadata Header */
.gh-issue-badge-open {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.6rem;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: 12px;
    background-color: #238636;
    color: #ffffff;
}

.gh-issue-badge-closed {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.6rem;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: 12px;
    background-color: #8957E5;
    color: #ffffff;
}

.gh-label-pill {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: 10px;
    background-color: var(--gh-surface-subtle);
    border: 1px solid var(--gh-border);
    color: var(--gh-text-secondary);
    margin-right: 0.35rem;
    margin-top: 0.25rem;
}

/* Section Headings */
.gh-section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--gh-text);
    border-bottom: 1px solid var(--gh-border);
    padding-bottom: 0.5rem;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.gh-section-num {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.85rem;
    color: var(--gh-blue);
    font-weight: 600;
}

/* File list card */
.gh-file-item {
    background-color: var(--gh-surface);
    border: 1px solid var(--gh-border);
    border-radius: 6px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.65rem;
}

.gh-file-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}

.gh-file-path {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.88rem;
    color: var(--gh-blue);
    text-decoration: none;
    font-weight: 500;
}

.gh-file-path:hover {
    text-decoration: underline;
}

.gh-file-badge {
    font-size: 0.72rem;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    background-color: rgba(63, 185, 80, 0.15);
    color: var(--gh-green);
    border: 1px solid rgba(63, 185, 80, 0.3);
}

.gh-file-reason {
    font-size: 0.85rem;
    color: var(--gh-text);
    margin: 0;
    line-height: 1.4;
}

/* Step list */
.gh-step-item {
    background-color: var(--gh-surface);
    border: 1px solid var(--gh-border);
    border-radius: 6px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.65rem;
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
}

.gh-step-badge {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--gh-green);
    background-color: rgba(63, 185, 80, 0.15);
    border: 1px solid rgba(63, 185, 80, 0.3);
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    flex-shrink: 0;
}

.gh-step-text {
    font-size: 0.88rem;
    color: var(--gh-text);
    line-height: 1.45;
}

/* Primary Button Styling */
div.stButton > button[kind="primary"] {
    background-color: var(--gh-green-bg) !important;
    color: #ffffff !important;
    border: 1px solid rgba(240, 246, 252, 0.1) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.25rem !important;
    transition: background-color 0.15s ease !important;
}

div.stButton > button[kind="primary"]:hover {
    background-color: var(--gh-green-hover) !important;
    border-color: rgba(240, 246, 252, 0.2) !important;
}

/* Secondary Button Styling */
div.stButton > button[kind="secondary"] {
    background-color: var(--gh-surface-subtle) !important;
    color: var(--gh-text) !important;
    border: 1px solid var(--gh-border) !important;
    border-radius: 6px !important;
}

div.stButton > button[kind="secondary"]:hover {
    background-color: var(--gh-surface) !important;
    border-color: var(--gh-text-secondary) !important;
}

/* Input Fields */
div[data-baseweb="input"] {
    background-color: var(--gh-bg) !important;
    border: 1px solid var(--gh-border) !important;
    border-radius: 6px !important;
}

div[data-baseweb="input"] input {
    color: var(--gh-text) !important;
}

/* Links */
a {
    color: var(--gh-blue) !important;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
</style>
"""
st.markdown(GITHUB_CSS, unsafe_allow_html=True)


def init_session_state() -> None:
    """Initialize application session state variables."""
    if "guide_data" not in st.session_state:
        st.session_state.guide_data = None
    if "issue_meta" not in st.session_state:
        st.session_state.issue_meta = None
    if "repo_files" not in st.session_state:
        st.session_state.repo_files = []
    if "default_branch" not in st.session_state:
        st.session_state.default_branch = "main"
    if "verified_files" not in st.session_state:
        st.session_state.verified_files = []
    if "url_input" not in st.session_state:
        st.session_state.url_input = ""


def render_header(api_key_configured: bool) -> None:
    """Render the compact GitHub-inspired application header."""
    status_html = (
        '<div class="gh-status-pill"><div class="gh-status-dot"></div>Ready</div>'
        if api_key_configured
        else '<div class="gh-status-pill-warn">⚠️ API Key Needed</div>'
    )

    header_html = f"""
    <div class="gh-header">
        <div class="gh-header-left">
            <svg height="24" viewBox="0 0 16 16" version="1.1" width="24" fill="#E6EDF3" aria-hidden="true">
                <path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path>
            </svg>
            <div>
                <p class="gh-header-title">Issue-to-First-PR Guide</p>
                <p class="gh-header-subtitle">Understand issues. Make your first contribution.</p>
            </div>
        </div>
        <div>{status_html}</div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_settings_drawer() -> tuple[str | None, str, str | None]:
    """Provide a clean, collapsed configuration drawer for API credentials and model choice."""
    env_key = os.getenv("GEMMA_API_KEY") or os.getenv("GEMINI_API_KEY")
    env_model = os.getenv("GEMMA_MODEL", llm.DEFAULT_GEMMA_MODEL)
    env_token = os.getenv("GITHUB_TOKEN", "")

    with st.expander("⚙️ Provider & API Configuration", expanded=not bool(env_key)):
        col1, col2 = st.columns([1, 1])
        with col1:
            gemma_key_input = st.text_input(
                "Gemma API Key",
                value=env_key if env_key else "",
                type="password",
                placeholder="AIzaSy...",
                help="Requires a Google GenAI API key. Configure via GEMMA_API_KEY in .env or enter here.",
            )
            model_input = st.text_input(
                "Gemma Model Identifier",
                value=env_model,
                placeholder="gemma-2-9b-it",
                help="Configurable model identifier (e.g., gemma-2-9b-it, gemma-2-27b-it).",
            )
        with col2:
            github_token_input = st.text_input(
                "GitHub Personal Token (Optional)",
                value=env_token,
                type="password",
                placeholder="ghp_...",
                help="Optional token to increase rate limit from 60 to 5,000 requests/hour.",
            )
            st.caption(
                "Public GitHub issues do not require a token. Your keys remain strictly "
                "local in this session and are never exposed or shared."
            )

    return (
        gemma_key_input.strip() if gemma_key_input else None,
        model_input.strip() if model_input else llm.DEFAULT_GEMMA_MODEL,
        github_token_input.strip() if github_token_input else None,
    )


def render_issue_summary(issue_meta: dict[str, Any]) -> None:
    """Render a compact GitHub-style repository and issue summary card."""
    owner = issue_meta["owner"]
    repo = issue_meta["repo"]
    number = issue_meta["number"]
    title = issue_meta["title"]
    state = issue_meta.get("state", "open").lower()
    html_url = issue_meta.get("html_url", "#")
    labels = issue_meta.get("labels", [])

    badge_class = "gh-issue-badge-open" if state == "open" else "gh-issue-badge-closed"
    state_label = "● Open" if state == "open" else "✓ Closed"

    labels_html = "".join(f'<span class="gh-label-pill">{lbl}</span>' for lbl in labels)
    if not labels_html:
        labels_html = '<span style="color: var(--gh-text-secondary); font-size: 0.8rem;">No labels</span>'

    card_html = f"""
    <div class="gh-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 0.5rem;">
            <div>
                <a href="https://github.com/{owner}/{repo}" target="_blank" style="font-size: 0.95rem; color: var(--gh-text-secondary); font-weight: 500;">
                    {owner} / <strong style="color: var(--gh-text);">{repo}</strong>
                </a>
            </div>
            <div>
                <span class="{badge_class}">{state_label}</span>
            </div>
        </div>
        <div style="font-size: 1.25rem; font-weight: 600; color: var(--gh-text); margin-bottom: 0.6rem;">
            {title} <span style="color: var(--gh-text-secondary); font-weight: 400;">#{number}</span>
        </div>
        <div style="margin-bottom: 0.75rem;">
            {labels_html}
        </div>
        <div style="font-size: 0.85rem; border-top: 1px solid var(--gh-border); padding-top: 0.6rem;">
            <a href="{html_url}" target="_blank">View original issue on GitHub ↗</a>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_guide_sections(
    guide: dict[str, Any],
    verified_files: list[dict[str, Any]],
    owner: str,
    repo: str,
    branch: str,
) -> None:
    """Render the 4 structured contribution guide sections."""
    # 01 — Issue Overview
    st.markdown(
        '<div class="gh-section-title"><span class="gh-section-num">01</span> Issue Overview</div>',
        unsafe_allow_html=True,
    )
    summary_text = guide.get("summary", "")
    st.markdown(
        f'<div class="gh-card" style="line-height: 1.6; font-size: 0.92rem;">{summary_text}</div>',
        unsafe_allow_html=True,
    )

    # 02 — Files to Investigate
    st.markdown(
        '<div class="gh-section-title"><span class="gh-section-num">02</span> Files to Investigate</div>',
        unsafe_allow_html=True,
    )

    if verified_files:
        st.caption(
            "Every file listed below has been verified against the fetched repository file tree."
        )
        for item in verified_files:
            file_path = item["path"]
            reason = item.get("reason", "Identified as relevant to the issue.")
            file_url = github_utils.build_github_file_url(owner, repo, branch, file_path)

            file_card_html = f"""
            <div class="gh-file-item">
                <div class="gh-file-header">
                    <a href="{file_url}" target="_blank" class="gh-file-path">📄 {file_path} ↗</a>
                    <span class="gh-file-badge">Verified in tree</span>
                </div>
                <p class="gh-file-reason">{reason}</p>
            </div>
            """
            st.markdown(file_card_html, unsafe_allow_html=True)
    else:
        st.info(
            "No specific repository files could be conclusively verified against the repository's "
            "file tree for this issue. You may need to explore the project structure manually."
        )

    # 03 — Recommended Steps
    st.markdown(
        '<div class="gh-section-title"><span class="gh-section-num">03</span> Recommended Steps</div>',
        unsafe_allow_html=True,
    )
    steps = guide.get("steps", [])
    if steps:
        for idx, step_desc in enumerate(steps, 1):
            clean_step = step_desc
            # Strip redundant prefix like "Step 1:" if present
            if clean_step.lower().startswith(f"step {idx}:"):
                clean_step = clean_step[len(f"step {idx}:") :].strip()

            step_html = f"""
            <div class="gh-step-item">
                <span class="gh-step-badge">Step {idx}</span>
                <div class="gh-step-text">{clean_step}</div>
            </div>
            """
            st.markdown(step_html, unsafe_allow_html=True)
    else:
        st.write("No steps provided.")

    # 04 — Pull Request Draft
    st.markdown(
        '<div class="gh-section-title"><span class="gh-section-num">04</span> Pull Request Draft</div>',
        unsafe_allow_html=True,
    )
    pr_title = guide.get("pr_title", "")
    pr_description = guide.get("pr_description", "")

    st.markdown("**Suggested PR Title**")
    st.code(pr_title, language="text")

    st.markdown("**Suggested PR Description**")
    st.code(pr_description, language="markdown")


def handle_example_click(example_url: str) -> None:
    """Populate input field with example URL."""
    st.session_state.url_input = example_url


def main() -> None:
    """Application main entry point and workflow orchestration."""
    init_session_state()

    configured_env_key = os.getenv("GEMMA_API_KEY") or os.getenv("GEMINI_API_KEY")
    api_key_override, target_model, github_token_override = render_settings_drawer()

    active_api_key = api_key_override or configured_env_key
    render_header(api_key_configured=bool(active_api_key))

    # If guide already generated, display results interface
    if st.session_state.guide_data and st.session_state.issue_meta:
        render_issue_summary(st.session_state.issue_meta)
        render_guide_sections(
            st.session_state.guide_data,
            st.session_state.verified_files,
            st.session_state.issue_meta["owner"],
            st.session_state.issue_meta["repo"],
            st.session_state.default_branch,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Analyze another issue", type="secondary"):
                st.session_state.guide_data = None
                st.session_state.issue_meta = None
                st.session_state.verified_files = []
                st.session_state.repo_files = []
                st.session_state.url_input = ""
                st.rerun()
        return

    # Main input interface
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem; text-align: left;">
            <h2 style="font-size: 1.75rem; font-weight: 600; margin-bottom: 0.35rem; color: #E6EDF3;">
                Find your path to a first PR.
            </h2>
            <p style="color: #9198A1; font-size: 0.95rem; line-height: 1.5; margin: 0;">
                Paste any public GitHub issue URL. We fetch real issue details and repository structure,
                then generate an actionable, verified contribution guide using Gemma AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Input form
    issue_url = st.text_input(
        "GitHub Issue URL",
        value=st.session_state.url_input,
        placeholder="https://github.com/owner/repository/issues/123",
        help="Paste a link to any public GitHub issue.",
    )

    col_btn, col_ex = st.columns([1, 2])
    with col_btn:
        generate_clicked = st.button("Generate Guide", type="primary")

    with col_ex:
        st.caption("Public GitHub issues are supported.")

    example_url = "https://github.com/pallets/flask/issues/5000"
    st.markdown(
        f"""
        <div style="margin-top: 0.5rem; font-size: 0.8rem; color: var(--gh-text-secondary);">
            Example: <code style="color: var(--gh-blue); background: transparent;">{example_url}</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if generate_clicked:
        if not issue_url or not issue_url.strip():
            st.error("Please enter a GitHub issue URL to continue.")
            return

        # Check credentials before starting
        if not active_api_key:
            st.error(
                "Gemma API credentials are not configured. "
                "Please configure GEMMA_API_KEY in your .env file or expand the "
                "'Provider & API Configuration' panel above to enter your key."
            )
            return

        # Validate URL
        try:
            owner, repo, issue_number = github_utils.parse_issue_url(issue_url)
        except ValueError as exc:
            st.error(str(exc))
            return

        # Perform analysis workflow with progress reporting
        with st.status("Analyzing issue & repository...", expanded=True) as status:
            try:
                # Step 1: Issue metadata
                status.update(label=f"Fetching issue #{issue_number} from {owner}/{repo}...")
                issue_meta = github_utils.get_issue(issue_url, token=github_token_override)

                # Step 2: README
                status.update(label="Retrieving repository README...")
                readme_text = github_utils.get_readme(owner, repo, token=github_token_override)

                # Step 3: File Tree & Default Branch
                status.update(label="Fetching repository file tree...")
                repo_files, default_branch = github_utils.get_file_tree(
                    owner, repo, token=github_token_override
                )

                # Step 4: Candidate Selection
                candidate_files = github_utils.select_candidate_files(
                    repo_files,
                    issue_title=issue_meta["title"],
                    issue_body=issue_meta["body"],
                    max_files=120,
                )

                # Step 5: Consult Gemma AI
                status.update(label=f"Consulting Gemma model ({target_model})...")
                guide = llm.generate_contribution_guide(
                    issue_data=issue_meta,
                    readme_text=readme_text,
                    candidate_files=candidate_files,
                    api_key=active_api_key,
                    model_name=target_model,
                )

                # Step 6: Verify file paths against real repository file tree
                status.update(label="Verifying suggested files against repository tree...")
                suggested_files = guide.get("likely_files", [])
                verified_files = github_utils.filter_valid_files(suggested_files, repo_files)

                # Save in session state
                st.session_state.guide_data = guide
                st.session_state.issue_meta = issue_meta
                st.session_state.repo_files = repo_files
                st.session_state.default_branch = default_branch
                st.session_state.verified_files = verified_files

                status.update(label="Guide generated successfully!", state="complete")
                st.rerun()

            except Exception as exc:
                status.update(label="Failed to generate guide", state="error")
                st.error(f"{exc}")


if __name__ == "__main__":
    main()
