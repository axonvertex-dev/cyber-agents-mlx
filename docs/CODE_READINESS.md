# Code Readiness Review

This document captures the readiness state before publishing the repo.

## Completed

- FastAPI app builds in Docker.
- App exposes `/health`, `/agents`, `/policy/status`, `/policy/search`, `/triage/fast`, `/triage`, and `/audit/status`.
- Docker talks to native Ollama/MLX through `host.docker.internal:11434`.
- Redaction is implemented before model reasoning.
- Deterministic signal scanning is implemented.
- Policy ingestion supports PDF, Markdown, and text files.
- Policy embeddings are generated through Ollama `/api/embed`.
- Retrieval uses semantic similarity plus BM25-style keyword scoring.
- Retrieval uses family balancing across internal policy, GDPR, EU AI Act, and GPAI guidance.
- Full triage writes JSON audit evidence.
- Fast triage endpoint is included for workshop demos.
- Download helper avoids automatic cleanup/deletion of policy source files.
- `.env.example`, `.gitignore`, examples, smoke test, and docs are included.

## Files expected in GitHub

```text
README.md
QUICKSTART.md
.env.example
.gitignore
.dockerignore
Dockerfile
docker-compose.yml
requirements.txt
app/
scripts/
policies/
skills/
agents/
examples/
docs/
policy_docs/raw/internal-ai-data-policy.md
policy_docs/raw/README.md
policy_docs/index/.gitkeep
audit_logs/.gitkeep
```

## Files intentionally excluded from GitHub

```text
.env
audit_logs/*.json
policy_docs/index/*.json
policy_docs/index/*.jsonl
policy_docs/raw/*.pdf
__pycache__/
*.pyc
.DS_Store
__MACOSX/
```

## Safety boundary

The V1 safety boundary is read-only triage. The system must not perform destructive or irreversible actions through chat or API responses. It can recommend human-reviewed next steps.

Blocked action classes:

```text
delete files or logs
wipe evidence
block IP addresses automatically
change firewall rules
change SSH configuration
rotate credentials automatically
disable accounts
quarantine machines
restart production services
execute exploit chains
provide malware or evasion instructions
```

## Validation commands

```bash
python3 -m py_compile app/main.py app/rag.py app/audit.py scripts/*.py

docker compose up -d --build
curl -s http://localhost:18110/health | python3 -m json.tool
./scripts/policy_embed_all.sh
./scripts/smoke_test.sh
```

## Known operational note

The full `/triage` endpoint can be slow because it calls the deeper model. Use `/triage/fast` for live workshop demos and `/triage` for complete evidence-generation examples.
