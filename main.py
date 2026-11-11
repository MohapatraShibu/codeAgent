import sys
import json
from tools import get_local_diff, get_github_pr_diff
from agent import review_diff

USAGE = """
Usage:
  python main.py                          # review local git diff
  python main.py <github_pr_url>          # review a GitHub pull request
  python main.py --diff <path_to_file>    # review a saved diff file
"""


def main():
    # step 1: Figure out where the diff is coming from

    if len(sys.argv) == 1:
        # no arguments - grab the diff from the local git repo
        print("Fetching local git diff...")
        diff = get_local_diff()

    elif sys.argv[1] == "--diff" and len(sys.argv) == 3:
        # diff flag - read the diff from a local file (e.g. sample.diff)
        with open(sys.argv[2], "r") as f:
            diff = f.read()

    elif sys.argv[1].startswith("https://github.com"):
        # GitHub PR URL - fetch the diff via the GitHub REST API
        print(f"Fetching GitHub PR diff from: {sys.argv[1]}")
        diff = get_github_pr_diff(sys.argv[1])

    else:
        # unrecognised input - show the help text and exit
        print(USAGE)
        sys.exit(1)

    # step 2: Show a short preview so the user knows what was picked up
    print(f"\n--- Diff preview (first 300 chars) ---\n{diff[:300]}\n")
    print("Sending diff to AI agent for review...\n")

    # step 3: Send the diff to the AI and get structured feedback
    feedback = review_diff(diff)

    # step 4: Pretty-print the JSON result
    print("=== Code Review Feedback ===\n")
    print(json.dumps(feedback, indent=2))

if __name__ == "__main__":
    main()
