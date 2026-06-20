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
pr-readiness
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

Current status: active development.

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
curl http://127.0.0.1:8765/pr/3
curl http://127.0.0.1:8765/pr/3/readiness
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

## CLI Usage

### PR Readiness Score

Compute a numeric readiness score (0-100) for a pull request:

~~~~bash
python3 tools/github-multitool/github_multitool.py pr-readiness <PR_NUMBER>
~~~~

Example:

~~~~bash
python3 tools/github-multitool/github_multitool.py pr-readiness 4
~~~~

Example output:

~~~~json
{
  "number": 4,
  "score": 86,
  "risk": "low",
  "blockers": [],
  "warnings": [
    "review decision unavailable"
  ],
  "scoring_reasons": [...],
  "changed_files": ["README.md", "docs/project-memory.md"],
  "recommended_next_action": "Run local verification and request review.",
  "ok": true
}
~~~~

#### Scoring signals

**Positive signals** (maintain score):
- PR is not a draft
- Merge state is clean (no conflicts)
- All checks passed
- Review approved
- No high-risk files changed
- Base branch is `main`

**Negative signals** (deductions):
- PR is a draft (-30)
- Merge conflicts or blocked (-30)
- Merge state unknown (-10)
- Changes requested in review (-15)
- Review decision unavailable (-5)
- Checks failed (-20+)
- Checks pending (-5)
- PR is stale (>14 days, -10)
- High-risk files changed (-10 per file, max -30)
- Base branch not `main` (-5)

#### Risk levels

| Score Range | Risk    |
|-------------|---------|
| 85 – 100    | low     |
| 60 – 84     | medium  |
| 30 – 59     | high    |
| 0 – 29      | blocked |

#### High-risk files

The following patterns are considered high-risk:

- `.github/workflows/`
- `tools/github-multitool/`
- `scripts/`
- `.opencode/`
- `package-lock.json`, `pyproject.toml`, `requirements.txt`
- `Dockerfile`, `docker-compose.yml`
- Paths containing: `secret`, `token`, `credential`, `auth`, `deploy`, `release`, `workflow`


### PR Review Pack Generator

Generate a local Markdown review package for a pull request that can be
handed to ChatGPT, opencode, or a manual reviewer:

~~~~bash
python3 tools/github-multitool/github_multitool.py pr-review-pack <PR_NUMBER>
~~~~

Example:

~~~~bash
python3 tools/github-multitool/github_multitool.py pr-review-pack 4
~~~~

Example output:

~~~~json
{
  "ok": true,
  "pr_number": 4,
  "output_path": "/home/calvin/calvin-opencode-system/dist/github-review-packs/pr-004-review-pack.md",
  "repository": "MerverliPy/calvin-opencode-system",
  "readiness_score": 86,
  "risk": "low",
  "changed_file_count": 3
}
~~~~

Generated files follow zero-padded 3-digit naming:
- PR 4 → `pr-004-review-pack.md`
- PR 27 → `pr-027-review-pack.md`
- PR 142 → `pr-142-review-pack.md`

#### Review Pack Structure

Each generated Markdown file contains:

| Section                   | Contents                                                        |
|---------------------------|-----------------------------------------------------------------|
| Summary                   | Title, author, branch, base branch, URL, state, draft, updated  |
| Readiness                 | Score, risk, blockers, warnings, recommended next action        |
| Changed Files             | File list with high-risk path flags                             |
| Diff Summary              | Compact diff stats and truncated diff (capped at 150 lines)     |
| Risk Assessment           | Risk-level explanation and risk signals breakdown               |
| Verification Commands     | Smoke test, verify-opencode-os.sh, git status commands          |
| Rollback Notes            | Commands to abandon or revert the branch safely                 |
| ChatGPT / opencode Prompt | Reusable review prompt with correctness, safety, and regression |
| Raw Metadata Appendix     | Compact JSON metadata (secrets redacted)                        |

Output files are written to `dist/github-review-packs/` which is gitignored.

#### Safety

- Read-only: uses `gh pr view` and `gh pr diff` only.
- Does not create, edit, merge, close, or delete PRs.
- Does not print tokens, credentials, or secret values.
- Metadata appendix redacts sensitive-looking keys.


## GitHub Actions Failure Explainer

Identify failed GitHub Actions workflow runs and get concise debugging guidance.

### List Failed Runs

List recent failed workflow runs with automatic failure classification:

~~~~bash
python3 tools/github-multitool/github_multitool.py runs-failed
python3 tools/github-multitool/github_multitool.py runs-failed --limit 10

# server endpoint:
curl http://127.0.0.1:8765/runs/failed
curl "http://127.0.0.1:8765/runs/failed?limit=10"
~~~~

Example output:

~~~~json
{
  "ok": true,
  "repository": "MerverliPy/calvin-opencode-system",
  "failed_runs": [
    {
      "database_id": 123456,
      "workflow_name": "Verify",
      "status": "completed",
      "conclusion": "failure",
      "branch": "main",
      "event": "push",
      "url": "https://github.com/...",
      "created_at": "2026-06-20T10:00:00Z",
      "updated_at": "2026-06-20T10:05:00Z",
      "probable_failure_class": "test failure",
      "recommended_local_command": "tools/github-multitool/smoke-test.sh",
      "next_debugging_step": "Inspect failed job logs with run-explain."
    }
  ],
  "total_count": 1
}
~~~~

### Explain a Failed Run

Get a detailed explanation and log excerpt for a specific failed run:

~~~~bash
python3 tools/github-multitool/github_multitool.py run-explain <RUN_ID>
python3 tools/github-multitool/github_multitool.py run-explain <RUN_ID> --log-lines 120

# server endpoint:
curl http://127.0.0.1:8765/run/<RUN_ID>/explain
curl "http://127.0.0.1:8765/run/<RUN_ID>/explain?log_lines=120"
~~~~

Example output:

~~~~json
{
  "ok": true,
  "repository": "MerverliPy/calvin-opencode-system",
  "run_id": 123456,
  "workflow_name": "Verify",
  "status": "completed",
  "conclusion": "failure",
  "probable_failure_class": "test failure",
  "recommended_local_command": "tools/github-multitool/smoke-test.sh",
  "next_debugging_step": "Run the matching local verification command and inspect the first failing test.",
  "log_excerpt": "...",
  "log_lines_returned": 80
}
~~~~

### Failure Classes

The tool automatically classifies failures using pattern matching on log output:

| Class                    | Patterns Matched                                              | Recommended Local Command                  |
|--------------------------|---------------------------------------------------------------|--------------------------------------------|
| `shell syntax`           | "syntax error", "unexpected token", "command not found"  | `bash -n <script>`                         |
| `test failure`           | "FAILED", "AssertionError", "pytest", "npm test"       | `tools/github-multitool/smoke-test.sh`     |
| `dependency install`     | "npm ERR!", "pip install", "Could not resolve"           | `pip install -r requirements.txt`          |
| `permission/token`       | "permission denied", "Bad credentials", "403", "401"   | `gh auth status`                           |
| `workflow configuration` | "Invalid workflow file", "mapping values are not allowed"  | `yamllint .github/workflows/`              |
| `unknown`                | No patterns matched                                           | `tools/github-multitool/smoke-test.sh`     |

### Safety

- Read-only: uses `gh run list`, `gh run view`, and `gh run view --log-failed`.
- Does not rerun, cancel, or delete workflow runs.
- Does not print tokens, credentials, or secret values.
- Log output is redacted before display.
- Sensitive patterns (token, secret, credential, password, cookie, authorization, bearer, GH_TOKEN, GITHUB_TOKEN) are filtered from log excerpts.


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
- CLI pr-readiness (with safe fallback when no open PRs)
- localhost server startup
- server health endpoint
- server repo status endpoint
- server PR list endpoint
- server PR readiness endpoint (with safe fallback)
- server issues list endpoint
- server branches list endpoint
- server strict-private route behavior
- rejection of write HTTP methods
