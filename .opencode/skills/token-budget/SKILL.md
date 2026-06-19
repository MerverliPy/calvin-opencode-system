---
name: token-budget
description: Controls model choice, context usage, escalation, and monthly budget risk.
---

# Token Budget Skill

Use this skill when working on repo tasks with limited monthly API budget.

Rules:
- Use the cheapest capable model first.
- Prefer read-only scans before implementation.
- Avoid repeatedly loading huge files.
- Summarize findings before switching models.
- Escalate only when the current model fails.
- Do not use premium models for broad repo exploration.
- Recommend compaction or a new session when context becomes noisy.

Escalation path:
1. Local model
2. DeepSeek V4 Flash
3. DeepSeek V4 Pro
4. ChatGPT/OpenAI/Copilot
5. Claude Pro manual review
