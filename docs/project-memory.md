# Project Memory

Use this file for durable repo-specific context.

## Architecture

- This repository is Calvin's private opencode operating system.
- It stores opencode agents, commands, skills, workflow templates, model-routing policy, setup notes, audit systems, and reusable guides.
- The main source directories are `.opencode/`, `docs/`, `templates/`, `registries/`, `configs/`, `benchmarks/`, and `scripts/`.

## Commands

- Generate the repository context pack and audit upload package:

  ~~~~bash
  ./scripts/opencode-os.sh audit-prep
  ~~~~

- Save an audit response into the repo:

  ~~~~bash
  ./scripts/opencode-os.sh save-audit path/to/audit-response.md --commit --push
  ~~~~

- Show current opencode OS status:

  ~~~~bash
  ./scripts/opencode-os.sh status
  ~~~~

- Generate only the context pack:

  ~~~~bash
  ./scripts/opencode-os.sh context-pack
  ~~~~

## Test Procedure

- Run shell syntax checks before committing script changes:

  ~~~~bash
  bash -n scripts/*.sh
  ~~~~

- Run the opencode OS verifier when available:

  ~~~~bash
  ./scripts/verify-opencode-os.sh
  ~~~~

## Coding Conventions

- Prefer small, reviewable, reversible changes.
- Use a branch for non-trivial workflow changes.
- Do not commit generated `dist/` files by default.
- Do not commit `.env`, API keys, tokens, credentials, local model files, or logs.
- Keep registries synchronized when adding or renaming agents, commands, or skills.

## Known Pitfalls

- Termius on iPhone should not rely on Windows clipboard automation.
- Windows Downloads copying is optional and should remain opt-in.
- The sensitive warning for `GITHUB_PERSONAL_ACCESS_TOKEN` is expected as a placeholder environment variable name, not a live token.
- Generated context packs can include script text that repeats section headings; duplicate heading grep results are not automatically a bug.

## Accepted Decisions

- `dist/` is generated output and should not be committed by default.
- `audit-prep` creates one upload package for ChatGPT or opencode.
- The Termius/iPhone workflow uses SFTP/file download for `dist/audit-requests/opencode-audit-upload.md`.
- GitHub MCP remains disabled unless explicitly needed.
- Playwright MCP remains disabled unless browser/UI automation is explicitly needed.

## Model Routing Notes

- Local models are suitable for scouting, summarization, docs drafting, test-output explanation, and low-risk analysis.
- Cloud/API models should be used for long-context reasoning, complex debugging, security review, final PR review, and architectural planning.
- The local host baseline is Windows 10 / WSL2 Ubuntu with Intel i7-9700K, 48 GB DDR4 RAM, and RTX 4070 12 GB VRAM.

## Phase 5 Agent/Skill Refinement

- Phase 5 refines existing agents and skills before adding new ones.
- Agents now emphasize project memory, existing workflows, verification, registry synchronization, Termius/iPhone-safe command patterns, and generated `dist/` hygiene.
- Skills now document update triggers for project memory, Termius/iPhone terminal safety, baseline verification with `./scripts/verify-opencode-os.sh`, context-pack budgeting, and local/cloud routing boundaries.
- Verification command for this repository remains:

  ~~~~bash
  ./scripts/verify-opencode-os.sh
  ~~~~

- Generated `dist/` files remain uncommitted by default.

## GitHub Localhost Multitool

- The GitHub multitool is a localhost-only utility under `tools/github-multitool/`.
- The MVP is read-only and uses GitHub CLI `gh` as the backend.
- Local config and logs are ignored:
  - `tools/github-multitool/config.json`
  - `tools/github-multitool/*.log`
- The smoke test command is:

  ~~~~bash
  tools/github-multitool/smoke-test.sh
  ~~~~

- Write tools must remain gated behind explicit confirmation.
- The server must bind only to `127.0.0.1` or `localhost`.

## Feature 1: PR Intelligence Dashboard

- Added `pr-dashboard` CLI command and `GET /prs/dashboard` server endpoint.
- Summarizes open PRs with risk classification (draft, needs_review, changes_requested, stale, merge_conflict, blocked, unknown_merge, ready) and recommended next actions.
- Uses `gh pr list --json` with expanded fields (mergeStateStatus, reviewDecision) and a 7-day staleness threshold.

## Feature 2: PR Readiness Score

- Added `pr-readiness` CLI command and `GET /pr/<number>/readiness` server endpoint.
- Computes a numeric readiness score (0–100) from PR metadata, merge state, review decision, check status, staleness (>14 days), high-risk file patterns, and base branch.
- Risk levels: low (85–100), medium (60–84), high (30–59), blocked (0–29).
- Includes blockers, warnings, scoring reasons, changed files list, and recommended next action.

## Feature 3: Local PR Review Pack Generator

- Added `pr-review-pack` CLI command.
- Generates a local Markdown review package under `dist/github-review-packs/pr-XXX-review-pack.md` (zero-padded 3-digit PR number).
- Reuses existing PR readiness scoring and file-risk classification from Feature 2.
- Uses `gh pr view --json` and `gh pr diff` (read-only backend).
- Review pack includes: summary, readiness, changed files, compact diff, risk assessment, verification commands, rollback notes, ChatGPT/opencode review prompt, and raw metadata appendix (secrets redacted).
- Output directory is gitignored; generated files are not staged.

## Feature 4: GitHub Actions Failure Explainer

- Added `runs-failed` CLI command and `GET /runs/failed` server endpoint.
- Added `run-explain` CLI command and `GET /run/<run_id>/explain` server endpoint.
- Lists failed GitHub Actions workflow runs with automatic failure classification.
- Classification uses lightweight pattern matching on log excerpts (shell syntax, test failure, dependency install, permission/token, workflow configuration, unknown).
- Uses `gh run list --status failure` for listing, `gh run view --json` for metadata, `gh run view --log-failed` for logs.
- Default log lines for `run-explain` is 80 (conservative); adjustable via `--log-lines`.
- Log output is redacted for sensitive patterns (token, secret, credential, password, cookie, authorization, bearer, GH_TOKEN, GITHUB_TOKEN).
- Safety: read-only, does not rerun/cancel/delete workflows, handles missing permissions gracefully.
- Smoke test includes safe fallback when no failed runs exist.

## Feature 5: Safe PR Creator

- Added `pr-create` CLI command — the first write-capable command, heavily gated and disabled by default.
- No server endpoint: POST /pr/create is deferred/disabled; server rejects all POST/PUT/DELETE with 405.
- Safety gates (all must pass before PR creation):
  1. `--confirm` flag is present (checked first for smoke-test validation).
  2. `allow_write_tools` is `true` in config (disabled by default).
  3. PR title is non-empty.
  4. Body file exists (`--body-file`).
  5. Repository is in the allowlist (enforced by `resolve_repo`).
  6. Current branch is not `main` or `master`.
  7. Working tree is clean (`git status --porcelain` empty).
  8. Head branch has commits ahead of base (`git rev-list --count`).
  9. Repository visibility guard passes (public repo warning, strict private).
- Prints a safe preview to stderr before executing `gh pr create`.
- Uses `gh pr create` via subprocess argument list (no `shell=True`).
- Never prints or stores tokens, credentials, or secret values.
- Smoke tests verify `--help`, refusal without `--confirm`, and refusal with write tools disabled.
- Server POST message updated to mention deferred `POST /pr/create`.


## Feature 6: PR Body Generator

- Added `pr-body` CLI command.
- Generates a local PR body Markdown file from commits, changed files, and verification context.
- Output is written to `dist/github-pr-bodies/pr-body-<branch>.md`.
- Sections: Summary, Changes, Verification, Risk, Rollback, Reviewer Notes.
- Read-only: uses local `git` commands only (no GitHub API calls).
- Refuses on `main`/`master` branches.
- Detects recent smoke test output to report verification status honestly.

## Feature 7: Branch Cleanup Advisor

- Added `branches-cleanup-plan` CLI command.
- Strictly read-only: identifies branches safe to delete but never deletes anything.
- Classifies branches into four categories:
  - `safe_to_delete_local`: local branches merged into default branch, no open PR.
  - `safe_to_delete_remote`: remote `origin/*` branches merged into default, no open PR.
  - `needs_manual_review`: unmerged branches, stale branches, or unknown merge status.
  - `do_not_delete`: default branch, `main`/`master`, current branch, branches with open PRs.
- Uses `git branch --format`, `git branch --merged`, `gh repo view --json defaultBranchRef`, and `gh pr list --json headRefName`.
- Produces suggested delete commands but never executes them.
  - Local: `git branch -d <branch>`
  - Remote: `git push origin --delete <branch>`
- Force-delete (`-D`) is excluded from safe commands.
- Returns stable JSON with `repository`, `default_branch`, `current_branch`, `generated_at`, and four classification arrays.
- Handles missing `gh` permissions gracefully.
- Uses subprocess argument lists (no `shell=True`).


## Feature 8: Issue-to-Branch Workflow

...existing content continues...

## Feature 9: Repo Visibility Guard

- Added `repo-guard` CLI command.
- Warns/blocks risky write operations when the repository is public.
- Config flags: `block_writes_on_public_repo` (default `true`), `allow_public_repo_write_override` (default `false`).
- `repo-guard` output includes: ok, repository, visibility, is_private, write_tools_enabled, block_writes_on_public_repo, allow_public_repo_write_override, write_tools_blocked, warnings, recommended_next_action.
- When repo is public and `block_writes_on_public_repo`=true, `write_tools_blocked` is true unless `allow_public_repo_write_override`=true.
- When repo is private, `write_tools_blocked` is false (unless other gates block).
- `pr-create` refuses when visibility guard blocks writes with message: "Repository visibility guard blocked write operation because repository is public."
- Read-only commands continue to work on public repos.
- Visibility guard is an additional gate on top of `allow_write_tools`, not a replacement.
- Public repo write override is marked as advanced/risky.

## Feature 10: Security Alerts Summary

- Added `security-summary` CLI command and `GET /security/summary` server endpoint.
- Summarizes GitHub security posture from read-only commands: repository visibility, default branch, branch protection status, open Dependabot alerts, open code scanning alerts, open secret scanning alerts, security workflow presence, recent security-related PRs, and risk summary.
- Uses `gh api` for security endpoints (`dependabot/alerts`, `code-scanning/alerts`, `secret-scanning/alerts`, `branches/.../protection`).
- Handles 401, 403, 404 from GitHub API gracefully — reports `unavailable` rather than crashing.
- 404 for branch protection → `protected: false`, status `not_protected_or_unavailable`.
- Secret scanning: only count/status/type metadata reported; never requests or prints secret values.
- Security workflows detected from local `.github/workflows/` files by scanning filenames and content for security-related keywords (security, codeql, dependabot, secret, scan, audit, vulnerability).
- Recent security PRs detected by filtering `gh pr list` titles, labels, and branch names for security-related terms.
- Risk levels: high (public + open secret/code scanning alerts), medium (public, no branch protection, APIs unavailable, no security workflows), low (private, protected, no alerts, workflows present), unknown (most checks unavailable).
- Unavailable data is reported as `unavailable` rather than treated as zero alerts, preventing false sense of security.
- Returns stable JSON output with `ok`, `repository`, `visibility`, `default_branch`, `branch_protection`, `alerts`, `security_workflows`, `recent_security_prs`, and `risk_summary`.
- Read-only: uses `gh repo view`, `gh api`, `gh pr list`, and local file reads.
- Smoke test validates output shape even when alert APIs are unavailable.
- Does not mutate GitHub.

## Feature 11: Branch Protection Inspector

- Added `branch-protection` CLI command and `GET /branch/<name>/protection` server endpoint.
- Inspects branch protection rules for any named branch via `gh api repos/.../branches/.../protection`.
- Returns stable JSON with all protection fields normalized (14 fields) regardless of API response.
- Handles 404 (no protection → `protected: false`, `raw_availability: not_protected_or_unavailable`) and 403 (permission denied → `protected: null`, `raw_availability: permission_denied_or_unavailable`) gracefully.
- Read-only: does not create, modify, or delete branch protection rules.
- Does not print tokens, credentials, or secret values.

## Feature 12: Terminal UI Dashboard

- Added `dashboard` CLI command — compact overview optimized for Termius/iPhone.
- Default output is narrow human-readable text with repository, visibility, default branch, open PR/issue counts, failed run count, branch protection status, security alert availability/count, repo guard summary, and prioritized recommended next action.
- `--json` flag produces stable JSON for agent/script consumption with fields: `ok`, `repository`, `visibility`, `default_branch`, `open_prs`, `open_issues`, `failed_runs`, `branch_protection`, `security_summary`, `repo_guard`, `recommended_next_action`, `warnings`.
- Aggregation helper `_aggregate_dashboard_data` reuses existing helpers: `_check_branch_protection` (Feature 10), `_check_alert_endpoint` (Feature 10), `_get_default_branch` (Feature 7).
- Handles missing permissions gracefully — reports `unavailable` rather than crashing when backend calls fail.
- Recommended next action priority: (1) public repo warning, (2) failed runs, (3) missing branch protection, (4) unavailable security APIs, (5) open alerts, (6) open PRs, (7) no active work.
- Strictly read-only: uses `gh repo view`, `gh pr list`, `gh issue list`, `gh run list`, `gh api`.
- Uses subprocess argument lists; never `shell=True`.
- Does not print tokens, credentials, or secret values.
