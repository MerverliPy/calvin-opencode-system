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
