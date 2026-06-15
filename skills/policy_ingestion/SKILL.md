# Skill: Policy Ingestion

## Purpose

Convert policy documents into a local retrieval index for policy-aware triage.

## Inputs

- PDF policy documents
- Markdown policy documents
- text policy documents

## Processing

1. Validate documents.
2. Extract text.
3. Clean text.
4. Chunk by page or section.
5. Generate embeddings through Ollama.
6. Store chunks, vectors, token statistics, and manifest locally.

## Output

- `policy_docs/index/policy_chunks.jsonl`
- `policy_docs/index/policy_vectors.jsonl`
- `policy_docs/index/policy_manifest.json`

## Safety Rules

- Do not modify source policy documents.
- Do not include raw incident logs in the policy index.
- Do not commit generated vector indexes to GitHub by default.
