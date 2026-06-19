# opencode System Audit 001

Saved: 2026-06-19T23:30:52Z

Repository branch: main

Repository commit at save time: cdbddb6

Source: /home/calvin/audit-response.md

---

Repository Audit Report

Executive Summary

The uploaded opencode-audit-upload.md is valid and contains the requested audit prompt plus a generated context pack for /home/calvin/calvin-opencode-system. The context pack was generated from main at commit cdbddb6, and it reports a clean included-path Git status.  

Overall, the repository is in a strong early-stage state. It now has the core pieces of a private opencode operating system:

* .opencode/agents/
* .opencode/commands/
* .opencode/skills/
* docs/
* templates/
* registries/
* automation scripts
* local model routing docs
* context-pack/audit-prep workflow

The main issue is not missing capability. The main issue is normalization: several useful parts exist, but they are not yet fully tied together into a single polished operating-system workflow. The next phase should focus on registry consistency, command naming, project memory, and documentation that explains the new Termius/iPhone workflow.

⸻

Current Strengths

1. The repository has a clear operating-system shape

The tree shows a coherent structure with .opencode, docs, templates, registries, configs, scripts, and benchmarks. The context pack reports 44 directories and 56 files, which is a healthy size for a private workflow system at this stage.  

2. Agent roles are well scoped

The existing agents have strong boundaries:

Agent	Strength
architect	Read-only planning with approval gate
implementer	Small reversible changes
reviewer	Diff review without editing
security-auditor	Secrets/security review
test-runner	Approved test execution only
local-scout	Cheap local read-only exploration
cost-guardian	Model/cost routing
memory-curator	Durable repo memory

This is a good foundational agent set. It avoids the common failure mode of one overpowered “do everything” agent.

3. Safety posture is strong

The repo has multiple layers of safety:

* .gitignore excludes secrets, local model files, logs, caches, build output, and generated dist/.
* .opencode/opencode.json defaults most actions to ask.
* destructive commands like rm, sudo, git reset --hard, and git clean are denied.
* skills include safe-terminal, sandbox-ladder, mcp-safety, dependency-security, and token-budget.

That is the right pattern for agentic coding.

4. Context-pack automation is now useful

The workflow now produces a single upload file:

dist/audit-requests/opencode-audit-upload.md

That is exactly the right design for Termius/iPhone usage. It reduces the workflow to:

./scripts/opencode-os.sh audit-prep

then uploading one Markdown file.

5. Local hardware assumptions are captured

The repo includes a detailed hardware profile and local model routing policy. The local machine is treated as a WSL2 workstation with RTX 4070 12 GB VRAM, 48 GB RAM, and practical 7B–14B quantized model support. That gives future agents a clear model-routing baseline.  

⸻

Critical Issues

No confirmed P0 issue appears in the context pack. I do not see an exposed live secret.

However, there are several P1/P2 structural issues that should be fixed before adding more agents.

P1 — Command naming is inconsistent

There are two audit-related commands:

.opencode/commands/repo-audit.md
.opencode/commands/audit-repo.md

The registry has repo-audit in the main table, then audit-repo appended as a separate section instead of as a normal registry row.  

This creates ambiguity:

Command	Current apparent role
repo-audit	General repo audit command
audit-repo	Context-pack audit command

That distinction is valid, but the names are too similar. One should be renamed or clearly differentiated.

Recommended fix: rename audit-repo conceptually to audit-context-pack, or merge it into repo-audit.

P1 — .env.example appears expected but absent from included files

The build script includes .env.example as an include target, and .gitignore explicitly allows .env.example, but the context pack’s included file list does not show .env.example.  

This means the repo likely lacks a safe environment template.

Recommended fix: add:

.env.example

with placeholder-only values for GitHub MCP, local model hosts, and optional APIs.

P1 — docs/project-memory.md is still empty scaffold

docs/project-memory.md exists but all sections are still Pending. That weakens future handoffs because the repo now has real durable decisions:

* Termius/iPhone default workflow
* generated dist/ should not be committed
* context pack workflow
* audit-prep workflow
* save-audit workflow
* command-router workflow
* local/cloud model routing assumptions

Recommended fix: populate docs/project-memory.md immediately.

P2 — README does not yet document the new automation workflow

README.md explains the repository’s purpose, but it does not yet explain the new high-value commands:

./scripts/opencode-os.sh audit-prep
./scripts/opencode-os.sh save-audit path/to/audit-response.md --commit --push
./scripts/opencode-os.sh status

The automation exists, but a future user or future agent may not know the canonical path.

Recommended fix: add a “Daily Workflow” or “Termius/iPhone Workflow” section.

P2 — configs/, templates/, and docs/how-to-guides/ directories exist but are underdeveloped

The tree shows the intended structure, but many folders are placeholders. That is acceptable early, but the next growth phase should add at least one canonical guide per major workflow.

⸻

Quick Wins

These are the highest return fixes.

Fix	Why it matters	Effort
Add .env.example	Reduces secret/config confusion	Low
Normalize command-registry.md	Makes command discovery cleaner	Low
Add docs/project-memory.md content	Improves future sessions immediately	Low
Add README section for opencode-os.sh	Makes automation discoverable	Low
Add docs/how-to-guides/termius-iphone-workflow.md	Matches your actual coding environment	Medium
Add docs/audits/README.md before first saved audit	Makes audit history first-class	Low
Add scripts/verify-opencode-os.sh	One command to validate repo hygiene	Medium

⸻

Structural Recommendations

1. Establish a canonical command taxonomy

Use this structure:

.opencode/commands/
├── repo-audit.md              # general repo audit
├── context-pack-audit.md      # audit from generated context pack
├── plan-feature.md
├── implement-phase.md
├── review-diff.md
├── security-audit.md
├── cost-check.md
├── local-benchmark.md
├── model-router.md
├── sandbox-start.md
└── memory-update.md

Either rename:

audit-repo.md -> context-pack-audit.md

or merge it into:

repo-audit.md

My recommendation: rename to context-pack-audit.md because it describes the actual function more precisely.

2. Create a first-class workflow docs layer

Recommended:

docs/workflows/
├── repository-audit-workflow.md
├── context-pack-workflow.md
├── termius-iphone-workflow.md
├── save-audit-workflow.md
└── implementation-phase-workflow.md

The current repo has only repository-audit-workflow.md. That is not enough to explain the new automation system.

3. Convert placeholder directories into purposeful directories

Right now several directories exist, but their purpose is not yet captured in local README files.

Add lightweight README.md files:

configs/README.md
templates/README.md
benchmarks/README.md
docs/how-to-guides/README.md
docs/decisions/README.md

Each should be short. The goal is not long documentation; the goal is orientation.

4. Add a verification script

Create:

scripts/verify-opencode-os.sh

It should check:

1. shell syntax for scripts/*.sh
2. required files exist
3. .env is absent
4. .env.example exists
5. dist/ is not staged
6. every .opencode/agent has a registry entry
7. every .opencode/command has a registry entry
8. every .opencode/skill has a registry entry
9. context pack can be generated

This will reduce manual checking.

⸻

opencode Agent Review

Confirmed existing agents

The context pack includes 9 agents:

architect
cost-guardian
docs-writer
implementer
local-scout
memory-curator
reviewer
security-auditor
test-runner

These are all registered in registries/agent-registry.md.  

Evaluation

The core agent set is good. Do not add too many agents yet. First, make existing agent behavior more operational.

Recommended improvements

Agent	Recommendation
architect	Add explicit instruction to check docs/project-memory.md before planning
implementer	Add instruction to run scripts/verify-opencode-os.sh when modifying repo infrastructure
docs-writer	Add instruction to update relevant registry or README when adding docs
memory-curator	Add explicit trigger: update after commits that change workflows/scripts/commands
security-auditor	Add context-pack sensitive-warning review instruction
local-scout	Add Termius/WSL2 constraints and avoid Windows GUI assumptions
test-runner	Add shell-script syntax check and dry-run verification pattern

New agents to add later

Do not add all of these now. Add after the registry/docs cleanup.

Agent	Purpose	Priority
workflow-operator	Runs repeatable repo OS workflows and reports state	Medium
registry-maintainer	Keeps agents/commands/skills registries synchronized	Medium
context-pack-curator	Optimizes what is included/excluded from context packs	Low
mobile-workflow-advisor	Optimizes Termius/iPhone workflows	Low

⸻

opencode Command Review

Confirmed existing commands

The repo includes commands for audit, planning, implementation, review, security, PR summaries, cost checks, local benchmarking, model routing, sandboxing, and memory updates.  

Main issue

Command coverage is good, but command naming and registry format need cleanup.

Command-specific findings

Command	Finding	Recommendation
repo-audit.md	Good general audit command	Keep
audit-repo.md	Overlaps with repo-audit.md	Rename to context-pack-audit.md or merge
model-router.md	Useful, but could refer to hardware profile explicitly	Add reference to docs/model-routing/local-model-routing.md
memory-update.md	Useful, but project memory is empty	Populate memory first
sandbox-start.md	Good concept	Add Termius/WSL2 notes
local-benchmark.md	Good	Add output capture path convention
cost-check.md	Useful	Tie to token-budget skill
review-diff.md	Good	Add “do not claim tests passed” rule, matching PR summary
security-audit.md	Good	Add sensitive-pattern report review

Registry cleanup

audit-repo should be moved into the main command table rather than appended as a separate section.

⸻

opencode Skill Review

Confirmed existing skills

The repo includes:

dependency-security
github-pr
local-model-routing
mcp-safety
project-memory
safe-terminal
sandbox-ladder
test-runner
token-budget

These are all registered.  

Evaluation

This is a strong skill set. The most important missing piece is not another skill; it is cross-linking.

Recommended skill improvements

Skill	Improvement
project-memory	Add exact update conditions and examples
token-budget	Add context-pack upload guidance
safe-terminal	Add Termius/iPhone caution: avoid huge terminal output unless requested
sandbox-ladder	Add “Git worktree for experimental agent changes”
mcp-safety	Add note that GitHub MCP remains disabled unless a task requires it
local-model-routing	Link explicitly to hardware profile and benchmark script
test-runner	Include bash -n scripts/*.sh as baseline check

⸻

Security and Hygiene Review

Confirmed findings

The context pack reports one sensitive-pattern warning: a GitHub token environment-variable placeholder in the GitHub MCP configuration. The context pack states sensitive warnings can be false positives when they refer to placeholder environment variable names.  

I do not see a live token value in the uploaded context pack. The placeholder should remain a placeholder.

Positive security controls

The repo already has:

* .env excluded
* model weight patterns excluded
* tokens/credentials folders excluded
* generated dist/ excluded
* MCP GitHub disabled by default
* Playwright disabled by default
* destructive commands denied

Security improvements

Issue	Risk	Fix
No .env.example visible	Users may create inconsistent local envs	Add safe .env.example
GitHub MCP env var is visible as a placeholder	False positive warning noise	Add allowlist/comment or improve scanner classification
setup_wsl2_opencode.sh uses `curl	bash` style installers	Normal for setup, but conflicts with safe-terminal policy
No verification script	Easy to miss staged/generated files	Add scripts/verify-opencode-os.sh

Recommended sensitive warning policy

Keep current warning behavior, but classify known placeholders.

Recommended categories:

Active secret suspected
Placeholder/env var name
Documentation mention
Scanner self-match

The current finding should classify as:

Placeholder/env var name

⸻

Documentation Review

Strong docs

File	Assessment
README.md	Clear purpose and hardware summary
README_MASTER_GUIDE.md	Useful high-level opencode workflow
docs/hardware/local-host-pc-specs.md	Strong hardware source of truth
docs/model-routing/local-model-routing.md	Useful routing policy
docs/workflows/repository-audit-workflow.md	Good audit process
templates/repo-audits/opencode-system-audit-template.md	Good reusable audit prompt
templates/prompts/clarification-questions-template.md	Matches preferred response style

Weak docs

File / Area	Issue
docs/project-memory.md	Empty scaffold
docs/how-to-guides/	No visible guides
docs/decisions/	No visible ADRs/decision records
configs/	No visible configuration explanation
benchmarks/	No visible benchmark workflow doc
README.md	Does not yet document opencode-os.sh workflow
README_MASTER_GUIDE.md	Still focused on initial setup, not the new audit automation

Recommended documentation sequence

1. Update docs/project-memory.md
2. Add docs/how-to-guides/termius-iphone-opencode-workflow.md
3. Add docs/workflows/context-pack-workflow.md
4. Add docs/workflows/save-audit-workflow.md
5. Update README.md with “Daily Commands”

⸻

Recommended New Files

File	Purpose	Priority
.env.example	Safe placeholder environment template for MCP/API/local config	High
scripts/verify-opencode-os.sh	One-command repo health check	High
docs/how-to-guides/termius-iphone-opencode-workflow.md	Canonical mobile/Termius workflow	High
docs/workflows/context-pack-workflow.md	Explain context-pack generation and upload package	High
docs/workflows/save-audit-workflow.md	Explain saving audit results into docs/audits/	Medium
docs/audits/README.md	Index saved audit reports	Medium
docs/decisions/0001-generated-files-policy.md	Decision record: do not commit dist/ generated files	Medium
configs/README.md	Explain config directory purpose	Low
benchmarks/README.md	Explain local benchmark storage and expectations	Low
templates/README.md	Explain template categories	Low

⸻

Prioritized Execution Plan

Phase 1 — Foundation cleanup

Goal: remove ambiguity and make the repo self-explaining.

Run this phase first.

Tasks:

1. Add .env.example
2. Normalize registries/command-registry.md
3. Rename or merge audit-repo.md
4. Populate docs/project-memory.md
5. Update README.md with current automation commands

Recommended branch:

git checkout -b audit-001-foundation-cleanup

Phase 2 — Verification automation

Goal: reduce manual checking.

Create:

scripts/verify-opencode-os.sh

Minimum checks:

bash -n scripts/*.sh
git status --short
test -f .env.example
test ! -f .env
./scripts/build-context-pack.sh

Then add registry checks.

Phase 3 — Termius/iPhone workflow docs

Goal: preserve your actual operating method.

Create:

docs/how-to-guides/termius-iphone-opencode-workflow.md

Include:

1. run audit prep
2. download upload package through Termius SFTP
3. upload to ChatGPT
4. save audit response
5. upload audit response back
6. run save-audit

Phase 4 — Audit history system

Goal: make audits first-class repository artifacts.

Create or improve:

docs/audits/README.md
docs/workflows/save-audit-workflow.md

Then save this audit as:

docs/audits/opencode-system-audit-001.md

Phase 5 — Agent/skill refinement

Only after the above cleanup, tune agents and skills.

Potential edits:

.opencode/agents/architect.md
.opencode/agents/implementer.md
.opencode/agents/memory-curator.md
.opencode/skills/project-memory/SKILL.md
.opencode/skills/test-runner/SKILL.md

⸻
