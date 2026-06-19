---
name: local-model-routing
description: Decides when local models are safe and useful on RTX 4070 12GB.
---

# Local Model Routing Skill

Hardware baseline:
- RTX 4070 12GB VRAM
- 48GB DDR4 RAM
- i7-9700K 8C/8T
- WSL2 Ubuntu target

Use local models for:
- repo summaries
- grep result interpretation
- README/docs drafts
- test-output summarization
- commit-message drafts
- low-risk code explanation

Avoid local models for:
- high-risk code edits
- auth/payment/security code
- major refactors
- dependency migrations
- multi-file implementation unless user approves and cloud review follows

Recommended local context:
- Start 32k if 64k is unstable.
- Use 64k only with smaller 4B/7B models or if memory allows.
