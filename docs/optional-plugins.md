# Optional OpenCode Plugins

Keep plugins disabled until the base setup works.

Recommended evaluation order:
1. opencode-dynamic-context-pruning
2. opencode-vibeguard
3. opencode-shell-strategy
4. opencode-notifier
5. opencode-worktree
6. opencode-devcontainers
7. opencode-helicone-session

Add only one plugin at a time, then run:

```bash
opencode
```

If opencode fails to start, remove the plugin from `.opencode/opencode.json`.
