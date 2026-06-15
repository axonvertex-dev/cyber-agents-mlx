#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/5] Checking Docker container..."
docker compose ps

echo
echo "[2/5] Checking policy documents inside Docker..."
docker compose exec -T cyber-agents-mlx python scripts/check_policy_docs.py

echo
echo "[3/5] Checking Ollama embedding model from inside Docker..."
docker compose exec -T cyber-agents-mlx python - <<'PY'
import json
import os
import urllib.request

base = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
model = os.getenv("EMBED_MODEL", "embeddinggemma:300m-qat-q8_0")

payload = {
    "model": model,
    "input": "GDPR data minimisation and AI Act human oversight"
}

req = urllib.request.Request(
    f"{base}/api/embed",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=120) as response:
    body = json.loads(response.read().decode("utf-8"))

embeddings = body.get("embeddings") or []
print("OLLAMA_BASE_URL =", base)
print("EMBED_MODEL =", model)
print("embedding_count =", len(embeddings))
print("embedding_dim =", len(embeddings[0]) if embeddings else 0)

if not embeddings:
    raise SystemExit("ERROR: no embeddings returned")
PY

echo
echo "[4/5] Ingesting and embedding policy documents..."
docker compose exec -T cyber-agents-mlx python scripts/ingest_policy_docs.py

echo
echo "[5/5] Checking generated index..."
ls -lh policy_docs/index
cat policy_docs/index/policy_manifest.json | python3 -m json.tool
wc -l policy_docs/index/policy_chunks.jsonl
wc -l policy_docs/index/policy_vectors.jsonl

echo
echo "Smoke test: GDPR search"
docker compose exec -T cyber-agents-mlx \
  python scripts/search_policy_index.py \
  "GDPR Article 5 data minimisation integrity confidentiality accountability security logs" \
  3

echo
echo "Smoke test: AI Act search"
docker compose exec -T cyber-agents-mlx \
  python scripts/search_policy_index.py \
  "AI Act human oversight transparency logging high-risk AI systems cybersecurity" \
  3

echo
echo "Policy embedding layer complete."
