# Project Agent Rules

This repository uses an opencode-first agentic workflow.

Core rules:
- Start with planning before edits.
- Use small, reversible implementation phases.
- Prefer cheap/local models for exploration and summaries.
- Use DeepSeek API for most coding work.
- Use ChatGPT/Copilot for higher-confidence planning/review.
- Use Claude Pro as an external review layer, not as a direct opencode provider unless allowed by provider terms.
- Run tests/builds in a sandbox whenever possible.
- Do not run destructive commands without explicit approval.
- Do not store secrets in project memory.
