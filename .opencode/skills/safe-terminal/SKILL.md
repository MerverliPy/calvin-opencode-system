---
name: safe-terminal
description: Safe command execution policy for local agentic coding.
---

# Safe Terminal Skill

Allowed without concern:
- git status
- git diff
- git log
- rg
- grep
- find
- ls
- cat
- pwd

Ask before:
- package installs
- build commands
- test commands
- database commands
- migrations
- chmod
- network commands
- docker commands

Never run without explicit approval:
- rm -rf
- sudo
- git reset --hard
- git clean
- git push
- curl | sh
- wget | sh
- credential or token exfiltration commands

## Termius / iPhone Safety

When the user is working from Termius on iPhone:

- prefer small command blocks
- avoid large pasted multi-step scripts
- prefer saved scripts in `/tmp` for complex operations
- checkpoint with `git status --short --branch`
- avoid clipboard and Windows GUI assumptions
- stop after failures and inspect before rerunning
