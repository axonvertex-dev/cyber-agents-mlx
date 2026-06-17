# Windows WSL2 Setup for `cyber-agents-mlx`

Use this setup for Windows users running the lab through WSL2 and Docker Desktop.

The app runs in Docker Compose. Ollama can run either on the Windows host or inside WSL2.

Recommended lab path:

```text
Windows + Docker Desktop + WSL2
Ollama API reachable at http://localhost:11434
Docker app reaches Ollama through http://host.docker.internal:11434
```

## Required models

Use non-MLX model tags on WSL:

```text
gemma4:e2b
gemma4:e4b
embeddinggemma:300m-qat-q8_0
```

## 1. Check WSL

In PowerShell:

```powershell
wsl --status
wsl --list --verbose
```

Expected:

```text
WSL version 2
```

Inside WSL:

```bash
uname -a
cat /etc/os-release
```

## 2. Docker Desktop

In Docker Desktop:

```text
Settings → Resources → WSL Integration
```

Enable integration for the Linux distribution used for the lab.

Verify inside WSL:

```bash
docker version
docker compose version
```

## 3. Ollama option A: Ollama on Windows

In PowerShell:

```powershell
ollama --version
curl http://localhost:11434
```

Expected:

```text
Ollama is running
```

From WSL:

```bash
curl http://localhost:11434
```

## 4. Ollama option B: Ollama inside WSL

Inside WSL:

```bash
ollama --version
curl http://localhost:11434
```

If installed as a Linux service:

```bash
sudo systemctl status ollama --no-pager
sudo systemctl start ollama
```

Use only one Ollama server at a time to avoid port conflicts.

## 5. Pull models

From the environment where Ollama is running:

```bash
ollama pull gemma4:e2b
ollama pull gemma4:e4b
ollama pull embeddinggemma:300m-qat-q8_0
```

## 6. Verify models

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

## 7. Configure `.env`

From the repo root inside WSL:

```bash
cp .env.example.wsl .env
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

## 8. Build and run with WSL override

```bash
docker compose -f docker-compose.yml -f docker-compose.wsl.yml up --build -d
```

Check:

```bash
curl -s http://localhost:18110/health | python3 -m json.tool
curl -s http://localhost:18110/agents | python3 -m json.tool
```

## 9. Rebuild policy index

```bash
docker compose -f docker-compose.yml -f docker-compose.wsl.yml exec cyber-agents-mlx python scripts/ingest_policy_docs.py
```

Check status:

```bash
curl -s http://localhost:18110/policy/status | python3 -m json.tool
```

## 10. Run fast triage

```bash
curl -s http://localhost:18110/triage/fast \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "WSL-DEMO-001",
    "text": "Suspicious login failures detected from multiple IPs. User email krish@example.com appeared in logs. Please triage safely."
  }' | python3 -m json.tool
```

## 11. Stop

```bash
docker compose -f docker-compose.yml -f docker-compose.wsl.yml stop
```

## Troubleshooting

### Docker command not found inside WSL

Enable Docker Desktop WSL integration.

### Ollama reachable in Windows but not WSL

Try from WSL:

```bash
curl http://localhost:11434
```

If it fails, either run Ollama inside WSL or check Windows firewall/networking.

### Docker app cannot reach Ollama

The WSL override includes:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Port conflict

Only run one Ollama server at a time.

## Notes

- WSL does not use MLX tags.
- Use `/triage/fast` for live demos.
- Full `/triage` can be slower depending on CPU/GPU.
