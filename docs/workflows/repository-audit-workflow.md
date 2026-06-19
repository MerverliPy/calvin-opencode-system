# Repository Audit Workflow

## Purpose

This workflow defines how Calvin's opencode operating system audits a repository using a generated context pack.

## Required Input

Use a generated context pack from:

~~~~bash
./scripts/build-context-pack.sh
~~~~

Expected output path:

~~~~text
dist/context-packs/calvin-opencode-system-context-pack.md
~~~~

## Audit Phases

### Phase 1 — Orientation

Identify the repository purpose, main directories, source-of-truth files, active workflows, missing documentation, stale documentation, and transitional files.

### Phase 2 — Structural Review

Evaluate whether the repository has a clear operating-system layout:

- .opencode/
- docs/
- templates/
- registries/
- configs/
- scripts/
- benchmarks/

Check for orphaned files, duplicate concepts, unclear naming, and misplaced assets.

### Phase 3 — opencode Review

Inspect agents, commands, skills, model routing, project instructions, reusable prompts, and registry coverage.

Every agent, command, and skill should have a clear purpose and registry entry.

### Phase 4 — Security and Hygiene Review

Check for secrets, tokens, credentials, unsafe .env handling, committed model files, large binary files, generated output committed by accident, and weak .gitignore coverage.

Do not expose secret values. Report only the file path, line number if known, and issue category.

### Phase 5 — Documentation Review

Evaluate README clarity, setup instructions, how-to guides, workflow documentation, hardware/model-routing docs, examples, and handoff quality.

### Phase 6 — Improvement Plan

Return recommendations in this order:

1. critical fixes
2. high-value quick wins
3. structural improvements
4. new agents, commands, and skills to create
5. documentation improvements
6. automation opportunities
7. longer-term roadmap

## Output Format

Use this structure:

~~~~markdown
# Repository Audit Report

## Executive Summary

## Current Strengths

## Critical Issues

## Quick Wins

## Structural Recommendations

## opencode Agent/Command/Skill Review

## Security and Hygiene Review

## Documentation Review

## Recommended New Files

## Prioritized Execution Plan

## Clarification Defaults
~~~~

## Clarification Defaults Pattern

Use short options and highlight the recommended answer:

| Question | Options | Recommended |
|---|---|---|
| What should we fix first? | A. Security / B. Docs / C. Agents | **A** |

## Operating Rule

Prefer small, reviewable, reversible changes.

Do not recommend committing generated context packs unless explicitly requested.
