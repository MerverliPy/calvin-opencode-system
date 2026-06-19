# Model Routing

## Primary routing

| Role | Primary | Backup 1 | Backup 2 | Backup 3 |
|---|---|---|---|---|
| Repo scout | Local Qwen Coder 7B | DeepSeek Flash | ChatGPT Plus | Copilot |
| Cheap implementation | DeepSeek Flash | DeepSeek Pro | Copilot | ChatGPT |
| Hard implementation | DeepSeek Pro | ChatGPT/Codex | Copilot premium model | Claude manual review |
| Final review | ChatGPT Plus | Claude Pro | Copilot review | DeepSeek Pro |
| PR/GitHub | Copilot Pro | ChatGPT Plus | Claude Pro manual | DeepSeek Pro |
| Web/UI testing | Playwright MCP + DeepSeek | ChatGPT | Copilot | Claude review |

## Local model policy

RTX 4070 12GB should prioritize 4B-14B quantized models.
Local models should start read-only. Allow edits only after model-specific testing.
