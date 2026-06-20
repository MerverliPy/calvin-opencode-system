# GitHub Localhost Multitool Workflow

## Purpose

The GitHub localhost multitool is a local-only assistant utility for working with GitHub repositories through a safer command wrapper.

It is designed for Calvin's WSL2 / Termius / opencode workflow.

## Core Principles

- Bind to `127.0.0.1` only.
- Prefer GitHub CLI `gh` as the backend.
- Do not store GitHub tokens in this repository.
- Do not expose the server publicly.
- Use an allowlist of approved repositories.
- Start read-only before enabling write tools.
- Require explicit confirmation for destructive or high-risk actions.
- Log tool names and outcomes, but never tokens or secrets.

## Initial MVP Scope

Read-only tools:

- repo status
- list pull requests
- view pull request metadata
- list issues
- list branches
- list workflow runs

Write tools, later and gated:

- create pull request
- comment on pull request
- merge pull request
- delete branch

## Risk Levels

| Level | Examples | Policy |
|---|---|---|
| Low | list PRs, show repo status, list issues | Allowed by default |
| Medium | create PR, add comment, create issue | Require clear user intent |
| High | merge PR, close issue, delete branch, edit secrets | Require explicit confirmation |
| Forbidden | token printing, credential exfiltration, public bind | Refuse |

## Recommended Local Flow

1. Start from a clean repo.
2. Run the opencode OS verifier.
3. Start the localhost bot bound to `127.0.0.1`.
4. Use read-only tools first.
5. Review generated commands before write actions.
6. Require confirmation for high-risk actions.

## Verification

Baseline repo verification remains:

~~~~bash
./scripts/verify-opencode-os.sh
~~~~

Future tool-specific checks should include:

~~~~bash
python3 tools/github-multitool/github_multitool.py health
python3 tools/github-multitool/github_multitool.py repo-status
~~~~


## Safe PR Creation Flow (Feature 5)

The `pr-create` command is the first write-capable tool. Follow this flow to create a PR safely:

### Step-by-step

1. **Generate or inspect the PR body.**
   Write a Markdown file describing the changes. For example:
   ```bash
   cat > /tmp/pr-body.md << 'EOF'
   ## Summary
   Brief description of the changes.

   ## Verification
   - [ ] Smoke test passes
   - [ ] verify-opencode-os.sh passes

   ## Risk
   Low
   EOF
   ```

2. **Verify your branch.**
   ```bash
   git status --short --branch
   git log --oneline origin/main..HEAD
   ```

3. **Run smoke test and verifier.**
   ```bash
   tools/github-multitool/smoke-test.sh
   ./scripts/verify-opencode-os.sh
   ```

4. **Enable write tools only intentionally.**
   Edit `tools/github-multitool/config.json` and set:
   ```json
   {
     "allow_write_tools": true
   }
   ```
   This must be done explicitly — write tools are disabled by default.

5. **Run pr-create with --confirm.**
   ```bash
   python3 tools/github-multitool/github_multitool.py pr-create \
     --title "Add feature" \
     --body-file /tmp/pr-body.md \
     --base main \
     --head current \
     --confirm
   ```
   The tool prints a preview to stderr before executing `gh pr create`.

6. **Disable write tools again after use.**
   ```bash
   # Edit config.json and set allow_write_tools back to false
   ```
   Or revert the config change. Keeping write tools enabled is not recommended
   for day-to-day read-only usage.

### Safety Gates Enforced

The command verifies all of these before executing:

| Gate | Check |
|------|-------|
| Write tools enabled | `allow_write_tools` is `true` |
| Explicit confirmation | `--confirm` flag present |
| Not on main/master | Current branch name checked |
| Clean working tree | `git status --porcelain` empty |
| Ahead of base | `git rev-list --count origin/main..HEAD` > 0 |
| Title present | `--title` is non-empty |
| Body file exists | `--body-file` points to a readable file |
| Repo allowlisted | Repository in `allowed_repositories` |
| Visibility guard | `warn_public_repositories` / `strict_private` |

### Post-Creation

After the PR is created:

1. Review the PR URL in the JSON output.
2. Run `pr-readiness <NUMBER>` to score the new PR.
3. Run `pr-review-pack <NUMBER>` to generate a review package.
4. Consider requesting a review from a human or AI reviewer.

