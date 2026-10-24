# Issue-to-First-PR Guide

A focused developer tool that helps beginner open-source contributors understand real GitHub issues, explore relevant codebase files, and prepare their first Pull Request with confidence.

![GitHub Theme](https://img.shields.io/badge/UI-GitHub%20Dark%20Theme-161b22?style=flat&logo=github)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=flat&logo=streamlit)
![Gemma](https://img.shields.io/badge/AI-Gemma%202-purple?style=flat)
![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat)

---

## 💡 Overview

New open-source contributors often encounter overwhelming barriers: complex codebases, cryptic issue descriptions, and uncertainty about where to start or how to format a pull request.

**Issue-to-First-PR Guide** bridges this gap:
1. **Fetches real issue context**: Retrieves issue title, description, labels, and state from the GitHub REST API.
2. **Inspects the codebase**: Fetches the repository's README, default branch, and real git file tree.
3. **Generates an AI guide**: Prompts a configurable Gemma model (via `google-genai`) with isolated context and strict formatting instructions.
4. **Verifies suggested files**: Cross-checks model-suggested files against the actual fetched repository tree, discarding hallucinated paths.
5. **Delivers a structured 4-part plan**:
   - **01 — Issue Overview**: Problem explained in plain English.
   - **02 — Files to Investigate**: Verified repository file paths with direct links to GitHub.
   - **03 — Recommended Steps**: Step-by-step reproduction, coding, and verification instructions.
   - **04 — Pull Request Draft**: Ready-to-copy PR title and markdown description.

> **Note**: This tool does not automatically write code or open PRs. It acts as a transparent, pedagogical guide for human developers.

---

## 🛠️ Technology Stack

* **Python 3.10+**
* **Streamlit**: Fast, reactive developer UI styled with GitHub's dark palette (`#0D1117`, `#161B22`, `#30363D`, `#3FB950`).
* **GitHub REST API**: Official GitHub REST API (`requests`) for issues, READMEs, and git trees.
* **Google Gen AI Python SDK (`google-genai`)**: Official SDK for interacting with Gemma models.
* **python-dotenv**: Environment configuration.
* **pytest**: Unit and integration test suite with mocking.

---

## 📁 Project Structure

```
issue-to-pr-guide/
├── app.py              # Streamlit interface and application flow
├── github_utils.py     # GitHub API operations, URL validation, tree verification
├── llm.py              # Gemma client, prompt engineering, JSON validation
├── requirements.txt    # Project dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git exclusion rules
├── README.md           # Documentation and guides
└── tests/
    ├── conftest.py     # Pytest configuration and path resolution
    ├── test_github.py  # Unit tests for URL parsing & GitHub API
    └── test_llm.py     # Unit tests for Gemma integration & validation
```

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10 or higher.
* A free Google Gen AI API key for Gemma from [Google AI Studio](https://aistudio.google.com/).
* *(Optional)* A GitHub Personal Access Token (classic or fine-grained) to increase rate limits.

### 2. Installation

Navigate into the project directory and create a virtual environment:

```bash
cd issue-to-pr-guide

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` and set your credentials:

```dotenv
# Required: Google GenAI API key for Gemma
GEMMA_API_KEY=your_actual_api_key_here

# Optional: Configurable model (defaults to gemma-2-9b-it)
GEMMA_MODEL=gemma-2-9b-it

# Optional: GitHub token to increase API limits from 60 to 5,000 req/hr
GITHUB_TOKEN=
```

> **Security Note**: Never commit your `.env` file. It is excluded by `.gitignore`.

---

## 🖥️ Running the Application

Launch the Streamlit app:

```bash
streamlit run app.py
```

Once started, open your browser to the local URL (typically `http://localhost:8501`).

### How to Use:
1. Paste a public GitHub issue link (e.g., `https://github.com/pallets/flask/issues/5000`).
2. Click **Generate Guide**.
3. View the repository summary, plain-English overview, verified files to explore, step-by-step guidance, and ready-to-use PR draft.
4. Click **← Analyze another issue** when finished.

---

## 🧪 Running Automated Tests

The test suite thoroughly mocks external GitHub and GenAI API calls, requiring no live credentials to execute.

Run all tests with:

```bash
pytest tests -v
```

### Tested Capabilities:
* ✅ Valid GitHub issue URL parsing (standard, trailing slashes, fragments, query strings).
* ✅ Invalid URL handling (non-GitHub hosts, malformed formats).
* ✅ Explicit pull request URL rejection (`/pull/...`).
* ✅ Successful issue metadata extraction.
* ✅ GitHub HTTP 404, 401, 403, and 429 rate limit handling.
* ✅ Missing or unencoded README fallbacks.
* ✅ Default branch and recursive file-tree retrieval.
* ✅ Strict model-suggested path verification against the actual repository tree.
* ✅ Gemma prompt isolation and boundary containment against prompt injection.
* ✅ Model response validation, markdown codeblock extraction, and malformed JSON rejection.
* ✅ Missing credential detection and friendly error messaging.
* ✅ Model availability verification and API quota exhaustion handling.

---

## 🔒 Security & Reliability

* **Strict Path Verification**: Model suggestions are never displayed blindly. Every path is checked against the repository's fetched tree; non-existent suggestions are discarded.
* **Prompt Injection Defense**: Issue descriptions and README files are treated as untrusted data and wrapped in isolated boundaries (`<untrusted_issue_data>`, `<untrusted_readme>`).
* **Zero Code Execution**: Repository code is never downloaded or executed on the user's system.
* **Credential Protection**: Secrets and tokens are never printed in logs or displayed in client interfaces.
* **Graceful Degradation**: Handles truncated file trees, missing READMEs, and API rate limits without crashing.

---

## ⚠️ Limitations

* **Public Repositories**: Designed for public repositories. Private repositories require a configured `GITHUB_TOKEN` with repository read permissions.
* **Monorepos & Massive Trees**: GitHub limits recursive tree queries to 100,000 entries. For ultra-large monorepos, the candidate selector prioritizes the most relevant source files.
* **Rate Limits**: Unauthenticated GitHub requests are limited by GitHub to 60 requests/hour per IP. Add a `GITHUB_TOKEN` to unlock 5,000 requests/hour.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/improvement`.
3. Ensure all tests pass: `pytest tests -v`.
4. Commit your changes: `git commit -m "feat: improve guide parsing"`.
5. Open a Pull Request!
