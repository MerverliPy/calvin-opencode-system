---
name: dependency-security
description: Dependency, package, and supply-chain safety workflow.
---

# Dependency Security Skill

Before installing packages:
1. Identify package name and purpose.
2. Check whether it is already in lockfile.
3. Prefer official packages.
4. Avoid unmaintained packages.
5. Ask before install.
6. Install only in sandbox/devcontainer unless approved.

Red flags:
- postinstall scripts
- unknown maintainers
- typo-squatting
- abandoned packages
- packages requesting broad tokens
