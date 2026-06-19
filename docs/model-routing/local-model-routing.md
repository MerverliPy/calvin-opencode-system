# Local Model Routing Policy

## Host

Calvin Windows 10 / WSL2 workstation.

## Hardware Assumption

- CPU: Intel Core i7-9700K, 8 cores / 8 threads
- RAM: 48 GB DDR4
- GPU: NVIDIA RTX 4070, 12 GB VRAM
- CUDA: available
- Practical local model target: 7B–14B quantized

## Routing Rules

### Use local models for:

- repository scouting
- summarizing files
- extracting TODOs
- drafting docs
- reading logs
- small refactors
- test-output explanation
- initial repository audits

### Use cloud/API models for:

- long-context reasoning
- architecture decisions
- complex debugging
- multi-file implementation plans
- security review
- final PR review
- ambiguous product decisions

## Local Model Tiers

| Tier | Model class | Use |
|---|---|---|
| Fast | 3B–4B | quick summaries, command drafting |
| Default local | 7B–8B | coding assistance, repo analysis |
| Heavy local | 9B–14B quantized | deeper code work, slower review |
| Avoid locally | 30B+ | use cloud unless heavily quantized/offloaded |
