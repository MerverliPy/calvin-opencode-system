# Context Pack Workflow

## Purpose

The context pack workflow creates a clean Markdown snapshot of the repository for ChatGPT, opencode, or another AI coding assistant.

## Primary Command

~~~~bash
./scripts/opencode-os.sh audit-prep
~~~~

This wraps:

~~~~bash
./scripts/build-context-pack.sh
~~~~

and creates a combined audit upload package:

~~~~text
dist/audit-requests/opencode-audit-upload.md
~~~~

## Generated Files

| File | Purpose |
|---|---|
| `dist/context-packs/calvin-opencode-system-context-pack.md` | Raw repository context pack |
| `dist/audit-requests/audit-request.md` | Audit prompt only |
| `dist/audit-requests/opencode-audit-upload.md` | Combined prompt plus context pack |
| `dist/audit-requests/sensitive-warning-report.txt` | Sensitive-pattern warning extract |
| `dist/audit-requests/mobile-upload-instructions.txt` | Termius/iPhone upload instructions |

## Commit Policy

Generated `dist/` files should not be committed by default.

Commit only source files such as scripts, docs, templates, registries, agents, commands, and skills.
