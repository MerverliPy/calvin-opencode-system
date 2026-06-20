# GitHub Localhost Multitool

## Purpose

This tool provides a localhost-only GitHub multitool for Calvin's opencode workflow.

It is intended to become a small local control layer over GitHub CLI commands, not a public bot.

## Backend

The initial backend should use the GitHub CLI:

~~~~bash
gh
~~~~

Authentication should be handled by GitHub CLI outside this repository.

Do not commit:

- tokens
- `.env`
- credentials
- GitHub personal access tokens
- generated logs containing secrets

## Planned Commands

Read-only first:

~~~~text
health
repo-status
prs-list
pr-view
pr-dashboard
issues-list
branches-list
runs-list
~~~~

Write commands later:

~~~~text
pr-create
pr-comment
pr-merge
branch-delete
~~~~

## Safety Model

The tool should:

- bind only to `127.0.0.1`
- use an approved repository allowlist
- avoid shell injection by passing command arguments as lists
- refuse unknown commands
- require confirmation for high-risk actions
- keep generated output out of `dist/` unless intentionally generated
- avoid storing sensitive information

## Status

Current status: design phase.

## Localhost Server

Start the read-only localhost server:

~~~~bash
python3 tools/github-multitool/server.py
~~~~

Example local requests:

~~~~bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/repo/status
curl http://127.0.0.1:8765/prs
curl http://127.0.0.1:8765/issues
curl http://127.0.0.1:8765/branches
curl http://127.0.0.1:8765/runs
curl http://127.0.0.1:8765/prs/dashboard
~~~~

The MVP server intentionally rejects POST, PUT, and DELETE requests.

## PR Intelligence Dashboard

Generate a read-only dashboard that summarizes open pull requests with risk
classification and recommended next actions:

~~~~bash
python3 tools/github-multitool/github_multitool.py pr-dashboard          # all open PRs, up to 50
python3 tools/github-multitool/github_multitool.py pr-dashboard --limit 10

# server endpoint:
curl http://127.0.0.1:8765/prs/dashboard
curl "http://127.0.0.1:8765/prs/dashboard?limit=10"
~~~~

The dashboard uses `gh pr list` and returns a JSON payload with:

- **prs**: normalized PR objects (number, title, state, draft, author,
  branches, timestamps, URL, merge state, review decision).
- **risk_levels**: per-PR risk tags — `draft`, `needs_review`,
  `changes_requested`, `stale`, `merge_conflict`, `blocked`,
  `unknown_merge`, or `ready`.
- **recommended_action**: a human-readable string suggesting the next step.
- **summary**: aggregate counts of each risk level across all open PRs.

### Risk Classifier Rules

| Condition                 | Risk Level          | Recommended Action                       |
|---------------------------|---------------------|------------------------------------------|
| Draft PR                  | `draft`             | Complete draft before requesting review  |
| No review decision        | `needs_review`      | Request or await review                  |
| Changes requested         | `changes_requested` | Address requested changes                |
| Review required           | `needs_review`      | Await review completion                  |
| Unknown merge state       | `unknown_merge`     | Check CI status and merge conflicts      |
| Dirty merge state         | `merge_conflict`    | Resolve merge conflicts                  |
| Blocked merge state       | `blocked`           | Unblock merge requirements               |
| Not updated in 7+ days    | `stale`             | Follow up or consider closing stale PR   |
| No risks detected         | `ready`             | Ready to merge                           |

## Smoke Test

Run the local smoke test:

~~~~bash
tools/github-multitool/smoke-test.sh
~~~~

The smoke test checks:

- Python syntax
- CLI health
- CLI repo status
- strict-private behavior
- localhost server startup
- server health endpoint
- server repo status endpoint
- server PR list endpoint
- server issues list endpoint
- server branches list endpoint
- server strict-private route behavior
- rejection of write HTTP methods
