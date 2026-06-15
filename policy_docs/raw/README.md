# Policy source documents

Place the policy source documents for this lab in this directory before running ingestion.

Expected filenames:

```text
gdpr-regulation-2016-679.pdf
eu-ai-act-regulation-2024-1689.pdf
eu-ai-act-gpai-guidelines-2025-draft-communication.pdf
internal-ai-data-policy.md
```

`internal-ai-data-policy.md` is included in the repository. The legal PDFs are intentionally not committed by default. Add them locally before running:

```bash
./scripts/policy_embed_all.sh
```

The embedding index will be generated in `policy_docs/index/`.
