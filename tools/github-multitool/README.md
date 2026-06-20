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
~~~~

The MVP server intentionally rejects POST, PUT, and DELETE requests.

## Smoke Test

Run the local smoke test:

~~~~bash
tools/github-multitool/smoke-test.sh
~~~~

The smoke test checks:

- Python syntax
- CLI health
- localhost server health
- read-only repo status endpoint
