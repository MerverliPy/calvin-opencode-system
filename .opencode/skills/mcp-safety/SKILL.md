---
name: mcp-safety
description: Safe MCP server access policy.
---

# MCP Safety Skill

Rules:
- Enable only the MCPs needed for the task.
- Prefer Context7 for documentation first.
- Keep GitHub MCP disabled until a GitHub task needs it.
- Keep Playwright MCP disabled until browser/UI testing needs it.
- Do not expose tokens to unknown MCP servers.
- Do not combine filesystem-write MCPs with GitHub/write tools unless sandboxed.
- Treat MCP tools as action tools, not harmless context.

Default MCP policy:
- Context7: allow for docs
- GitHub: ask
- Playwright: ask, sandbox preferred
- Filesystem: avoid unless necessary
- Docker: ask, sandbox only
- Memory: carefully scoped
