# Quickstart

This quickstart assumes native Ollama/MLX is already installed and running on macOS.

## 1. Clone and configure

```bash
git clone <YOUR_REPO_URL>
cd cyber-agents-mlx
cp .env.example .env
```

## 2. Pull project models

```bash
./scripts/pull_project_models.sh
```

## 3. Start the Docker app

```bash
docker compose up -d --build
```

## 4. Add policy PDFs

Place these files in `policy_docs/raw/`:

```text
gdpr-regulation-2016-679.pdf
eu-ai-act-regulation-2024-1689.pdf
eu-ai-act-gpai-guidelines-2025-draft-communication.pdf
```

The internal policy file is already included:

```text
policy_docs/raw/internal-ai-data-policy.md
```

## 5. Build policy embeddings

```bash
./scripts/policy_embed_all.sh
```

Expected generated files:

```text
policy_docs/index/policy_chunks.jsonl
policy_docs/index/policy_vectors.jsonl
policy_docs/index/policy_manifest.json
```

## 6. Run the smoke test

```bash
./scripts/smoke_test.sh
```

## 7. Watch logs

```bash
docker compose logs -f --tail=100 cyber-agents-mlx
```
