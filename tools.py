import subprocess
import requests


def get_local_diff() -> str:
    # run "git diff HEAD" as a shell command and capture its output
    # this returns all changes that haven't been committed yet
    result = subprocess.run(
        ["git", "diff", "HEAD"],
        capture_output=True, text=True
    )

    # if git itself errored (example: not a git repo), surface the error message
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr.strip()}")

    diff = result.stdout.strip()

    # if there are no changes, there is nothing to review
    if not diff:
        raise ValueError("No local diff found. Stage or commit some changes first.")

    return diff


def get_github_pr_diff(pr_url: str) -> str:
    # break the PR URL into parts so we can extract owner, repo, and PR number
    # example: https://github.com/owner/repo/pull/123
    # -> owner="owner", repo="repo", number="123"
    parts = pr_url.rstrip("/").split("/")

    try:
        pull_index = parts.index("pull")  # find where "pull" sits in the URL
        owner = parts[pull_index - 2]
        repo = parts[pull_index - 1]
        number = parts[pull_index + 1]
    except (ValueError, IndexError):
        raise ValueError(f"Could not parse GitHub PR URL: {pr_url}")

    # build the GitHub REST API endpoint for this PR
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

    # the special Accept header tells GitHub to return a raw .diff instead of JSON
    response = requests.get(api_url, headers={"Accept": "application/vnd.github.v3.diff"})

    if response.status_code != 200:
        raise RuntimeError(f"GitHub API error {response.status_code}: {response.text[:200]}")

    return response.text
