---
name: test-runner
description: Controlled test/build execution policy.
---

# Test Runner Skill

Rules:
- Run the smallest relevant test first.
- Prefer deterministic tests.
- Capture exact command and result.
- Do not claim tests passed unless actually run.
- Escalate failures to debugging plan before editing again.
- In WSL2, keep repo files inside the Linux filesystem for better performance.
