# opencode System Audit Template

Use this template to audit Calvin's private opencode operating system repository from a generated context pack.

## Input

Paste or upload the latest generated context pack:

~~~~text
dist/context-packs/calvin-opencode-system-context-pack.md
~~~~

## Audit Request

Analyze this repository context pack and produce a complete repository audit.

Focus on:

1. repository structure
2. .opencode agents, commands, and skills
3. reusable workflow templates
4. registries
5. documentation clarity
6. local model routing assumptions
7. security hygiene
8. missing automation
9. opportunities for new agents, commands, skills, and integrations

## Required Output

Use this report structure:

~~~~markdown
# Repository Audit Report

## Executive Summary

## Current Strengths

## Critical Issues

## Quick Wins

## Structural Recommendations

## opencode Agent Review

## opencode Command Review

## opencode Skill Review

## Security and Hygiene Review

## Documentation Review

## Recommended New Files

## Prioritized Execution Plan

## Clarification Defaults
~~~~

## Recommended New Files Table

| File | Purpose | Priority |
|---|---|---|

## Constraints

- Keep recommendations specific.
- Prefer small commits.
- Do not invent files that are not visible in the context pack.
- Separate confirmed findings from assumptions.
- Treat generated files as non-source unless the repo intentionally tracks them.
