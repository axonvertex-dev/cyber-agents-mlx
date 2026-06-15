# Policy source documents

This directory contains the policy source documents used by the lab.

## Included policy sources

```text
gdpr-regulation-2016-679.pdf
eu-ai-act-regulation-2024-1689.pdf
eu-ai-act-gpai-guidelines-2025-draft-communication.pdf
internal-ai-data-policy.md
```

The three PDF files are included for training convenience so participants can run the policy ingestion workflow without manually downloading legal source documents.

## Source attribution

- GDPR Regulation (EU) 2016/679: EUR-Lex / European Union
- Regulation (EU) 2024/1689, Artificial Intelligence Act: EUR-Lex / European Union
- Draft Commission communication on GPAI model obligations: European Commission / European Union

The internal policy file is a lab policy used to demonstrate policy-as-code and human-approval guardrails.

## Generated embedding artifacts

Generated embedding artifacts are not committed. They are created locally in:

```text
policy_docs/index/
```

Run:

```bash
./scripts/policy_embed_all.sh
```

The ingestion script intentionally skips this README file.
