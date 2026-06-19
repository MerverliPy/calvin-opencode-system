---
description: Security review of repo or diff.
agent: security-auditor
---

Perform a security audit for: $ARGUMENTS

Check:
- Secrets and credentials
- Unsafe shell commands
- Auth/session bugs
- Injection risks
- Dependency vulnerabilities
- MCP/tool permission risks
- Docker/devcontainer risk
- GitHub workflow risk

Do not edit files.
