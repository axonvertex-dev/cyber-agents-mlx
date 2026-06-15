# Understanding the Flow

This project implements a policy-aware defensive cyber triage workflow.

## Runtime flow

```text
User sends security event/log
   ↓
FastAPI endpoint receives request
   ↓
Redaction layer masks obvious secrets and personal data
   ↓
Deterministic scanner identifies security signals
   ↓
Policy query is built from redacted event + signals
   ↓
Policy RAG retrieves relevant chunks
   ↓
Fast classifier model produces structured severity/category JSON
   ↓
GDPR assessment is generated deterministically
   ↓
EU AI Act assessment is generated deterministically
   ↓
Deep analyst model writes a defensive report, or /triage/fast writes a fast report
   ↓
Human approval guard blocks risky action classes
   ↓
Audit record is written to audit_logs/
   ↓
Response is returned to caller
```

## Agent roles

The implementation is a deterministic orchestrator with logical agents:

| Agent | Implementation role |
|---|---|
| Redaction Agent | `redact_sensitive()` masks obvious secrets, IPs, emails, private keys |
| Signal Scanner Agent | `deterministic_signal_scan()` identifies security signals |
| Policy Retrieval Agent | `search_policy()` performs hybrid RAG |
| Fast Classifier Agent | `FAST_MODEL` returns structured JSON classification |
| GDPR Policy Agent | `gdpr_assess()` creates GDPR-aligned assessment |
| EU AI Act Policy Agent | `eu_ai_act_assess()` creates AI Act-aligned assessment |
| Deep Analyst Agent | `DEEP_MODEL` writes analyst report for `/triage` |
| Compliance Guard Agent | `policy_filter_actions()` and blocked policy prevent unsafe recommendations |
| Audit Agent | `write_audit_record()` writes JSON evidence |

## Policy RAG flow

Policy ingestion runs before the API is used:

```text
policy_docs/raw/*.pdf + internal policy
   ↓
PDF/text extraction
   ↓
chunking
   ↓
embeddinggemma embeddings through Ollama /api/embed
   ↓
BM25-style token statistics
   ↓
policy_docs/index/policy_vectors.jsonl
```

Runtime retrieval uses:

```text
semantic similarity + BM25-style keyword score + family balancing
```

Family balancing ensures the response is not dominated by the internal policy. It tries to include chunks from:

```text
INTERNAL_POLICY
GDPR
EU_AI_ACT
EU_AI_ACT_GPAI_GUIDANCE
```

## Full mode vs fast mode

`/triage/fast` is for live demos. It uses policy RAG and the fast classifier model, then produces a deterministic short report.

`/triage` is the full workflow. It uses policy RAG, the fast classifier, and the deep analyst model. It is slower but produces a more complete analyst report.
