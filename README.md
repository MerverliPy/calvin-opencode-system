# Calvin opencode System

Private source-of-truth repository for opencode workflows, agents, commands, skills, templates, tools, local model routing, setup guides, tips, and repository audit systems.

## Purpose

This repository is my personal operating system for agentic development.

It stores:

- opencode agents
- opencode commands
- opencode skills
- local model routing rules
- WSL2 setup notes
- local AI hardware profile
- repository audit workflows
- implementation templates
- clarification-question templates
- how-to guides
- reusable tips and tricks

## Local Host Assumption

Primary workstation:

- Windows 10 Pro
- WSL2 Ubuntu target
- Intel Core i7-9700K
- 48 GB DDR4 RAM
- NVIDIA RTX 4070 12 GB
- Best local model range: 7B–14B quantized
- Use CUDA where possible
- Use cloud models for heavy reasoning, long context, and complex multi-agent orchestration

See:

- `docs/hardware/local-host-pc-specs.md`
- `docs/model-routing/local-model-routing.md`

## Operating Rule

All workflow changes should be small, reviewable, and reversible.

## Daily opencode OS Workflow

Generate a Termius/iPhone-safe audit upload package:

~~~~bash
./scripts/opencode-os.sh audit-prep
~~~~

Upload this generated file into ChatGPT or opencode:

~~~~text
dist/audit-requests/opencode-audit-upload.md
~~~~

Save an audit response back into the repository:

~~~~bash
./scripts/opencode-os.sh save-audit path/to/audit-response.md --commit --push
~~~~

Check repository operating-system status:

~~~~bash
./scripts/opencode-os.sh status
~~~~

Run repository verification:

~~~~bash
./scripts/verify-opencode-os.sh
~~~~

Generated `dist/` files are not committed by default.
