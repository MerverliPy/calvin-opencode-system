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
pr-create        ← available (gated, disabled by default)
pr-comment       ← planned
pr-merge         ← planned
branch-delete    ← planned
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



## Safe PR Creator (Feature 5)

The first write-capable command. Heavily gated and **disabled by default**.

### Usage

```bash
python3 tools/github-multitool/github_multitool.py pr-create \
  --title "Add feature" \
  --body-file /tmp/pr-body.md \
  --base main \
  --head current \
  --confirm
```

### Safety Gates

**The command refuses unless ALL of these conditions are met:**

| # | Gate | Refusal Message |
|---|------|-----------------|
| 1 | `allow_write_tools` is `true` in config | `Write tools are disabled. Set allow_write_tools=true in config to enable gated write commands.` |
| 2 | `--confirm` flag is present | `Refusing to create PR without --confirm.` |
| 3 | Current branch is not `main` or `master` | `Refusing to create PR from main branch.` |
| 4 | Working tree is clean (`git status --porcelain` empty) | `Refusing to create PR: working tree is not clean.` |
| 5 | Branch has commits ahead of base | `Refusing to create PR: head branch has 0 commits ahead of base.` |
| 6 | PR title is non-empty | `PR title must be non-empty.` |
| 7 | Body file exists (`--body-file`) | `Refusing to create PR: body file does not exist.` |
| 8 | Repository is in the allowlist | `Repository is not allowlisted.` |
| 9 | Repository visibility guard passes | Covered by `warn_public_repositories` / `strict_private` |

### Write Tools Are Disabled By Default

The config key `allow_write_tools` defaults to `false`. To enable gated write
commands, intentionally change it to `true`:

```json
{
  "allow_write_tools": true
}
```

**Recommendation:** Enable write tools only for the duration of the PR creation
operation, then disable them again.

### Safe PR Preview

Before executing `gh pr create`, the tool prints a preview to stderr:

```text
--- PR Preview ---
Repository:     MerverliPy/calvin-opencode-system
Title:          Add feature
Base:           main
Head:           feature-branch
Body file:      /tmp/pr-body.md
Commits ahead:  3
Current branch: feature-branch
--- Creating PR ---
```

### Expected Output

**Refusal (write tools disabled):**
```json
{
  "ok": false,
  "error": "Write tools are disabled. Set allow_write_tools=true in config to enable gated write commands."
}
```

**Refusal (no --confirm):**
```json
{
  "ok": false,
  "error": "Refusing to create PR without --confirm."
}
```

**Refusal (on main branch):**
```json
{
  "ok": false,
  "error": "Refusing to create PR from main branch."
}
```

**Success:**
```json
{
  "ok": true,
  "repository": "MerverliPy/calvin-opencode-system",
  "title": "Add feature",
  "base": "main",
  "head": "feature-branch",
  "url": "https://github.com/MerverliPy/calvin-opencode-system/pull/42",
  "write_action": "pr_create"
}
```

### Disposable Branch Testing

**Always test PR creation on a disposable branch**, never on `main` or a
production branch. Create a throwaway branch:

```bash
git checkout -b test-pr-create-disposable
echo "test" > /tmp/test-pr-body.md
# Enable write tools, then:
python3 tools/github-multitool/github_multitool.py pr-create \
  --title "TEST: disposable branch" \
  --body-file /tmp/test-pr-body.md \
  --base main \
  --head current \
  --confirm
```

Close the test PR immediately after verifying the command works.

### Server Endpoint

**POST /pr/create is deferred/disabled.** The CLI command (`pr-create`) works
when write tools are enabled, but the server does not expose a write endpoint.
All POST, PUT, and DELETE requests are rejected with HTTP 405.

### Security

- Does not store, read, or print GitHub tokens.
- Uses `gh` authentication boundary only.
- Runs `gh pr create` via subprocess argument list (no `shell=True`).
- Does not print credentials, cookies, or secret values.
- Body file is read from disk by `gh`, not by this tool.


## PR Body Generator (Feature 6)

Generate a local PR body Markdown file from commits, changed files, and available
verification context. The generated file can be reviewed and then used with
`pr-create --body-file`.

### Usage

```bash
python3 tools/github-multitool/github_multitool.py pr-body
```

### Example Output

```json
{
  "ok": true,
  "output_path": "/home/calvin/calvin-opencode-system/dist/github-pr-bodies/pr-body-feature-github-multitool-pr-body.md",
  "branch": "feature-github-multitool-pr-body",
  "base": "origin/main",
  "commit_count": 4,
  "changed_file_count": 5,
  "verification_detected": true
}
```

### Generated Output Location

Output files are written to `dist/github-pr-bodies/` with the naming convention:

```
dist/github-pr-bodies/pr-body-<branch-name>.md
```

Branch names with unsafe filename characters (anything other than alphanumeric,
hyphens, underscores, and dots) are sanitized by replacing unsafe characters
with hyphens.

Example:
- Branch: `feature-github-multitool-pr-body`
- Output: `dist/github-pr-bodies/pr-body-feature-github-multitool-pr-body.md`

### Generated File Sections

Each generated PR body Markdown file contains:

| Section          | Contents                                                        |
|------------------|-----------------------------------------------------------------|
| Summary          | Branch purpose derived from commit subjects and changed files   |
| Changes          | Commit list, changed file list, and compact diff stat           |
| Verification     | Commands to run before opening the PR, plus auto-detection note |
| Risk             | High-risk file analysis based on changed paths                  |
| Rollback         | Commands to abandon or revert the branch safely                 |
| Reviewer Notes   | Branch stats and a reusable review checklist                    |

### Safety

- Read-only: uses local `git` commands only (`git log`, `git diff`, `git branch`).
- Does not talk to GitHub API — uses only the local repository state.
- Refuses to generate on `main` or `master` branches.
- Generated files are in `dist/github-pr-bodies/` which is gitignored.
- Does not print tokens, credentials, or secret values.
- Uses subprocess argument lists (no `shell=True`).

### Using with pr-create

1. Generate the PR body:
   ```bash
   python3 tools/github-multitool/github_multitool.py pr-body
   ```
2. Review the generated file at the output path.
3. When satisfied, use it with `pr-create`:
   ```bash
   python3 tools/github-multitool/github_multitool.py pr-create      --title "Your PR title"      --body-file dist/github-pr-bodies/pr-body-<branch>.md      --head current      --confirm
   ```

### Verification Detection

The generator checks for recent smoke test output files (within 24 hours) to
detect whether local verification was run. If no evidence is found, the
Verification section includes a note:

> Not automatically verified by this generator. Run the commands below before
> opening the PR.

This ensures the generator is honest and never invents successful verification.

### Base Branch Resolution

- Compares against `origin/main` by default.
- Falls back to `main` if `origin/main` is unavailable (e.g., no remote
  configured or never fetched).
- Raises an error if neither base branch is available.



## Branch Cleanup Advisor (Feature 7)

Identify local and remote branches that are likely safe to delete, but **never
delete anything automatically**. This command is strictly advisory and
read-only.

### Usage

```bash
python3 tools/github-multitool/github_multitool.py branches-cleanup-plan
```

### Advisory Only

- This command **never deletes branches**.
- All suggested commands must be **reviewed and executed manually**.
- The tool classifies branches into four categories.

### Categories

| Category               | Meaning                                                              |
|------------------------|----------------------------------------------------------------------|
| `safe_to_delete_local` | Local branches merged into the default branch with no open PRs.     |
| `safe_to_delete_remote`| Remote branches (`origin/*`) merged into default with no open PRs.   |
| `needs_manual_review`  | Unmerged branches, stale branches, or branches with unknown status. |
| `do_not_delete`        | Default branch, current branch, `main`/`master`, or has open PR.    |

### Suggested Commands

Each entry in `safe_to_delete_local` and `safe_to_delete_remote` includes a
`suggested_command` field. **Never run these without review.**

- **Local delete**: `git branch -d <branch>`
- **Remote delete**: `git push origin --delete <branch>`

Force-delete variants (`-D`) are intentionally excluded from safe suggestions.

### Classification Rules

| Condition                                      | Classification         |
|------------------------------------------------|------------------------|
| Default branch (`main`, `master`, etc.)        | `do_not_delete`        |
| Current checked-out branch                     | `do_not_delete`        |
| Branch with an open pull request               | `do_not_delete`        |
| Merged into default branch, no open PR         | `safe_to_delete_local` |
| Remote merged into default, no open PR         | `safe_to_delete_remote`|
| Not merged, no open PR                         | `needs_manual_review`  |
| Remote merge state undetectable                | `needs_manual_review`  |

### Expected Output

```json
{
  "ok": true,
  "repository": "MerverliPy/calvin-opencode-system",
  "default_branch": "main",
  "current_branch": "feature-branch",
  "safe_to_delete_local": [
    {
      "branch": "old-merged-branch",
      "reason": "Merged into main and has no open PR.",
      "suggested_command": "git branch -d old-merged-branch"
    }
  ],
  "safe_to_delete_remote": [
    {
      "branch": "origin/old-merged-branch",
      "reason": "Remote branch appears merged into main and has no open PR.",
      "suggested_command": "git push origin --delete old-merged-branch"
    }
  ],
  "needs_manual_review": [],
  "do_not_delete": [
    {
      "branch": "main",
      "reason": "Default branch."
    }
  ],
  "generated_at": "2026-06-20T12:00:00.123456+00:00"
}
```

### Safety

- **Strictly read-only**: uses `git branch`, `gh repo view`, and `gh pr list`.
- Does not create, delete, push, or modify branches.
- Does not print tokens, credentials, or secret values.
- Handles missing `gh` permissions gracefully.
- Uses subprocess argument lists (no `shell=True`).



## Issue-to-Branch Workflow (Feature 8)

Turn a GitHub issue into a safe local branch plan. This command is **strictly advisory**
and read-only — it does not create branches, mutate issues, or execute any commands.

### Usage

```bash
python3 tools/github-multitool/github_multitool.py issue-plan <ISSUE_NUMBER>
```

### Example

```bash
python3 tools/github-multitool/github_multitool.py issue-plan 12
```

### Expected Output

```json
{
  "ok": true,
  "repository": "MerverliPy/calvin-opencode-system",
  "issue": {
    "number": 12,
    "title": "Add branch cleanup advisor",
    "state": "OPEN",
    "url": "https://github.com/...",
    "author": "username",
    "labels": ["enhancement"]
  },
  "recommended_branch_name": "issue-012-add-branch-cleanup-advisor",
  "risk": "medium",
  "risk_reasons": [
    "enhancement label indicates feature work"
  ],
  "first_commands": [
    "git checkout main",
    "git pull --ff-only origin main",
    "git checkout -b issue-012-add-branch-cleanup-advisor"
  ],
  "suggested_pr_title": "Resolve #12: Add branch cleanup advisor",
  "suggested_checklist": [
    "Confirm issue scope",
    "Create branch from updated main",
    "Implement the smallest complete change",
    "Run tools/github-multitool/smoke-test.sh",
    "Run ./scripts/verify-opencode-os.sh",
    "Open PR referencing issue #12"
  ],
  "warnings": []
}
```

### Branch Name Format

Branch names follow the convention:

```
issue-<zero-padded-number>-<slugified-title>
```

Examples:

- Issue 12, "Add branch cleanup advisor" → `issue-012-add-branch-cleanup-advisor`
- Issue 4, "Fix README links" → `issue-004-fix-readme-links`
- Issue 127, "Implement new feature" → `issue-127-implement-new-feature`

Rules:
- Issue number is zero-padded to 3 digits.
- Title is lowercased with unsafe characters replaced by hyphens.
- Repeated hyphens are collapsed.
- Total branch name is trimmed to 70 characters.
- If the title produces an empty slug, `fix` is used as the fallback.

### Risk Estimate

The tool estimates risk based on issue labels, title, and body content:

| Risk    | Triggers                                                                 |
|---------|--------------------------------------------------------------------------|
| `low`   | Documentation, typo, README, guide-only labels or title/body cues        |
| `medium`| Feature, enhancement, refactor labels or title/body cues                 |
| `high`  | Security, auth, workflow, CI, deploy, config, secret, token, production, or breaking-change cues |

Risk is determined as the **highest** matching level across labels and body text.
Labels take priority over title/body cues.

### Checklist

The suggested checklist adapts to issue labels:

| Label(s)                         | Extra Checklist Item                |
|----------------------------------|-------------------------------------|
| `documentation`, `docs`, `readme`| Update project-memory.md            |
| `security`, `token`, `auth`      | Run security audit review           |
| `workflow`, `ci`, `deploy`       | Validate workflow YAML syntax       |
| `bug`, `fix`                     | Add test to prevent regression      |

The base checklist always includes scope confirmation, branch creation, minimal
implementation, smoke test, verification, and PR creation steps.

### Warnings

The command may include warnings for:

- **Issue is closed** — verify the issue should be reopened before starting.
- **Issue body is empty** — the issue may lack sufficient context for implementation.
- **Very short slug** — the issue title produces a slug under 5 characters, making the branch name ambiguous.
- **High-risk labels** — labels matching security/auth/deploy/etc. patterns suggest extra scrutiny.

### Advisory Only — No Commands Executed

This command **never**:

- Creates a branch
- Assigns, edits, closes, comments on, or mutates the issue
- Executes `git checkout`, `git pull`, or any other commands

The `first_commands` array shows the suggested sequence for getting started.
**Review every command before running it manually.**

### Safety

- Read-only: uses `gh issue view --json` via subprocess argument lists (no `shell=True`).
- Does not create branches, mutate issues, or execute any git commands.
- Does not print tokens, credentials, or secret values.
- Handles missing `gh` permissions gracefully.
- Returns stable JSON output.

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
 - CLI pr-body generation (with safe fallback on main branch)
