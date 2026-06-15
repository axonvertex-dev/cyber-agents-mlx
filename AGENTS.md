# Cyber Agents MLX Agent Registry

Local defensive cybersecurity agent system running on Apple Silicon.

## Runtime

- Host model server: native Ollama on macOS
- Model backend: MLX / Apple Silicon Metal
- Fast model: `gemma4:e2b-mlx`
- Deep model: `gemma4:e4b-mlx`
- Embedding model: `embeddinggemma:300m-qat-q8_0`
- App runtime: Docker Compose
- App port: `18110`

## Design

The system uses a deterministic orchestrator rather than a free-form LLM planner. The model is not the security boundary. The deterministic redaction layer, policy retrieval rules, blocked-action policy, and audit layer are the security boundary.

## Logical Agents

1. Redaction Agent
2. Signal Scanner Agent
3. Policy Ingestion Agent
4. Policy Retrieval Agent
5. Fast Classifier Agent
6. GDPR Policy Agent
7. EU AI Act Policy Agent
8. Deep Analyst Agent
9. Compliance Guard Agent
10. Audit Agent

## Allowed Scope

- log triage
- incident explanation
- alert prioritization
- privacy-preserving redaction
- policy context retrieval
- read-only investigation planning
- safe next-action generation
- audit evidence generation

## Not Allowed

The system must not:

- write exploit chains
- provide malware instructions
- suggest attacking third-party systems
- run destructive commands
- delete logs or evidence
- rotate secrets automatically
- block IPs automatically
- modify firewall rules automatically
- restart production services automatically
- bypass human approval controls
