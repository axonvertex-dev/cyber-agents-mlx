# Cyber Agents MLX

Policy-aware defensive cyber triage agent for Apple Silicon, Docker, native Ollama MLX, GDPR, EU AI Act, and auditable AI-assisted security workflows.

This repository is a training lab asset for building secure AppSec triage agents. It assumes the Mac already has native Ollama/MLX installed and serving. The Docker app does not run MLX directly; it calls the host Ollama API through `host.docker.internal:11434`.

## What this project demonstrates

- Local FastAPI cyber triage service in Docker.
- Native Apple Silicon model serving via Ollama MLX.
- Redaction before model reasoning.
- Deterministic cyber signal scanning.
- Policy RAG over internal policy, GDPR, EU AI Act, and GPAI guidance.
- Hybrid semantic retrieval plus BM25-style keyword scoring.
- Family-balanced policy retrieval.
- Fast classifier agent and deep analyst agent.
- GDPR and EU AI Act assessment blocks.
- Human approval gates for risky actions.
- JSON audit evidence for every policy-aware triage run.

## What this project does not do

This lab does not install Ollama/MLX. Keep that as a separate setup guide or repository. It also does not perform autonomous remediation, blocking, credential rotation, firewall changes, destructive cleanup, or exploit execution.

## Architecture

```text
Security event/log
   ↓
FastAPI Docker service on :18110
   ↓
Redaction layer
   ↓
Deterministic signal scanner
   ↓
Policy RAG retrieval
   ↓
Fast classifier model
   ↓
GDPR + EU AI Act assessment
   ↓
Deep analyst model or fast triage mode
   ↓
Human-approval action guard
   ↓
JSON audit evidence
```

## Prerequisites

- Apple Silicon Mac.
- Docker Desktop installed.
- Native Ollama/MLX already installed and serving at `http://localhost:11434`.
- Required Ollama models pulled locally.

Recommended models for this lab:

```bash
ollama pull gemma4:e2b-mlx
ollama pull gemma4:e4b-mlx
ollama pull embeddinggemma:300m-qat-q8_0
```

Or run:

```bash
./scripts/pull_project_models.sh
```

## Quick start

```bash
git clone <YOUR_REPO_URL>
cd cyber-agents-mlx

cp .env.example .env
docker compose up -d --build
```

Add policy PDFs into `policy_docs/raw/` using the expected filenames listed in `policy_docs/raw/README.md`, then build the policy index:

```bash
./scripts/policy_embed_all.sh
```

Check the service:

```bash
curl -s http://localhost:18110/health | python3 -m json.tool
curl -s http://localhost:18110/policy/status | python3 -m json.tool
```

Run fast demo triage:

```bash
curl -s http://localhost:18110/triage/fast   -H "Content-Type: application/json"   -d @examples/ssh_failed_login.json | python3 -m json.tool
```

Run full deep triage:

```bash
curl -s http://localhost:18110/triage   -H "Content-Type: application/json"   -d @examples/ssh_failed_login.json | python3 -m json.tool
```

Watch progress logs in another terminal:

```bash
docker compose logs -f --tail=100 cyber-agents-mlx
```

## Main API endpoints

| Endpoint | Method | Purpose |
|---|---:|---|
| `/health` | GET | Service, model, policy index, and audit status |
| `/agents` | GET | Logical agent list |
| `/policy/status` | GET | Policy vector index status |
| `/policy/search` | POST | Hybrid policy retrieval |
| `/triage/fast` | POST | Fast triage using policy RAG and fast model only |
| `/triage` | POST | Full triage using policy RAG, fast classifier, and deep analyst |
| `/audit/status` | GET | Audit evidence status |

## Training context

This repo supports a module in a broader training program on building, securing, and deploying AI agent swarms in trustless decentralized ecosystems. This specific project focuses on the Apple Silicon local lab: policy-governed and privacy-preserving AppSec triage with auditable controls.

## Safety boundary

The system is read-only by design. It can inspect supplied logs, redact sensitive content, classify events, retrieve policy context, and recommend safe next actions. It must not autonomously delete logs, modify files, block IP addresses, rotate credentials, restart production services, change firewall rules, quarantine machines, or execute exploit chains.

## Documentation

Start here:

- `docs/INSTALL_APPLE_PROJECT.md`
- `docs/UNDERSTANDING_THE_FLOW.md`
- `docs/UNDERSTANDING_THE_RESULT.md`
- `docs/CODE_READINESS.md`
- `docs/GITHUB_PREP.md`
