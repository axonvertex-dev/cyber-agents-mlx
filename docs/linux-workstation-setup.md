# Linux Workstation Setup for `cyber-agents-mlx`

Use this setup for Ubuntu/Linux workstations.

The app runs in Docker Compose. Ollama runs on the Linux host and exposes the API at:

```text
http://localhost:11434
```

The Docker app calls the host Ollama server through:

```text
http://host.docker.internal:11434
```

On Linux, this usually requires Docker Compose `extra_hosts`.

## Required models

Use non-MLX model tags on Linux:

```text
gemma4:e2b
gemma4:e4b
embeddinggemma:300m-qat-q8_0
```

## 1. Verify system

```bash
uname -a
cat /etc/os-release
free -h
df -h .
```

For NVIDIA systems:

```bash
nvidia-smi
```

## 2. Verify Ollama

```bash
ollama --version
curl http://localhost:11434
```

Expected:

```text
Ollama is running
```

If Ollama is installed as a service:

```bash
sudo systemctl status ollama --no-pager
```

Start if needed:

```bash
sudo systemctl start ollama
```

## 3. Pull models

```bash
ollama pull gemma4:e2b
ollama pull gemma4:e4b
ollama pull embeddinggemma:300m-qat-q8_0
```

## 4. Verify models

```bash
ollama list
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

You should see:

```text
gemma4:e2b
gemma4:e4b
embeddinggemma:300m-qat-q8_0
```

## 5. Configure `.env`

From the repo root:

```bash
cp .env.example.linux .env
```

Expected `.env`:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
FAST_MODEL=gemma4:e2b
DEEP_MODEL=gemma4:e4b
EMBED_MODEL=embeddinggemma:300m-qat-q8_0
POLICY_TOP_K=6
POLICY_INDEX_PATH=/app/policy_docs/index/policy_vectors.jsonl
POLICY_CHUNKS_PATH=/app/policy_docs/index/policy_chunks.jsonl
POLICY_MANIFEST_PATH=/app/policy_docs/index/policy_manifest.json
AUDIT_LOG_DIR=/app/audit_logs
PORT=18110
```

## 6. Build and run with Linux override

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.yml up --build -d
```

Check:

```bash
curl -s http://localhost:18110/health | python3 -m json.tool
curl -s http://localhost:18110/agents | python3 -m json.tool
```

## 7. Rebuild policy index

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.yml exec cyber-agents-mlx python scripts/ingest_policy_docs.py
```

Check status:

```bash
curl -s http://localhost:18110/policy/status | python3 -m json.tool
```

## 8. Run fast triage

```bash
curl -s http://localhost:18110/triage/fast \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "LINUX-DEMO-001",
    "text": "Suspicious login failures detected from multiple IPs. User email krish@example.com appeared in logs. Please triage safely."
  }' | python3 -m json.tool
```

## 9. Stop

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.yml stop
```

## Troubleshooting

### Docker cannot resolve `host.docker.internal`

Use the Linux override file:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Ollama service inactive

```bash
sudo systemctl start ollama
sudo systemctl status ollama --no-pager
journalctl -u ollama -n 100 --no-pager
```

### NVIDIA GPU not visible

```bash
nvidia-smi
```

Fix the NVIDIA driver/runtime before the lab.

## Notes

- Linux does not use MLX tags.
- Use `/triage/fast` for live demos.
- Full `/triage` can be slower depending on CPU/GPU.
