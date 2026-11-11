# AI Code Review Agent

A lightweight AI agent that reviews a git diff or GitHub pull request and returns structured feedback on bugs, risks, missing tests, and style issues.

---

## What It Does

You point it at a code change - a local `git diff`, a GitHub PR URL, or a saved `.diff` file - and it returns a JSON report with four categories:

- **bugs** - logic errors or incorrect behaviour introduced by the change
- **risks** - security, performance, or reliability concerns
- **missing_tests** - scenarios or edge cases with no test coverage
- **style_issues** - naming, readability, or convention problems

---

## How It Was Built

**Model:** `nvidia/nemotron-3.5-super-vl-120b-a12b` via [NVIDIA NIM](https://build.nvidia.com) - free API, no credit card required.

**Framework:** No agent framework (LangChain, etc.) was used intentionally - the task is a single-turn review, so a direct API call is simpler and easier to explain.

**How it calls tools:**
1. `tools.py` fetches the diff - either via `subprocess` running `git diff HEAD`, or via the GitHub REST API (`application/vnd.github.v3.diff` accept header).
2. `agent.py` sends a system prompt + the diff to the model and asks for a strict JSON response.
3. `main.py` is the CLI that wires the two together and pretty-prints the result.

**All configuration lives in `.env`** - API key, base URL, and model name. Nothing is hardcoded in the source files. To switch models, change the single `MODEL=` line in `.env`.

**File layout:**
```
main.py          # CLI entry point
agent.py         # LLM call + JSON parsing
tools.py         # diff fetching (local git or GitHub PR)
sample.diff      # a ready-made diff for quick testing
.env             # API key, base URL, model name (not committed)
requirements.txt
```

---

## What Went Wrong and How It Was Handled

- **Model returns markdown-wrapped JSON.** Even with "return ONLY valid JSON" in the prompt, models sometimes wrap the output in ` ```json ``` ` fences. Fixed with a `.removeprefix` / `.removesuffix` strip before `json.loads`.
- **`json.JSONDecodeError` on rare hallucinations.** Added a fallback that returns `{"raw_response": ...}` so the program never crashes - the user still gets the model's text.
- **Model returning empty content.** Some NVIDIA NIM models return a `None` content field. Fixed by checking both `content` and `text` keys in the response, with an empty-string fallback and a clear error message.
- **GitHub API rate limits on unauthenticated requests.** The tool works without a token for public repos but can hit the 60 req/hr limit. Users can add a `GITHUB_TOKEN` header if needed.

---

## What I Would Do Next

1. **Add a `GITHUB_TOKEN` env var** to authenticate GitHub API calls and raise the rate limit to 5 000/hr.
2. **Stream the response** so large diffs give incremental output instead of a long wait.
3. **Per-file breakdown** - split the diff by file and review each one separately, then merge results, so the model isn't overwhelmed by large PRs.
4. **GitHub Actions integration** - run the agent automatically on every PR via a workflow file and post the feedback as a PR comment.
5. **Severity scoring** - add a `severity` field (low / medium / high) to each finding so reviewers can triage quickly.

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo_url> && cd codeAgent

# 2. Create and activate the virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Fill in your API key in .env
# Get a free key at https://build.nvidia.com
API_KEY=nvapi-your_actual_key_here
API_BASE=https://integrate.api.nvidia.com/v1
MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b

# 5. Run against the sample diff
python main.py --diff sample.diff

# 6. Run against a GitHub PR
python main.py https://github.com/owner/repo/pull/42

# 7. Run against your local uncommitted changes
python main.py
```

---

## Requirements

- Python 3.9+
- Free [NVIDIA NIM API key](https://build.nvidia.com)
