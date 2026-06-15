# Install Guide for the Apple MLX Cyber Agents Project

This document covers only this project. It does not install Ollama or the MLX runtime. The lab assumes native Ollama/MLX is already installed and serving on the Mac.

## Assumptions

```text
Ollama is reachable on the Mac at http://localhost:11434
Docker Desktop is installed
The Docker app can reach Ollama at http://host.docker.internal:11434
This project runs on port 18110
```

## Required models

```bash
ollama pull gemma4:e2b-mlx
ollama pull gemma4:e4b-mlx
ollama pull embeddinggemma:300m-qat-q8_0
```

Or:

```bash
./scripts/pull_project_models.sh
```

## Environment setup

```bash
cp .env.example .env
```

Default `.env` values:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
FAST_MODEL=gemma4:e2b-mlx
DEEP_MODEL=gemma4:e4b-mlx
EMBED_MODEL=embeddinggemma:300m-qat-q8_0
POLICY_TOP_K=6
```

## Start the service

```bash
docker compose up -d --build
```

Check container status:

```bash
docker compose ps
```

Check service health:

```bash
curl -s http://localhost:18110/health | python3 -m json.tool
```

## Policy documents

Place these policy documents into `policy_docs/raw/`:

```text
gdpr-regulation-2016-679.pdf
eu-ai-act-regulation-2024-1689.pdf
eu-ai-act-gpai-guidelines-2025-draft-communication.pdf
```

The repo includes:

```text
policy_docs/raw/internal-ai-data-policy.md
```

Validate policy documents:

```bash
docker compose exec -T cyber-agents-mlx python scripts/check_policy_docs.py
```

## Build embeddings

```bash
./scripts/policy_embed_all.sh
```

Expected result from the completed local build used during development:

```text
document_count: 4
chunk_count: 1101
embedding_model: embeddinggemma:300m-qat-q8_0
embedding_dimension: 768
hybrid_retrieval: embedding + BM25-style keyword scoring
```

## Run triage

Fast mode:

```bash
curl -s http://localhost:18110/triage/fast   -H "Content-Type: application/json"   -d @examples/ssh_failed_login.json | python3 -m json.tool
```

Full mode:

```bash
curl -s http://localhost:18110/triage   -H "Content-Type: application/json"   -d @examples/ssh_failed_login.json | python3 -m json.tool
```

## Live progress logs

```bash
docker compose logs -f --tail=100 cyber-agents-mlx
```

You should see progress steps such as:

```text
triage_started
redaction_done
signal_scan_done
policy_search_done
fast_classifier_done
deep_analyst_started
audit_write_started
triage_complete
```
