---
name: project-memory
description: Durable repo memory policy.
---

# Project Memory Skill

Benefits:
- Reduces repeated repo exploration.
- Preserves architecture decisions.
- Tracks accepted commands, test procedures, and pitfalls.
- Helps future sessions start faster with less token waste.

Implementation:
- Use docs/project-memory.md per repo.
- Update after meaningful completed tasks.
- Store only durable technical facts.

Do not store:
- API keys
- secrets
- personal data
- temporary errors
- raw chat transcripts

## Update Triggers

Update `docs/project-memory.md` after:

- merged workflow changes
- script or command-router changes
- agent, command, or skill changes
- registry changes
- repeated Termius/iPhone pitfalls
- accepted verification or security decisions

Keep entries concise and durable.
