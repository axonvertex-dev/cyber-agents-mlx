# Apple Silicon MLX Setup for `cyber-agents-mlx`

Use this setup for macOS on Apple Silicon: M1, M2, M3, or M4.

This is the primary tested path for the lab.

## Architecture

```text
Docker Compose app container
        |
        | HTTP
        v
Native Ollama on macOS
        |
        v
Apple Silicon MLX models
```

The app runs in Docker. Ollama runs natively on macOS.

Do not run Ollama MLX inside Docker. Docker cannot directly use Apple Metal/MLX acceleration the same way native Ollama can.

## Required models

```text
gemma4:e2b-mlx
gemma4:e4b-mlx
embeddinggemma:300m-qat-q8_0
```

## 1. Verify Ollama

```bash
ollama --version
curl http://localhost:11434
```

Expected:

```text
Ollama is running
```

## 2. Pull models

```bash
ollama pull gemma4:e2b-mlx
ollama pull gemma4:e4b-mlx
ollama pull embeddinggemma:300m-qat-q8_0
```

## 3. Verify models

```bash
ollama list
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

You should see:

```text
gemma4:e2b-mlx
gemma4:e4b-mlx
embeddinggemma:300m-qat-q8_0
```

## 4. Configure `.env`

From the repo root:

```bash
cp .env.example.apple .env
```

Expected `.env`:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
FAST_MODEL=gemma4:e2b-mlx
DEEP_MODEL=gemma4:e4b-mlx
EMBED_MODEL=embeddinggemma:300m-qat-q8_0
POLICY_TOP_K=6
POLICY_INDEX_PATH=/app/policy_docs/index/policy_vectors.jsonl
POLICY_CHUNKS_PATH=/app/policy_docs/index/policy_chunks.jsonl
POLICY_MANIFEST_PATH=/app/policy_docs/index/policy_manifest.json
AUDIT_LOG_DIR=/app/audit_logs
PORT=18110
```

## 5. Build and run

```bash
docker compose up --build -d
```

Check:

```bash
curl -s http://localhost:18110/health | python3 -m json.tool
curl -s http://localhost:18110/agents | python3 -m json.tool
```

## 6. Rebuild policy index

```bash
docker compose exec cyber-agents-mlx python scripts/ingest_policy_docs.py
```

Check status:

```bash
curl -s http://localhost:18110/policy/status | python3 -m json.tool
```

## 7. Run fast triage

```bash
curl -s http://localhost:18110/triage/fast \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "APPLE-DEMO-001",
    "text": "User reports repeated failed login attempts from unknown IPs. Email krish@example.com appeared in logs. Please triage safely."
  }' | python3 -m json.tool
```

## 8. Stop

```bash
docker compose stop
```

## Notes

- Keep Ollama native on macOS.
- Keep models outside Docker.
- Use `host.docker.internal` from Docker to reach native Ollama.
- Use `/triage/fast` for live lab demos if time is limited.
