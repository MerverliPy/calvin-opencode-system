# cost-guardian

Routing and budget agent. Picks the cheapest model that can safely do a task, escalates only when forced to, and tells you when to compact or start a new session.

Defined in `.opencode/agents/cost-guardian.md`. Read-only — has no `edit`, `write`, or `bash` permission.

## What it answers

Given a task, cost-guardian returns exactly one decision in this order:

1. Should this stay local-only (secrets, PII, sensitive data)?
2. Is this destructive / hard to revert (force-push, prod migration, secret rotation)?
3. Is the current session too noisy to keep using?
4. What is the right base tier (1–5)?
5. Does the task need the opencode harness (it usually does)?
6. Are we going to loop for many turns? Demote a tier.
7. Is this an interactive keystroke loop? Bias local.
8. Does this need an external Claude review? What type?
9. Are we late in the month on quota? Demote one tier for non-critical work.

Earlier steps override later ones. Steps 1 and 2 cannot be overridden for any reason, including cost.

## The five tiers

| Tier | Class | Typical model | Use for |
|------|-------|---------------|---------|
| 1 | local 12B | qwen2.5-coder, deepseek-coder | greps, single-file reads, docstrings, mechanical refactors |
| 2 | cheap cloud | DeepSeek V3 Flash | multi-file edits in one package, clear-spec feature work, tests |
| 3 | mid cloud | DeepSeek V3 Pro | cross-file refactor, ambiguous spec, real debugging |
| 4 | high cloud | ChatGPT Plus / Copilot Pro | planning, architecture, multi-package work, when cheaper tiers failed |
| 5 | reviewer only | Claude Pro (Sonnet / Opus) | pre-merge audit, security, architecture decisions — never the implementer |

## Output format

Every response ends with this block. Prose is capped at three sentences; the block is the answer.

```
VERDICT: <LOCAL ONLY | TIER N | REVIEW REQUIRED>
MODEL: <specific model name>
TIER: <1-5>
REASON: <one sentence citing the dominant axis that decided it>
REVIEW TYPE: <none | correctness | security | architecture | style>
REVIEWER MODEL: <specific reviewer model, or "n/a">
ESCALATE IF: <concrete failure signal>
COMPACT/NEW SESSION: <yes/no, ≤10-word why>
SENSITIVITY BLOCK: <yes/no>
```

If a gate conflicts with a later step, the earlier gate wins and the conflict is named in `REASON`.

## How to invoke

From the opencode TUI, dispatch as a subagent:

```text
/task subagent=cost-guardian "Route this: <your task description>"
```

The agent takes the task description, runs the cascade, and returns the verdict block. It does not edit files. You apply the routing decision yourself when you pick the model for the next step.

## Examples

**Local-routed read task.** No secrets, no destructive action, single grep:

```
VERDICT: TIER 1
MODEL: local:qwen2.5-coder-12b
TIER: 1
REASON: read-only grep task with no destructive action, local is sufficient.
REVIEW TYPE: none
REVIEWER MODEL: n/a
ESCALATE IF: task expands into modifying any of the matched call sites.
COMPACT/NEW SESSION: no, fresh query.
SENSITIVITY BLOCK: no
```

**Pre-merge auth audit with Claude as reviewer.** Auth-touching, pre-merge, irreversible post-merge blast radius:

```
VERDICT: REVIEW REQUIRED
MODEL: deepseek-v3-pro
TIER: 3
REASON: auth-touching pre-merge audit triggers reversibility + security review gates; Claude reviews, does not implement.
REVIEW TYPE: security
REVIEWER MODEL: claude-opus-4
ESCALATE IF: DeepSeek plan conflicts with Claude security review, or review flags a token-handling defect.
COMPACT/NEW SESSION: no, task is focused on one PR.
SENSITIVITY BLOCK: no
```

## Hard rules

- Step 1 (sensitivity) is absolute. Credentials, PII, customer data, or unreleased financials → `VERDICT: LOCAL ONLY`. No cloud model, no exceptions.
- Step 2 (reversibility) is absolute. Force-push, drop table, prod deploy, `rm -rf`, secret rotation, schema migration against prod, history rewrite, disabling a security control → escalate one tier and require a review step. No local. Demotions from step 9 do not apply.
- Claude Pro is **reviewer-only**. It must never appear as `MODEL` inside opencode.
- Implementation must happen in the opencode harness when shell, grep, glob, MCP, file edits, or tests are involved. Raw claude.ai or chatgpt.com is not a valid implementation model.
- The model must commit. No "it depends" without a tier number. No axis-listing without a verdict.

## Related

- `.opencode/agents/cost-guardian.md` — the agent definition (cascade, rules, examples)
- `docs/model-routing.md` — high-level model routing policy
- `docs/model-routing/local-model-routing.md` — local model selection rules
- `docs/project-memory.md` — recurring routing decisions worth remembering
