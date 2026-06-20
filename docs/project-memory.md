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
