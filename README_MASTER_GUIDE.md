# Calvin's opencode Full-System Agentic Workflow

This kit is tuned for:

- Windows 10 Pro host
- WSL2 Ubuntu development target
- Intel i7-9700K, 8 cores / 8 threads
- 48GB DDR4 RAM
- NVIDIA RTX 4070 12GB
- opencode-first terminal workflow
- ChatGPT Plus + Copilot Pro + DeepSeek API + Claude Pro + API reserve

## Install order

1. Verify WSL2 Ubuntu.
2. Verify NVIDIA WSL CUDA access with `nvidia-smi`.
3. Install Docker Desktop with WSL2 backend.
4. Install opencode inside WSL2.
5. Install Ollama and/or LM Studio.
6. Copy `.opencode` into each repo.
7. Connect providers with `/connect`.
8. Select models with `/models`.
9. Enable Context7 MCP first.
10. Enable GitHub MCP only when needed.
11. Enable Playwright MCP only for browser/UI work.
12. Run `/repo-audit`.
13. Run `/plan-feature`.
14. Approve one phase.
15. Run `/implement-phase`.
16. Run `/review-diff`.
17. Run `/cost-check`.
18. Update `docs/project-memory.md`.

## First commands

```bash
bash scripts/system_check.sh
bash scripts/setup_wsl2_opencode.sh
opencode
```

Inside opencode:

```text
/connect
/models
/repo-audit
```

## Budget routing

- Local models: free scouting, summaries, docs, test output.
- DeepSeek Flash: default coding fuel.
- DeepSeek Pro: harder implementation and debugging.
- ChatGPT Plus: planning and final reasoning.
- Copilot Pro: GitHub-native workflow and PR review.
- Claude Pro: external review/comparison.
- Flexible API reserve: emergency model escalation.
