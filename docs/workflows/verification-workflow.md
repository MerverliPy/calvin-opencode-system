# Verification Workflow

## Purpose

This workflow defines the baseline checks for Calvin's opencode operating system repository.

## Primary Command

~~~~bash
./scripts/verify-opencode-os.sh
~~~~

## What It Checks

The verifier checks:

1. required source files exist
2. `.env` is absent
3. `.env.example` exists
4. all shell scripts pass `bash -n`
5. every discovered opencode agent is registered
6. every discovered opencode command is registered
7. every discovered opencode skill is registered
8. every registry path points to a real file
9. no generated `dist/` files are staged
10. the context pack generator still runs

## When To Run

Run verification:

- before committing workflow changes
- after renaming agents, commands, or skills
- after editing scripts
- after changing registries
- before opening a pull request

## Commit Policy

Do not commit generated `dist/` files unless explicitly requested.

The verifier is allowed to generate context-pack output during checks, but those files remain generated artifacts.
