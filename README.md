# Cyber Agents MLX

Policy-aware secure cyber triage agent for Apple Silicon MLX, Docker, GDPR, EU AI Act, and auditable AI-assisted workflows.

This project is a hands-on training lab for building a local defensive AppSec/cybersecurity triage agent that uses:

- Native Ollama MLX model serving on Apple Silicon
- Dockerized FastAPI application layer
- Hybrid policy retrieval using embeddings and BM25-style keyword scoring
- GDPR, EU AI Act, GPAI guidance, and internal policy context
- Redaction before model reasoning
- Deterministic security signal detection
- Fast and deep triage modes
- JSON audit evidence records
- Explicit human-approval gates for risky actions

This repository is intended for defensive security training and lab use.

---

## What this repo does

The system accepts a security event, log, or alert and produces a policy-aware triage result.

It performs:

1. Redaction of obvious secrets and personal identifiers
2. Deterministic cyber signal scanning
3. Policy RAG retrieval over GDPR, EU AI Act, GPAI guidance, and internal policy
4. Fast model classification
5. Optional deep analyst reasoning
6. GDPR-oriented assessment
7. EU AI Act-oriented assessment
8. Safe next-action generation
9. Blocked-action policy enforcement
10. Audit record creation

---

## What this repo does not do

This project does not perform autonomous remediation.

It does not:

- delete files
- delete logs
- wipe evidence
- block IP addresses automatically
- change firewall rules automatically
- rotate credentials automatically
- restart production services automatically
- execute exploit chains
- provide malware or evasion instructions
- replace legal, compliance, or incident-response review

All containment, infrastructure modification, credential rotation, and irreversible actions require human approval.

---

## Apple Silicon / MLX assumption

This repository assumes native Ollama MLX is already installed and running on macOS.

This repo does **not** install Ollama or configure MLX from scratch.

Expected host setup:

```text
macOS Apple Silicon
Native Ollama MLX serving at http://localhost:11434
Docker Desktop installed
Docker app calls Ollama through http://host.docker.internal:11434
```

The Docker container does not run MLX directly. The model server stays native on macOS for Apple Silicon acceleration.

---

## Required models

Pull the project models on the Mac host:

```bash
ollama pull gemma4:e2b-mlx
ollama pull gemma4:e4b-mlx
ollama pull embeddinggemma:300m-qat-q8_0
```

Or use:

```bash
./scripts/pull_project_models.sh
```

Default model roles:

| Model | Role |
|---|---|
| `embeddinggemma:300m-qat-q8_0` | Policy document embeddings |
| `gemma4:e2b-mlx` | Fast classifier |
| `gemma4:e4b-mlx` | Deep analyst |

---

## Quick start

Clone the repo:

```bash
git clone https://github.com/axonvertex-dev/cyber-agents-mlx.git
cd cyber-agents-mlx
```

Create environment config:

```bash
cp .env.example .env
```

Check that Ollama is reachable on the Mac host:

```bash
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

Start the Docker app:

```bash
docker compose up -d --build
```

Check health:

```bash
curl -s http://localhost:18110/health | python3 -m json.tool
```

---

## Policy source documents

The required policy source documents are included in:

```text
policy_docs/raw/
```

Included files:

```text
gdpr-regulation-2016-679.pdf
eu-ai-act-regulation-2024-1689.pdf
eu-ai-act-gpai-guidelines-2025-draft-communication.pdf
internal-ai-data-policy.md
```

The PDF files are included for training convenience so participants can run the policy ingestion workflow without manually downloading legal source documents.

The internal lab policy demonstrates policy-as-code, defensive operating boundaries, and human-approval guardrails.

Validate policy files:

```bash
docker compose exec -T cyber-agents-mlx python scripts/check_policy_docs.py
```

---

## Build policy index

Generate the local policy RAG index:

```bash
./scripts/policy_embed_all.sh
```

Expected generated files:

```text
policy_docs/index/policy_chunks.jsonl
policy_docs/index/policy_vectors.jsonl
policy_docs/index/policy_manifest.json
```

Expected tested state:

```text
chunk_count: 1101
embedding_model: embeddinggemma:300m-qat-q8_0
policy families:
  EU_AI_ACT_GPAI_GUIDANCE
  EU_AI_ACT
  GDPR
  INTERNAL_POLICY
```

---

## API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Service, model, policy index, and audit status |
| `/agents` | GET | Logical agent list |
| `/policy/status` | GET | Policy vector index status |
| `/policy/search` | POST | Hybrid policy retrieval |
| `/triage/fast` | POST | Fast triage using policy RAG and fast model only |
| `/triage` | POST | Full triage using policy RAG, fast classifier, and deep analyst |
| `/audit/status` | GET | Audit evidence status |

---

## Example: fast triage

```bash
curl -s http://localhost:18110/triage/fast \
  -H "Content-Type: application/json" \
  -d @examples/ssh_failed_login.json | python3 -m json.tool
```

Fast triage returns:

```text
redacted_input
deterministic_signals
policy_context
fast_classification
gdpr_assessment
eu_ai_act_assessment
analyst_report
safe_next_actions
blocked_actions_policy
audit_id
```

---

## Example: full deep triage

Full triage uses both the fast classifier and deep analyst model.

```bash
time curl -s http://localhost:18110/triage \
  -H "Content-Type: application/json" \
  -d @examples/ssh_failed_login.json | python3 -m json.tool
```

Watch progress logs in another terminal:

```bash
docker compose logs -f --tail=50 cyber-agents-mlx
```

Expected progress steps:

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

---

## Smoke test

Run the end-to-end smoke test:

```bash
./scripts/smoke_test.sh
```

The smoke test checks:

```text
/health
/policy/status
/policy/search
/triage/fast
/audit/status
```

---

## Architecture flow

```text
Security log / alert
    ↓
Redaction layer
    ↓
Deterministic signal scanner
    ↓
Policy retrieval agent
    ↓
Hybrid RAG:
  - embedding search
  - BM25-style keyword scoring
  - family-balanced policy retrieval
    ↓
Fast classifier agent
    ↓
GDPR assessment
    ↓
EU AI Act assessment
    ↓
Deep analyst agent
    ↓
Safe next-action filter
    ↓
Audit evidence writer
    ↓
JSON response
```

---

## Policy source attribution

The included EU policy PDFs are used as training source documents for local policy retrieval.

- GDPR Regulation (EU) 2016/679: EUR-Lex / European Union
- Regulation (EU) 2024/1689, Artificial Intelligence Act: EUR-Lex / European Union
- Draft Commission communication on GPAI model obligations: European Commission / European Union

Generated embeddings are local runtime artifacts and are not committed.

---

## GitHub hygiene

The following files are intentionally not committed:

- `.env`
- `audit_logs/*.json`
- `policy_docs/index/*.json`
- `policy_docs/index/*.jsonl`
- other unapproved `policy_docs/raw/*.pdf` files
- Python cache files
- macOS metadata files

The named policy PDFs in `policy_docs/raw/` are intentionally included for the training lab.

Audit logs and generated vector indexes are runtime artifacts.

---

## Tested state

Validated on Apple Silicon with:

- Docker Compose service on port `18110`
- Native Ollama MLX reachable from Docker through `host.docker.internal:11434`
- `gemma4:e2b-mlx`
- `gemma4:e4b-mlx`
- `embeddinggemma:300m-qat-q8_0`
- Policy index: `1101` chunks
- Policy families: GDPR, EU AI Act, EU AI Act GPAI guidance, internal policy
- Fast triage: passed
- Full triage: passed
- Audit evidence: passed

---

## Training context

This project supports hands-on training for:

```text
Building, Securing, and Deploying AI Agent Swarms in a Trustless Decentralized Ecosystem
```

It demonstrates a focused Apple Silicon lab module for:

- policy-governed agent workflows
- privacy-preserving triage
- RAG controls
- auditability
- human-approval boundaries
- defensive AppSec/cybersecurity workflows

---

## Documentation

Additional docs are in:

```text
docs/
```

Recommended reading order:

```text
docs/CODE_READINESS.md
docs/INSTALL_APPLE_PROJECT.md
docs/UNDERSTANDING_THE_FLOW.md
docs/UNDERSTANDING_THE_RESULT.md
docs/TRAINING_CONTEXT.md
docs/GITHUB_PREP.md
```

---

## Safety boundary

This project is defensive only.

The system may recommend read-only triage and human-approved escalation.

It must not autonomously perform destructive, exploitative, credential-stealing, privacy-invasive, or infrastructure-modifying actions.
