---
description: Operate the local GitHub multitool safely.
agent: implementer
---

Use the GitHub localhost multitool for safe repository inspection and local GitHub workflow support.

Rules:

- Prefer read-only commands first.
- Confirm the server is localhost-only before use.
- Do not expose the server publicly.
- Do not print or store tokens.
- Do not use write tools unless the user explicitly approves the exact action.
- Require explicit confirmation before merge, branch deletion, issue closure, repo setting changes, or secret changes.
- Run the smoke test before relying on the tool.

Baseline commands:

~~~~bash
python3 tools/github-multitool/github_multitool.py health
tools/github-multitool/smoke-test.sh
~~~~

Read-only CLI commands:

~~~~bash
python3 tools/github-multitool/github_multitool.py repo-status
python3 tools/github-multitool/github_multitool.py prs-list --state open
python3 tools/github-multitool/github_multitool.py issues-list --state open
python3 tools/github-multitool/github_multitool.py branches-list
python3 tools/github-multitool/github_multitool.py runs-list
~~~~

Read-only server commands:

~~~~bash
python3 tools/github-multitool/server.py
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/repo/status
curl http://127.0.0.1:8765/prs
curl http://127.0.0.1:8765/issues
curl http://127.0.0.1:8765/branches
curl http://127.0.0.1:8765/runs
~~~~

Verification:

~~~~bash
tools/github-multitool/smoke-test.sh
./scripts/verify-opencode-os.sh
~~~~
