---
name: sandbox-ladder
description: Chooses branch/worktree/devcontainer/docker isolation level.
---

# Sandbox Ladder Skill

Level 1: Git branch
Use for docs and low-risk code edits.

Level 2: Git worktree
Use for refactors, generated code, experiments, or parallel agent sessions.

Level 3: Devcontainer
Use for dependency installs, builds, tests, and unknown repos.

Level 4: Docker disposable container
Use for untrusted repos, migration scripts, web automation, and destructive experiments.

Default:
- Tests/builds should run in devcontainer when practical.
- Dependency installation should happen in devcontainer or disposable container.
- Never run destructive cleanup commands outside sandbox without explicit approval.
